#!/usr/bin/env python3
"""
Тестовый скрипт для поиска 3 лидов прямо сейчас
"""
import os
import sys
import json
import subprocess
from dotenv import load_dotenv

# Добавить текущую папку в path
sys.path.insert(0, os.path.dirname(__file__))

# Загрузить переменные окружения
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

from scheduler import search_leads, send_text_notification

def main():
    print("[*] Запуск тестового поиска лидов...")
    
    # Поиск 3 лидов
    leads = search_leads("horeca", 3)
    print(f"[+] Найдено {len(leads)} лидов")
    
    if not leads:
        print("[-] Лиды не найдены!")
        return
    
    # Сохранить в st8hub/leads.json
    hub_path = os.path.join(os.path.dirname(__file__), 'st8hub')
    leads_file = os.path.join(hub_path, 'leads.json')
    
    os.makedirs(hub_path, exist_ok=True)
    
    with open(leads_file, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    
    print(f"[+] Сохранено в {leads_file}")
    
    # Список компаний для уведомления
    companies = [lead['company_name'] for lead in leads]
    companies_text = "\n".join([f"• {c}" for c in companies])
    
    # Git commit и push
    try:
        subprocess.run(['git', 'add', '.'], cwd=hub_path, check=True)
        subprocess.run(['git', 'commit', '-m', f"Test: Add {len(leads)} test leads"], cwd=hub_path, check=True)
        result = subprocess.run(['git', 'push'], cwd=hub_path, capture_output=True, text=True)
        print("[+] Pushed to repository")
    except subprocess.CalledProcessError as e:
        print(f"[-] Git error: {e}")
    
    # Отправить уведомление в Telegram
    notification = f"""🔥 Тестовый поиск завершен!

Найдено лидов: {len(leads)}

{companies_text}

✅ Данные сохранены в GitHub Hub"""
    
    try:
        send_text_notification(notification)
        print("[+] Уведомление отправлено в Telegram")
    except Exception as e:
        print(f"[-] Ошибка при отправке в Telegram: {e}")
    
    # Вывести информацию о лидах
    print("\n=== НАЙДЕННЫЕ ЛИДЫ ===")
    for i, lead in enumerate(leads, 1):
        print(f"\n{i}. {lead['company_name']}")
        print(f"   ЛПР: {lead['lpr']}")
        print(f"   Email: {lead['email'] or 'не найден'}")
        print(f"   Телефон: {lead['phone'] or 'не найден'}")
        print(f"   Сегмент: {lead['segment']}")

if __name__ == "__main__":
    main()
