"""
map_parser.py - 2GIS + Yandex Maps lead parser for HoReCa/retail/production
Uses 2GIS catalog API + Yandex Search Maps API + Playwright fallback
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

YANDEX_API_KEY = os.getenv("YANDEX_PLACES_API_KEY", "")
YANDEX_BASE_URL = "https://search-maps.yandex.ru/v1/"

ST8HUB_LEADS_PATH = os.path.join(os.path.dirname(__file__), "st8hub", "leads.json")
ST8HUB_DIR = os.path.join(os.path.dirname(__file__), "st8hub")
TG_BOT_TOKEN = os.getenv("JARVIS_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
TG_NOTIFY_CHAT = "6152243830"


def _tg_send(text: str, chat_id: str = TG_NOTIFY_CHAT) -> None:
    """Send Telegram message (fire-and-forget, no crash on failure)."""
    token = TG_BOT_TOKEN
    if not token:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [tg] send failed: {e}")

# 2GIS city slugs (for Playwright URL) and city names (for search query)
CITIES = {
    "москва":          "moscow",
    "санкт-петербург": "saint_petersburg",
    "спб":             "saint_petersburg",
    "новосибирск":     "novosibirsk",
    "екатеринбург":    "ekaterinburg",
    "казань":          "kazan",
    "краснодар":       "krasnodar",
    "ростов-на-дону":  "rostov-na-donu",
    "самара":          "samara",
    "уфа":             "ufa",
    "омск":            "omsk",
    "красноярск":      "krasnoyarsk",
    "воронеж":         "voronezh",
    "пермь":           "perm",
    "волгоград":       "volgograd",
    "тюмень":          "tyumen",
    "челябинск":       "chelyabinsk",
    "иркутск":         "irkutsk",
    "хабаровск":       "khabarovsk",
}

API_KEY = "demo"
BASE_URL = "https://catalog.api.2gis.com/3.0/items"
FIELDS = "items.contact_groups,items.address,items.rubrics,items.reviews,items.rating"


@dataclass
class Lead:
    name: str
    address: str
    phone: str
    category: str
    city: str
    email: str = ""
    website: str = ""
    rating: float = 0.0
    reviews: int = 0
    source: str = "2gis"

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        parts = [self.name]
        parts.append(self.phone if self.phone else "(no phone)")
        if self.address:
            parts.append(self.address)
        if self.rating:
            parts.append(f"{self.rating}* ({self.reviews})")
        return " | ".join(parts)


def _fetch_json(url: str, timeout: int = 15) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [fetch error] {e}")
        return None


def _parse_contacts(item: dict) -> tuple[str, str, str]:
    """Returns (phone, email, website) from contact_groups."""
    phone = email = website = ""
    for group in item.get("contact_groups", []):
        for contact in group.get("contacts", []):
            ctype = contact.get("type", "")
            val = contact.get("value", "")
            if ctype == "phone" and not phone and val:
                phone = val
            elif ctype == "email" and not email and val:
                email = val
            elif ctype == "website" and not website and val:
                # strip 2gis redirect wrapper
                url = contact.get("url", val)
                if "link.2gis.ru" in url:
                    url = val
                website = url
    return phone, email, website


def _parse_item(item: dict, city: str, query: str) -> Optional[Lead]:
    name = item.get("name", "").strip()
    if not name:
        return None

    address = item.get("address_name", "") or ""

    rubrics = item.get("rubrics", [])
    category = rubrics[0].get("name", query) if rubrics else query

    phone, email, website = _parse_contacts(item)

    rating = item.get("rating")
    rating = float(rating) if rating else 0.0

    reviews_obj = item.get("reviews")
    if isinstance(reviews_obj, dict):
        reviews = reviews_obj.get("general_review_count", 0) or 0
    else:
        reviews = 0

    return Lead(
        name=name,
        address=address,
        phone=phone,
        email=email,
        website=website,
        category=category,
        city=city,
        rating=rating,
        reviews=int(reviews),
    )


def search_yandex(
    query: str,
    city: str = "москва",
    limit: int = 20,
) -> list[Lead]:
    """Search Yandex Maps business API."""
    if not YANDEX_API_KEY:
        print("  [yandex] No YANDEX_PLACES_API_KEY, skipping")
        return []

    leads = []
    seen = set()
    print(f"  Yandex search: '{query}' in '{city}' (limit={limit})")

    params = {
        "apikey": YANDEX_API_KEY,
        "text": f"{query} {city}",
        "lang": "ru_RU",
        "type": "biz",
        "results": min(limit, 50),
    }
    url = YANDEX_BASE_URL + "?" + urllib.parse.urlencode(params)
    data = _fetch_json(url)

    if not data:
        return []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        name = props.get("name", "").strip()
        if not name:
            continue

        comp_meta = props.get("CompanyMetaData", {})
        address = comp_meta.get("address", "")
        url_val = comp_meta.get("url", "")
        cats = comp_meta.get("Categories", [])
        category = cats[0].get("name", query) if cats else query

        phone = ""
        for ph in comp_meta.get("Phones", []):
            val = ph.get("formatted", "") or ph.get("number", "")
            if val:
                phone = val
                break

        rating = 0.0
        reviews = 0
        rating_obj = comp_meta.get("rating")
        if rating_obj:
            rating = float(rating_obj.get("score", 0) or 0)
            reviews = int(rating_obj.get("ratings", 0) or 0)

        key = (name.lower()[:40], phone)
        if key in seen:
            continue
        seen.add(key)

        leads.append(Lead(
            name=name, address=address, phone=phone,
            category=category, city=city,
            website=url_val, rating=rating, reviews=reviews,
            source="yandex",
        ))
        if len(leads) >= limit:
            break

    print(f"  Yandex found {len(leads)} leads")
    return leads


def score_lead(lead: Lead) -> tuple[int, str, str]:
    """
    Score lead 1-10 based on data completeness and signals.
    Returns (score, priority, comment).
    """
    score = 5
    notes = []

    if lead.phone:
        score += 1
    else:
        score -= 2
        notes.append("нет телефона")

    if lead.rating >= 4.5:
        score += 1
        notes.append(f"рейтинг {lead.rating}")
    elif lead.rating >= 4.0:
        pass
    elif lead.rating > 0 and lead.rating < 3.5:
        score -= 1

    if lead.reviews >= 50:
        score += 1
        notes.append(f"{lead.reviews} отзывов")
    elif lead.reviews >= 20:
        pass

    if lead.website:
        score += 1
        notes.append("есть сайт")

    if lead.email:
        score += 1

    score = max(1, min(10, score))

    if score >= 8:
        priority = "высокий"
    elif score >= 6:
        priority = "средний"
    else:
        priority = "низкий"

    comment = "; ".join(notes) if notes else "стандартный лид"
    return score, priority, comment


def save_to_hub(leads: list[Lead], min_score: int = 7, city: str = "") -> int:
    """
    Save leads with score >= min_score to st8hub/leads.json.
    Auto git add + commit + push + Telegram notify after writing.
    Returns count of added leads.
    """
    try:
        with open(ST8HUB_LEADS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    seen_phones = {e.get("phone", "") for e in existing if e.get("phone")}

    added = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for lead in leads:
        score, priority, comment = score_lead(lead)
        if score < min_score:
            continue
        if lead.phone and lead.phone in seen_phones:
            continue

        entry = {
            "id": f"{today}-{len(existing) + added + 1:04d}",
            "name": lead.name,
            "phone": lead.phone,
            "site": lead.website,
            "city": lead.city,
            "category": lead.category,
            "score": score,
            "priority": priority,
            "comment": comment,
            "source": lead.source,
            "first_touch": "",
            "date": today,
            "status": "новый",
        }
        existing.append(entry)
        if lead.phone:
            seen_phones.add(lead.phone)
        added += 1

    if added == 0:
        print(f"  [hub] No new leads above score {min_score}")
        return 0

    with open(ST8HUB_LEADS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"  [hub] Saved {added} leads to st8hub/leads.json")

    try:
        subprocess.run(["git", "-C", ST8HUB_DIR, "add", "leads.json"], check=True)
        subprocess.run(
            ["git", "-C", ST8HUB_DIR, "commit", "-m",
             f"2GIS/Yandex: +{added} leads ({today})"],
            check=True,
        )
        result = subprocess.run(
            ["git", "-C", ST8HUB_DIR, "push"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  [hub] Pushed to GitHub Pages")
            city_label = city or (leads[0].city if leads else "")
            _tg_send(
                f"\U0001f3af ST8 Hub \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d "
                f"\u2014 {added} \u043d\u043e\u0432\u044b\u0445 \u043b\u0438\u0434\u043e\u0432 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e\n"
                f"\u0413\u043e\u0440\u043e\u0434: {city_label} | "
                f"\u0414\u0430\u0442\u0430: {today}\n"
                f"\U0001f449 https://kosmos686-bit.github.io/st8hub"
            )
        else:
            print(f"  [hub] Push failed: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"  [hub] Git error: {e}")

    return added


def search_2gis(
    query: str,
    city: str = "москва",
    limit: int = 20,
    page_size: int = 50,
) -> list[Lead]:
    """
    Search 2GIS catalog for businesses.

    Args:
        query:    search query in Russian (e.g. "ресторан", "кафе", "отель")
        city:     city name in Russian (lowercase)
        limit:    max leads to return
        page_size: items per API request (max 50)

    Returns:
        List of Lead objects, deduplicated by phone.
    """
    leads = []
    seen = set()  # deduplicate by (name, phone) pair
    page = 1

    print(f"  2GIS search: '{query}' in '{city}' (limit={limit})")

    while len(leads) < limit:
        params = {
            "q": f"{query} {city}",
            "key": API_KEY,
            "page": page,
            "page_size": min(page_size, 50),
            "fields": FIELDS,
            "type": "branch",
            "sort": "relevance",
        }
        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        data = _fetch_json(url)

        if not data:
            break

        result = data.get("result", {})
        items = result.get("items", [])
        total = result.get("total", 0)

        if not items:
            break

        for item in items:
            lead = _parse_item(item, city, query)
            if not lead:
                continue

            key = (lead.name.lower()[:40], lead.phone)
            if key in seen:
                continue
            seen.add(key)

            leads.append(lead)
            if len(leads) >= limit:
                break

        if page * page_size >= total:
            break

        page += 1
        time.sleep(0.3)

    print(f"  Found {len(leads)} unique leads")
    return leads


async def search_2gis_playwright(
    query: str,
    city: str = "москва",
    limit: int = 20,
) -> list[Lead]:
    """Playwright fallback scraper for 2GIS when API fails."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  playwright not available")
        return []

    city_slug = CITIES.get(city.lower(), city.lower().replace(" ", "_"))
    search_url = f"https://2gis.ru/{city_slug}/search/{urllib.parse.quote(query)}"
    leads = []

    print(f"  Playwright fallback: {search_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        content = await page.content()

        # Extract from embedded JSON
        names = re.findall(r'"name"\s*:\s*"([^"]{3,80})"', content)
        addresses = re.findall(r'"address_name"\s*:\s*"([^"]{5,100})"', content)
        phones = re.findall(r'\+7\d{10}', content)

        seen_names = set()
        for i, name in enumerate(names[:limit]):
            if name in seen_names:
                continue
            seen_names.add(name)
            addr = addresses[i] if i < len(addresses) else ""
            phone = phones[i] if i < len(phones) else ""
            leads.append(Lead(name=name, address=addr, phone=phone,
                              category=query, city=city))

        await browser.close()

    print(f"  Playwright found {len(leads)} leads")
    return leads[:limit]


def save_leads(leads: list[Lead], filename: str = "leads_output.json"):
    """Save leads to JSON file."""
    data = [l.to_dict() for l in leads]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(data)} leads -> {filename}")
    return filename


