# -*- coding: utf-8 -*-
# meal_scheduler.py — Smart meal scheduler for Jarvis
# SEND ONLY: 08:00 menu, 18:30 product check, 21:00 summary
# All incoming messages (ок/нет X) handled by jarvis.py

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import datetime
import json
import os
import time
import threading

JARVIS_TOKEN = os.getenv("JARVIS_BOT_TOKEN", "")
ALEKSEY_ID   = 6152243830
START_DATE   = datetime.date(2026, 4, 23)

BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
PLAN_FILE         = os.path.join(BASE_DIR, "meal_plan_28.json")
LOG_FILE          = os.path.join(BASE_DIR, "data", "meal_sent.json")
WEIGHT_FILE       = os.path.join(BASE_DIR, "data", "weight_log.json")
EVENING_STATE_FILE = os.path.join(BASE_DIR, "data", "meal_evening_state.json")

SCHEDULE = {
    "morning_menu":  "08:00",
    "evening_check": "18:30",
    "summary":       "21:00",
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            return json.loads(open(path, encoding="utf-8").read())
        except Exception:
            pass
    return {}

def _save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))

def tg(text: str):
    if not JARVIS_TOKEN:
        print("[meal_scheduler] JARVIS_BOT_TOKEN не задан")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{JARVIS_TOKEN}/sendMessage",
            json={"chat_id": ALEKSEY_ID, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"[meal_scheduler] TG error: {e}")

def day_number() -> int:
    delta = (datetime.date.today() - START_DATE).days
    return (delta % 28) + 1

# ─── PLAN HELPERS ─────────────────────────────────────────────────────────────

def load_plan() -> list:
    try:
        return json.loads(open(PLAN_FILE, encoding="utf-8").read())
    except Exception as e:
        print(f"[meal_scheduler] Не удалось загрузить план: {e}")
        return []

def get_plan_for_day(day_num: int) -> dict | None:
    plan = load_plan()
    if not plan:
        return None
    idx = (day_num - 1) % len(plan)
    return plan[idx]

# ─── FORMAT MESSAGES ──────────────────────────────────────────────────────────

def format_morning_menu(plan: dict, date: datetime.date = None) -> str:
    if not plan:
        return "⚠️ План питания не найден"
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime("%d.%m.%Y")
    m = plan["macros"]
    lines = [f"📅 {date_str} | {plan['total_kcal']} ккал", ""]
    for meal in plan["meals"]:
        drink = f" + {meal['drink']}" if meal.get("drink") else ""
        lines.append(f"{meal['emoji']} {meal['time']} {meal['display']}{drink}")
    lines += [
        "",
        f"💧 {plan['water_liters']}л воды",
        f"🥩 б:{m['protein']} у:{m['carbs']} ж:{m['fat']}",
    ]
    if plan.get("note"):
        lines.append(f"⚠️ {plan['note']}")
    return "\n".join(lines)

def format_evening_check(tomorrow_plan: dict, tomorrow_date: datetime.date) -> str:
    if not tomorrow_plan:
        return "⚠️ План на завтра не найден"
    date_str = tomorrow_date.strftime("%d.%m.%Y")
    lines = [f"🛒 завтра {date_str} — проверь продукты:", ""]
    name_map = {"breakfast": "Завтрак", "lunch": "Обед", "dinner": "Ужин"}
    confirm_map = {"breakfast": "завтрак ок", "lunch": "обед ок", "dinner": "ужин ок"}
    for meal in tomorrow_plan["meals"]:
        if meal["id"] not in ("breakfast", "lunch", "dinner"):
            continue
        lines.append(f"{meal['emoji']} {name_map[meal['id']]} {meal['time']}")
        for item in meal["items"]:
            lines.append(f"- {item}")
        lines.append(f'→ "{confirm_map[meal["id"]]}" или "нет [продукт]"')
        lines.append("")
    return "\n".join(lines).rstrip()

# ─── CONFIRM HANDLER (called by jarvis.py poll) ───────────────────────────────

