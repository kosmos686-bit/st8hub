import requests
from datetime import datetime

TOKEN = "8797018278:AAGHwcZK5bvA2QuVG5Jx0FB__8hbqxpvip0"
CHAT_ALEX = 6152243830
GIS_KEY = "3f3a2847-659a-4331-aef5-74d7928316f1"

SEARCHES = [
    {"q": "сеть ресторанов", "vertical": "HoReCa"},
    {"q": "сеть кафе", "vertical": "HoReCa"},
    {"q": "торговая сеть магазинов", "vertical": "Retail"},
    {"q": "производственный завод", "vertical": "Factory"},
    {"q": "логистическая компания", "vertical": "Logistics"},
]

CITIES = [
    {"name": "Москва", "lat": 55.7522, "lon": 37.6156},
    {"name": "Санкт-Петербург", "lat": 59.9386, "lon": 30.3141},
    {"name": "Екатеринбург", "lat": 56.8519, "lon": 60.6122},
    {"name": "Самара", "lat": 53.1959, "lon": 50.1008},
]

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ALEX, "text": msg[:4000], "parse_mode": "HTML"},
        timeout=10
    )

def search_2gis(query, lat, lon):
    try:
        r = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params={
                "q": query,
                "point": f"{lon},{lat}",
                "radius": 50000,
                "key": GIS_KEY,
                "fields": "items.contact_groups,items.address,items.name_ex",
                "page_size": 10,
            },
            timeout=10
        )
        data = r.json()
        return data.get("result", {}).get("items", [])
    except Exception as e:
        print(f"Ошибка 2GIS: {e}")
        return []

def format_lead(item, vertical, city):
    name = item.get("name", "?")
    address = item.get("address_name", "—")
    
    contacts = []
    for group in item.get("contact_groups", []):
        for contact in group.get("contacts", []):
            if contact.get("type") in ["phone", "email", "website"]:
                contacts.append(contact.get("value", ""))

    contacts_str = "\n".join(contacts[:3]) if contacts else "не указаны"

    return f"""
🎯 <b>2GIS Лид — {vertical}</b>

<b>Компания:</b> {name}
<b>Город:</b> {city}
<b>Адрес:</b> {address}
<b>Контакты:</b> {contacts_str}

💬 <b>Первое сообщение:</b>
Добрый день, {name}! ST8-AI помогает {vertical}-бизнесам автоматизировать процессы с помощью AI. Окупаемость от 2 мес, гарантия KPI. Есть 15 минут на созвон?
"""

def run():
    tg("🗺️ 2GIS Hunter запущен")
    found = 0

    for city in CITIES:
        for search in SEARCHES:
            items = search_2gis(search["q"], city["lat"], city["lon"])
            for item in items:
                msg = format_lead(item, search["vertical"], city["name"])
                tg(msg)
                found += 1
                if found >= 5:
                    tg(f"✅ 2GIS Hunter завершён. Найдено: {found} лидов")
                    return

    tg(f"✅ 2GIS Hunter завершён. Найдено: {found} лидов")

if __name__ == "__main__":
    run()