import requests
import json
import os
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ALEX = 6152243830
GIS_KEY = "3f3a2847-659a-4331-aef5-74d7928316f1"
GMAIL = "kosmos686@gmail.com"
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
AGENTS_DIR = r"C:\Users\user\.claude\agents"
TAVILY_KEY = os.getenv('TAVILY_KEY')

def find_contacts(company, city):
    """Ищет контакты компании через Tavily"""
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": f"{company} {city} email телефон контакты сайт", "max_results": 3},
            timeout=10
        )
        results = r.json().get("results", [])
        contacts = ""
        for res in results[:2]:
            contacts += res.get("content", "")[:500] + " "
        return contacts.strip()
    except:
        return ""
TAVILY_KEY = "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"

def find_contacts(company, city):
    """Ищет контакты компании через Tavily"""
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": f"{company} {city} email телефон контакты сайт", "max_results": 3},
            timeout=10
        )
        results = r.json().get("results", [])
        contacts = ""
        for res in results[:2]:
            contacts += res.get("content", "")[:500] + " "
        return contacts.strip()
    except:
        return ""

SEARCHES = [
    {"q": "сеть ресторанов", "vertical": "HoReCa"},
    {"q": "торговая сеть", "vertical": "Retail"},
    {"q": "производственный завод", "vertical": "Factory"},
]

CITIES = [
    {"name": "Москва", "lat": 55.7522, "lon": 37.6156},
    {"name": "Самара", "lat": 53.1959, "lon": 50.1008},
]

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ALEX, "text": msg[:4000], "parse_mode": "HTML"},
        timeout=10
    )

def load_agent(name):
    path = os.path.join(AGENTS_DIR, f"{name}.md")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return ""

def run_agent(system, task, model="claude-haiku-4-5-20251001"):
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=model, max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": task}]
    )
    return r.content[0].text

def search_2gis(query, lat, lon):
    try:
        r = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params={"q": query, "point": f"{lon},{lat}", "radius": 30000,
                    "key": GIS_KEY, "fields": "items.contact_groups,items.address", "page_size": 5},
            timeout=10
        )
        return r.json().get("result", {}).get("items", [])
    except:
        return []

def get_contacts(item):
    contacts = {"phone": "", "email": "", "website": ""}
    for group in item.get("contact_groups", []):
        for c in group.get("contacts", []):
            t = c.get("type", "")
            if t == "phone" and not contacts["phone"]:
                contacts["phone"] = c.get("value", "")
            elif t == "email" and not contacts["email"]:
                contacts["email"] = c.get("value", "")
            elif t == "website" and not contacts["website"]:
                contacts["website"] = c.get("value", "")
    return contacts

def make_kp(company, vertical, contacts):
    discovery = load_agent("sales-discovery-coach")
    analysis = run_agent(discovery,
        f"Компания: {company}, Вертикаль: {vertical}, Контакты: {contacts}\nОпредели боли и приоритетное предложение ST8-AI. 3 пункта.")

    proposal = load_agent("sales-proposal-strategist")
    kp = run_agent(proposal,
        f"КП для {company} ({vertical}).\nАнализ: {analysis}\n3 абзаца, цифры, призыв к действию.",
        model="claude-sonnet-4-6")
    return kp

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"ST8-AI <{GMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL, GMAIL_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:
        tg(f"❌ Email ошибка: {e}")
        return False

def run():
    tg("🚀 Sales Pipeline запущен")
    processed = 0

    for city in CITIES:
        for search in SEARCHES:
            items = search_2gis(search["q"], city["lat"], city["lon"])
            for item in items:
                company = item.get("name", "?")
                address = item.get("address_name", "—")
                contacts = get_contacts(item)
                vertical = search["vertical"]

                tg(f"🔍 Обрабатываю: <b>{company}</b> ({vertical}, {city['name']})")
                
                # Ищем контакты через Tavily
                found_contacts = find_contacts(company, city['name'])
                if found_contacts:
                    tg(f"📞 Найдены контакты для {company}:\n{found_contacts[:500]}")
                    contacts['search_result'] = found_contacts

                kp = make_kp(company, vertical, contacts)

                chunks = [kp[i:i+3000] for i in range(0, len(kp), 3000)]
                tg(f"📋 КП для <b>{company}</b>:")
                for i, chunk in enumerate(chunks, 1):
                    tg(f"Часть {i}/{len(chunks)}:\n{chunk}")

                if contacts["email"]:
                    ok = send_email(contacts["email"], f"AI-автоматизация — ST8-AI", kp)
                    tg(f"📧 Отправлено на {contacts['email']}" if ok else "📧 Email не отправлен")
                else:
                    tg(f"📞 Email нет. Контакты:\nТел: {contacts['phone']}\nСайт: {contacts['website']}")

                processed += 1
                if processed >= 3:
                    tg(f"✅ Pipeline завершён. Обработано: {processed} лидов")
                    return

    tg(f"✅ Pipeline завершён. Обработано: {processed} лидов")

if __name__ == "__main__":
    run()