"""
jarvis_watchdog.py — автоперезапуск Jarvis при падении
Независимый процесс с отдельным токеном (MAMA_BOT_TOKEN).
Если Jarvis не поднялся после MAX_RESTARTS — Mama Bot пишет Алексею.
"""

import subprocess
import time
import os
import sys
import ctypes
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ── Защита от дублей: только один watchdog одновременно ──────────────────────
_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\ST8AI_JarvisWatchdog")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    print("[Watchdog] Уже запущен другой экземпляр. Выход.")
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "watchdog.log"
JARVIS_SCRIPT = str(BASE_DIR / "jarvis.py")
PYTHON = sys.executable

MAMA_BOT_TOKEN = os.getenv('MAMA_BOT_TOKEN')   # отдельный токен, не Jarvis
JARVIS_CHAT_ID = 6152243830

MAX_RESTARTS = 20
RESTART_DELAY = 10
FAST_CRASH_THRESHOLD = 30
MAX_FAST_CRASHES = 5


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def mama_alert(text):
    """Отправляет через Mama Bot (отдельный токен) если Jarvis недоступен."""
    token = MAMA_BOT_TOKEN
    if not token:
        log("[Watchdog] MAMA_BOT_TOKEN не задан — alert не отправлен")
        return
    data = urllib.parse.urlencode({"chat_id": JARVIS_CHAT_ID, "text": text}).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data
        )
        urllib.request.urlopen(req, timeout=15)
        log("[Watchdog] Mama Bot alert отправлен")
    except Exception as e:
        log(f"[Watchdog] Mama Bot alert ОШИБКА: {e}")


def run():
    restarts = 0
    fast_crashes = 0

    log("=== Jarvis Watchdog запущен ===")
    log(f"Скрипт: {JARVIS_SCRIPT}")
    log(f"Лог: {LOG_FILE}")

    while restarts < MAX_RESTARTS:
        log(f"Запуск Jarvis (попытка #{restarts + 1})...")
        start_time = time.time()

        try:
            process = subprocess.run(
                [PYTHON, JARVIS_SCRIPT],
                cwd=str(BASE_DIR),
            )
            exit_code = process.returncode
        except Exception as e:
            log(f"ОШИБКА запуска: {e}")
            exit_code = -1

        elapsed = time.time() - start_time
        log(f"Jarvis завершился. Код: {exit_code}, работал: {elapsed:.1f} сек")

        if exit_code == 0:
            log("Jarvis завершился нормально (код 0). Watchdog останавливается.")
            break

        if elapsed < FAST_CRASH_THRESHOLD:
            fast_crashes += 1
            log(f"Быстрый крэш #{fast_crashes} (упал за {elapsed:.1f} сек)")
            if fast_crashes >= MAX_FAST_CRASHES:
                log("5 быстрых крэшей подряд — пауза 5 минут...")
                mama_alert(
                    f"⚠️ Jarvis: 5 быстрых крэшей подряд. Пауза 5 минут. "
                    f"Попыток перезапуска: {restarts + 1}/{MAX_RESTARTS}"
                )
                time.sleep(300)
                fast_crashes = 0
        else:
            fast_crashes = 0

        restarts += 1
        if restarts < MAX_RESTARTS:
            log(f"Перезапуск через {RESTART_DELAY} сек...")
            time.sleep(RESTART_DELAY)

    log("=== Watchdog: достигнут лимит перезапусков. Остановка. ===")
    mama_alert(
        "❌ Jarvis упал. Открой Cowork и напиши: запусти jarvis\n"
        f"(не удалось запустить после {MAX_RESTARTS} попыток)"
    )


if __name__ == "__main__":
    run()
