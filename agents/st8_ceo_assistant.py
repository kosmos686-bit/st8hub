"""ST8 CEO Assistant — daily morning briefing at 08:00 MSK."""

import json
import os
import urllib.request
from datetime import datetime, timezone

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from telegram import Bot

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
BOT_TOKEN = os.getenv('JARVIS_BOT_TOKEN')
CEO_CHAT_ID = int(os.getenv('CEO_TELEGRAM_ID', '6152243830'))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_weather() -> str:
    """Fetch Moscow weather from Open-Meteo. Returns formatted string."""
    try:
        url = (
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=55.75&longitude=37.62'
            '&current=temperature_2m,windspeed_10m,weathercode'
            '&windspeed_unit=ms'
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        cur = data['current']
        temp = cur['temperature_2m']
        wind = cur['windspeed_10m']
        code = cur['weathercode']

        # Weather code → description
        if code == 0:
            desc = '\u044f\u0441\u043d\u043e'          # ясно
        elif code in (1, 2, 3):
            desc = '\u043e\u0431\u043b\u0430\u0447\u043d\u043e'  # облачно
        elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
            desc = '\u0434\u043e\u0436\u0434\u044c'    # дождь
        elif code in (71, 73, 75, 77, 85, 86):
            desc = '\u0441\u043d\u0435\u0433'          # снег
        else:
            desc = '\u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u043e'  # переменно

        # Clothing advice
        if temp < 0:
            clothes = '\u0437\u0438\u043c\u043d\u044f\u044f \u043a\u0443\u0440\u0442\u043a\u0430, \u0448\u0430\u043f\u043a\u0430, \u0448\u0430\u0440\u0444'
        elif temp < 10:
            clothes = '\u0442\u0451\u043f\u043b\u0430\u044f \u043a\u0443\u0440\u0442\u043a\u0430'
        elif temp < 18:
            clothes = '\u043b\u0451\u0433\u043a\u0430\u044f \u043a\u0443\u0440\u0442\u043a\u0430'
        else:
            clothes = '\u0431\u0435\u0437 \u043a\u0443\u0440\u0442\u043a\u0438'

        umbrella = '\u0434\u0430' if code in (51, 53, 55, 61, 63, 65, 80, 81, 82) else '\u043d\u0435\u0442'

        return (
            f'\U0001f324 \u041c\u043e\u0441\u043a\u0432\u0430: {temp}\u00b0C, {desc}, '
            f'\u0432\u0435\u0442\u0435\u0440 {wind} \u043c/\u0441\n'
            f'\U0001f9e5 {clothes} | \u2602\ufe0f \u0417\u043e\u043d\u0442: {umbrella}'
        )
    except Exception as exc:
        return f'\u041f\u043e\u0433\u043e\u0434\u0430: \u043e\u0448\u0438\u0431\u043a\u0430 ({exc})'


def _get_hub_summary() -> str:
    """Read leads.json and return a brief lead count summary."""
    try:
        path = os.path.join(BASE_DIR, 'st8hub', 'leads.json')
        with open(path, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        total = len(leads) if isinstance(leads, list) else 0
        # Count leads added today (MSK)
        today = datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d')
        new_today = 0
        if isinstance(leads, list):
            for lead in leads:
                created = lead.get('created_at', '') or lead.get('date', '')
                if str(created).startswith(today):
                    new_today += 1
        return (
            f'\U0001f4cb \u041b\u0438\u0434\u044b: {total} \u0432\u0441\u0435\u0433\u043e, '
            f'{new_today} \u0441\u0435\u0433\u043e\u0434\u043d\u044f'
        )
    except FileNotFoundError:
        return '\U0001f4cb \u041b\u0438\u0434\u044b: \u043d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445'
    except Exception as exc:
        return f'\U0001f4cb \u041b\u0438\u0434\u044b: \u043e\u0448\u0438\u0431\u043a\u0430 ({exc})'


def morning_briefing() -> None:
    """Compose and send the morning briefing to CEO via Telegram."""
    if not BOT_TOKEN:
        print('[st8_ceo_assistant] JARVIS_BOT_TOKEN not set, skipping')
        return

    now = datetime.now(MOSCOW_TZ)
    date_str = now.strftime('%d.%m.%Y')

    weather = _get_weather()
    hub = _get_hub_summary()

    text = (
        f'\u2600\ufe0f \u0414\u043e\u0431\u0440\u043e\u0435 \u0443\u0442\u0440\u043e, \u0421\u044d\u0440!\n\n'
        f'{weather}\n\n'
        f'\U0001f4c5 \u041f\u043b\u0430\u043d \u0434\u043d\u044f \u2014 {date_str}\n'
        f'{hub}'
    )

    import asyncio
    bot = Bot(token=BOT_TOKEN)
    asyncio.run(bot.send_message(chat_id=CEO_CHAT_ID, text=text))


def init(scheduler: BackgroundScheduler) -> None:
    """Register morning_briefing on the provided APScheduler instance."""
    scheduler.add_job(
        morning_briefing,
        CronTrigger(hour=8, minute=0, timezone=MOSCOW_TZ),
        id='ceo_morning_briefing',
        replace_existing=True,
    )
