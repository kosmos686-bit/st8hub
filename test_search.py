import asyncio
from scheduler import search_leads, send_leads

# Тестовый поиск: 3 лида по HoReCa
leads = search_leads("horeca", 3)
print(f"Найдено лидов: {len(leads)}")
for lead in leads:
    print(f"Компания: {lead['company_name']}, ЛПР: {lead['lpr']}, Сегмент: {lead['segment']}")

# Отправка в Telegram
send_leads(leads)
print("Лиды отправлены в Telegram!")