import requests
import json
from datetime import datetime

TOKEN = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
CHAT_ALEX = 6152243830

VERTICALS = {
    'horeca': ['IT директор ресторан', 'автоматизация ресторан', 'iiko внедрение', 'CRM ресторан'],
    'retail': ['Head of Digital retail', 'CRM директор ритейл', 'программа лояльности'],
    'factory': ['computer vision производство', 'автоматизация контроль качества'],
}

AREAS = [1, 2, 3, 88, 78]  # Москва, СПб, Екб, Казань, Самара

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ALEX, "text": msg[:4000], "parse_mode": "HTML"},
        timeout=10
    )

def search_hh(query, area):
    try:
        r = requests.get(
            "https://api.hh.ru/vacancies",
            params={"text": query, "area": area, "period": 1, "per_page": 20},
            headers={"User-Agent": "ST8-AI/1.0"},
            timeout=10
        )
        return r.json().get("items", [])
    except:
        return []

def get_employer(employer_id):
    try:
        r = requests.get(
            f"https://api.hh.ru/employers/{employer_id}",
            headers={"User-Agent": "ST8-AI/1.0"},
            timeout=10
        )
        return r.json()
    except:
        return {}

def format_lead(vacancy, vertical, employer):
    salary = vacancy.get("salary")
    salary_str = "не указана"
    if salary:
        f = salary.get("from", "")
        t = salary.get("to", "")
        salary_str = f"{f}-{t} руб"

    open_vac = employer.get("open_vacancies", 0)
    size = "🏢 Крупная" if open_vac > 10 else "🏭 Средняя" if open_vac > 3 else "🏠 Малая"

    return f"""
🎯 <b>HH Лид — {vertical.upper()}</b>

<b>Компания:</b> {employer.get('name', '?')} {size}
<b>Вакансия:</b> {vacancy.get('name')}
<b>Зарплата:</b> {salary_str}
<b>Открытых вакансий:</b> {open_vac}
<b>Сайт:</b> {employer.get('site_url', '—')}
<b>Ссылка:</b> {vacancy.get('alternate_url')}

💬 <b>Первое сообщение:</b>
Добрый день! Видим вашу вакансию "{vacancy.get('name')}". ST8-AI специализируется на AI-автоматизации для {vertical}. 47 проектов, 0 провалов, окупаемость от 2 мес. Есть 15 минут на созвон?
"""

def run():
    tg("🤖 HH Hunter запущен")
    found = 0

    for vertical, queries in VERTICALS.items():
        for query in queries:
            for area in AREAS:
                vacancies = search_hh(query, area)
                for v in vacancies:
                    employer_id = v.get("employer", {}).get("id")
                    if not employer_id:
                        continue
                    employer = get_employer(employer_id)
                    if employer.get("open_vacancies", 0) < 3:
                        continue
                    msg = format_lead(v, vertical, employer)
                    tg(msg)
                    found += 1
                    if found >= 10:
                        tg(f"✅ HH Hunter завершён. Найдено лидов: {found}")
                        return

    tg(f"✅ HH Hunter завершён. Найдено лидов: {found}")

if __name__ == "__main__":
    run()