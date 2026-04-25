import sys
sys.stdout.reconfigure(encoding="utf-8")
import sys
# -*- coding: utf-8 -*-
"""
ST8-AI Scheduler — запуск охоты по расписанию
09:00 и 17:00 МСК
"""
import schedule
import time
import asyncio
import subprocess
from datetime import datetime

TOKEN = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
CHAT_ALEX = 6152243830
CHAT_JULIA = 5438530925

import requests

def tg(msg):
    for chat in [CHAT_ALEX, CHAT_JULIA]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat, "text": msg},
                timeout=10
            )
        except:
            pass
    print(msg)


def run_hunt():
    now = datetime.now().strftime('%H:%M:%S')
    tg(f"⏰ {now} МСК — запускаю охоту на Kwork...")
    try:
        result = subprocess.run(
            [r"C:\st8-workspace\.venv\Scripts\python.exe", "auto_system.py"],
            cwd=r"C:\st8-workspace",
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(result.stderr)
            tg(f"❌ Ошибка охоты:\n{result.stderr[:300]}")
    except subprocess.TimeoutExpired:
        tg("⚠️ Охота прервана по таймауту (5 мин)")
    except Exception as e:
        tg(f"❌ Исключение: {e}")


def main():
    print("=" * 50)
    print("🤖 ST8-AI ПЛАНИРОВЩИК ЗАПУЩЕН")
    print("⏰ Охота: 09:00 и 17:00 МСК")
    print("=" * 50)

    tg("🤖 ST8-AI планировщик запущен\n⏰ Охота: 09:00 и 17:00 МСК")

    schedule.every().day.at("09:00").do(run_hunt)
    schedule.every().day.at("17:00").do(run_hunt)

    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("Остановлен")
            tg("⛔ Планировщик остановлен")
            break


if __name__ == "__main__":
    main()
