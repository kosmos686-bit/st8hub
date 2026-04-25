# -*- coding: utf-8 -*-
"""
Дёма — мониторинг ошибок после охоты
Проверяет скриншоты и логи, присылает отчёт в Telegram
"""
import os
import json
from pathlib import Path
from datetime import datetime
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

TOKEN = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
CHAT_ALEX = 6152243830


def tg(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ALEX, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"[TG] {e}")
    print(msg)


def tg_photo(path, caption=""):
    try:
        with open(path, 'rb') as f:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ALEX, "caption": caption},
                files={"photo": f},
                timeout=15
            )
    except Exception as e:
        print(f"[TG Photo] {e}")


def check_results():
    """Проверяет результаты последней охоты"""
    data_dir = Path("C:/st8-workspace/data")
    issues = []
    ok = []

    # 1. Проверяем responded.json
    responded_file = data_dir / "responded.json"
    if responded_file.exists():
        try:
            responded = json.loads(responded_file.read_text(encoding='utf-8'))
            today = datetime.now().date()
            today_count = len([r for r in responded
                              if datetime.fromisoformat(r['time']).date() == today])
            if today_count > 0:
                ok.append(f"Откликов сегодня: {today_count}")
            else:
                issues.append("Сегодня не было откликов")
        except Exception as e:
            issues.append(f"responded.json повреждён: {e}")
    else:
        issues.append("responded.json не найден")

    # 2. Проверяем скриншоты ошибок
    debug_screens = list(data_dir.glob("debug_*.png"))
    if debug_screens:
        # Берём самый свежий
        latest = max(debug_screens, key=lambda f: f.stat().st_mtime)
        age_min = (datetime.now().timestamp() - latest.stat().st_mtime) / 60
        if age_min < 60:  # Если скриншот свежий (до часа)
            issues.append(f"Найден скриншот ошибки: {latest.name}")

    # 3. Проверяем after_submit.png
    after_submit = data_dir / "after_submit.png"
    if after_submit.exists():
        age_min = (datetime.now().timestamp() - after_submit.stat().st_mtime) / 60
        if age_min < 60:
            ok.append("Скриншот после отправки есть")

    return ok, issues, debug_screens


def analyze_with_claude(issues, debug_screens):
    """Анализирует ошибки через Claude если есть проблемы"""
    if not issues:
        return None

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Читаем скриншот если есть
        content = [{"type": "text", "text": f"Проблемы в системе ST8-AI Kwork охота:\n" + "\n".join(issues) + "\n\nЧто пошло не так и как исправить? Кратко, 2-3 предложения."}]

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": content}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Ошибка анализа: {e}"


def run():
    print("🔍 Дёма проверяет результаты охоты...")
    ok, issues, debug_screens = check_results()

    if not issues:
        msg = "✅ Дёма: всё чисто\n" + "\n".join([f"  ✓ {x}" for x in ok])
        tg(msg)
        return

    # Есть проблемы — анализируем
    diagnosis = analyze_with_claude(issues, debug_screens)

    msg = (
        "🔧 Дёма нашёл проблемы:\n\n"
        + "\n".join([f"  ❌ {x}" for x in issues])
        + "\n\n"
        + (f"💡 Диагноз: {diagnosis}" if diagnosis else "")
    )
    tg(msg)

    # Отправляем скриншот ошибки если есть свежий
    if debug_screens:
        latest = max(debug_screens, key=lambda f: f.stat().st_mtime)
        age_min = (datetime.now().timestamp() - latest.stat().st_mtime) / 60
        if age_min < 60:
            tg_photo(latest, f"Скриншот ошибки: {latest.name}")


if __name__ == "__main__":
    run()