def handle_meal_confirm(text: str) -> str | None:
    """
    Returns reply string if state changed, None otherwise.
    Called from jarvis.py poll_jarvis() handler.
    """
    t = text.strip().lower()
    state = _load_json(EVENING_STATE_FILE)
    if not state:
        return None
    if state.get("all_confirmed"):
        return None

    confirm_phrases = {
        "завтрак ок": "breakfast",
        "обед ок":    "lunch",
        "ужин ок":    "dinner",
    }
    for phrase, meal_id in confirm_phrases.items():
        if phrase in t:
            state["confirmed"][meal_id] = True
            if all(state["confirmed"].values()):
                state["all_confirmed"] = True
                _save_json(EVENING_STATE_FILE, state)
                try:
                    d = datetime.datetime.strptime(state["date"], "%Y-%m-%d")
                    date_fmt = d.strftime("%d.%m")
                except Exception:
                    date_fmt = state.get("date", "")
                return f"✅ Меню на {date_fmt} готово, пришлю в 08:00"
            _save_json(EVENING_STATE_FILE, state)
            return f"👍 Записал"

    return None

def get_evening_state() -> dict:
    return _load_json(EVENING_STATE_FILE)

# ─── SCHEDULER ────────────────────────────────────────────────────────────────

def check_and_send():
    now   = datetime.datetime.now().strftime("%H:%M")
    today = datetime.date.today().isoformat()
    sent  = _load_json(LOG_FILE)
    day_sent = sent.get(today, [])

    # 08:00 — morning menu
    if now == SCHEDULE["morning_menu"] and "morning_menu" not in day_sent:
        day_plan = get_plan_for_day(day_number())
        msg = format_morning_menu(day_plan)
        tg(msg)
        print(f"[{now}] morning_menu sent (day {day_number()})")
        day_sent.append("morning_menu")
        if day_plan:
            confirmed_path = os.path.join(BASE_DIR, "data", f"confirmed_menu_{today}.json")
            _save_json(confirmed_path, {
                "day": day_number(),
                "date": today,
                "plan": day_plan,
                "substitutions": {},
            })

    # 18:30 — evening product check for tomorrow
    elif now == SCHEDULE["evening_check"] and "evening_check" not in day_sent:
        tomorrow      = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_day  = ((tomorrow - START_DATE).days % 28) + 1
        tomorrow_plan = get_plan_for_day(tomorrow_day)
        msg = format_evening_check(tomorrow_plan, tomorrow)
        tg(msg)
        print(f"[{now}] evening_check sent (tomorrow day {tomorrow_day})")
        day_sent.append("evening_check")
        _save_json(EVENING_STATE_FILE, {
            "date": tomorrow.isoformat(),
            "day":  tomorrow_day,
            "confirmed": {"breakfast": False, "lunch": False, "dinner": False},
            "all_confirmed": False,
        })

    # 21:00 — brief summary
    elif now == SCHEDULE["summary"] and "summary" not in day_sent:
        tg(f"📊 День {day_number()} завершён. Пей воду перед сном. Спокойной ночи!")
        print(f"[{now}] summary sent")
        day_sent.append("summary")

    sent[today] = day_sent
    _save_json(LOG_FILE, sent)

# ─── WEEKLY WEIGHT REPORT (Sunday 09:00) ──────────────────────────────────────

def check_weekly_report():
    now = datetime.datetime.now()
    if now.weekday() != 6 or now.strftime("%H:%M") != "09:00":
        return
    today = datetime.date.today().isoformat()
    sent  = _load_json(LOG_FILE)
    if "weekly_weight" in sent.get(today, []):
        return
    log = _load_json(WEIGHT_FILE)
    if not log:
        tg("⚖️ Нет данных о весе за эту неделю.")
    else:
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        all_e  = sorted(log.items())
        recent = [(d, w) for d, w in all_e if d >= week_ago]
        lines  = ["📊 Итог недели (вес):"]
        if len(recent) >= 2:
            delta = recent[-1][1] - recent[0][1]
            lines.append(f"За неделю: {'+' if delta>0 else ''}{delta:.1f} кг  ({recent[0][1]} → {recent[-1][1]})")
        if len(all_e) >= 2:
            dt = all_e[-1][1] - all_e[0][1]
            lines.append(f"От старта: {'+' if dt>0 else ''}{dt:.1f} кг")
        lines.append("\nПоследние замеры:")
        for d, w in all_e[-5:]:
            lines.append(f"  {d}: {w} кг")
        tg("\n".join(lines))
    day_sent = sent.get(today, [])
    day_sent.append("weekly_weight")
    sent[today] = day_sent
    _save_json(LOG_FILE, sent)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"[meal_scheduler] Started. Cycle day: {day_number()}")
    while True:
        try:
            check_and_send()
            check_weekly_report()
        except Exception as e:
            print(f"[meal_scheduler] error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