def print_leads(leads: list[Lead]):
    """Print leads summary."""
    if not leads:
        print("  No leads found.")
        return
    print(f"\n{'='*70}")
    print(f"  LEADS: {len(leads)}")
    print(f"{'='*70}")
    for i, lead in enumerate(leads, 1):
        phone = lead.phone or "(no phone)"
        print(f"  {i:>3}. {lead.name}")
        print(f"       Phone  : {phone}")
        if lead.address:
            print(f"       Addr   : {lead.address}")
        if lead.email:
            print(f"       Email  : {lead.email}")
        if lead.website:
            print(f"       Web    : {lead.website}")
        if lead.rating:
            print(f"       Rating : {lead.rating} ({lead.reviews} reviews)")
        print()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "ресторан"
    city  = sys.argv[2] if len(sys.argv) > 2 else "москва"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    # 2GIS
    leads = search_2gis(query=query, city=city, limit=limit)
    if not leads:
        print("2GIS API returned 0, trying Playwright...")
        leads = asyncio.run(search_2gis_playwright(query=query, city=city, limit=limit))

    # Yandex Maps (merge + dedup by phone)
    yandex_leads = search_yandex(query=query, city=city, limit=limit)
    if yandex_leads:
        existing_phones = {l.phone for l in leads if l.phone}
        existing_keys   = {(l.name.lower()[:40], l.phone) for l in leads}
        for yl in yandex_leads:
            key = (yl.name.lower()[:40], yl.phone)
            if key not in existing_keys:
                leads.append(yl)
                existing_keys.add(key)
        print(f"  Merged total: {len(leads)} leads")

    print_leads(leads)

    if leads:
        out = f"leads_{city}_{query}.json".replace(" ", "_")
        save_leads(leads, out)

        # Score and push to st8hub
        print("\n  Scoring and pushing to hub...")
        added = save_to_hub(leads, min_score=7, city=city)
        print(f"  Hub: {added} new leads added")
