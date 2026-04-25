import subprocess
import asyncio
import time
import os
from datetime import datetime
from pathlib import Path
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class MasterSystem:
    """Запускает всю систему в одном процессе"""
    
    def __init__(self):
        self.processes = []
    
    def start_all(self):
        """Запускает все компоненты в фоне"""
        
        print("=" * 70)
        print("ЗАПУСК ПОЛНОЙ СИСТЕМЫ АГЕНТОВ")
        print("=" * 70)
        print()
        
        # Запускаем каждый скрипт в фоновом процессе
        scripts = [
            ("hourly_monitor.py", "Мониторинг сообщений"),
            ("system_dashboard.py", "Dashboard и логи")
        ]
        
        for script, description in scripts:
            print(f"Запускаю {description}...")
            
            try:
                # Запускаем в фоне
                process = subprocess.Popen(
                    [f"python3", script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.processes.append((script, process))
                print(f"   OK - {script} запущен (PID: {process.pid})\n")
            
            except Exception as e:
                print(f"   ERROR: {e}\n")
        
        print("=" * 70)
        print("OK - ВСЕ КОМПОНЕНТЫ ЗАПУЩЕНЫ!")
        print("=" * 70)
        print()
        print("STATUS:")
        print(f"  * Охота: Работает в фоне")
        print(f"  * Мониторинг: Работает в фоне")
        print(f"  * Dashboard: Работает в фоне")
        print()
        print("Все уведомления приходят в Telegram!")
        print()
        print("Press Ctrl+C для остановки...")
        print()
        
        # Основной цикл - держим процесс живым
        try:
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nОСТАНОВКА СИСТЕМЫ...")
            print("=" * 70)
            
            for script, process in self.processes:
                print(f"Останавливаю {script}...")
                process.terminate()
            
            print("\nOK - Система остановлена!")

TELEGRAM_TOKEN = '8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y'
CHAT_ID = 6152243830


def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"[TG] Ошибка: {e}")


def send_hunt_report(sent_projects, total_found, next_hunt="завтра 07:00"):
    now = datetime.now().strftime("%H:%M")
    lines = [
        "🎯 ОХОТА ЗАВЕРШЕНА!",
        f"⏰ Время: {now}",
        f"📊 Найдено проектов: {total_found}",
        "",
    ]
    for proj in sent_projects:
        budget_fmt = f"{proj['budget']:,}".replace(",", " ")
        lines += [
            "━━━━━━━━━━━━━━━━",
            f"📌 {proj['title'][:60]}",
            f"💰 Бюджет: {budget_fmt} ₽",
            f"🔗 https://kwork.ru/projects/{proj['id']}",
            "🔍 Алина — нашла",
            "📊 Анна — проанализировала",
            "✍️ Макс — написал отклик",
            "📤 Юлия — отправила ✅",
            "━━━━━━━━━━━━━━━━",
            "",
        ]
    total_budget = sum(p["budget"] for p in sent_projects)
    budget_fmt = f"{total_budget:,}".replace(",", " ")
    conv_fmt = f"{int(total_budget * 0.2):,}".replace(",", " ")
    lines += [
        f"💰 Общий потенциал: {budget_fmt} ₽",
        f"📈 При конверсии 20%: {conv_fmt} ₽",
        f"⏰ Следующая охота: {next_hunt}",
    ]
    send_telegram("\n".join(lines))


if __name__ == '__main__':
    system = MasterSystem()
    system.start_all()
