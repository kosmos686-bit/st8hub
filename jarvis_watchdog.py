"""
jarvis_watchdog.py — автоперезапуск Jarvis при падении
Запускать вместо jarvis.py: python jarvis_watchdog.py
"""

import subprocess
import time
import os
import sys
import ctypes
from datetime import datetime

# ── Защита от дублей: только один watchdog одновременно ──────────────────────
_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\ST8AI_JarvisWatchdog")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    print("[Watchdog] Уже запущен другой экземпляр. Выход.")
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

LOG_FILE = "jarvis_watchdog.log"
JARVIS_SCRIPT = os.path.join(os.path.dirname(__file__), "jarvis.py")
PYTHON = sys.executable

MAX_RESTARTS = 20       # максимум перезапусков за сессию
RESTART_DELAY = 10      # секунд между перезапусками
FAST_CRASH_THRESHOLD = 30  # если упал быстрее чем за 30 сек — "быстрый крэш"
MAX_FAST_CRASHES = 5    # после 5 быстрых крэшей — пауза 5 минут


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run():
    restarts = 0
    fast_crashes = 0

    log("=== Jarvis Watchdog запущен ===")
    log(f"Скрипт: {JARVIS_SCRIPT}")

    while restarts < MAX_RESTARTS:
        log(f"Запуск Jarvis (попытка #{restarts + 1})...")

        start_time = time.time()

        try:
            process = subprocess.run(
                [PYTHON, JARVIS_SCRIPT],
                cwd=os.path.dirname(JARVIS_SCRIPT) or ".",
            )
            exit_code = process.returncode
        except Exception as e:
            log(f"ОШИБКА запуска: {e}")
            exit_code = -1

        elapsed = time.time() - start_time
        log(f"Jarvis завершился. Код: {exit_code}, работал: {elapsed:.1f} сек")

        # Нормальное завершение (0) — не перезапускаем
        if exit_code == 0:
            log("Jarvis завершился нормально (код 0). Watchdog останавливается.")
            break

        # Быстрый крэш
        if elapsed < FAST_CRASH_THRESHOLD:
            fast_crashes += 1
            log(f"Быстрый крэш #{fast_crashes} (упал за {elapsed:.1f} сек)")

            if fast_crashes >= MAX_FAST_CRASHES:
                log("5 быстрых крэшей подряд — пауза 5 минут...")
                time.sleep(300)
                fast_crashes = 0
        else:
            fast_crashes = 0  # сбрасываем счётчик если работал дольше порога

        restarts += 1

        if restarts < MAX_RESTARTS:
            log(f"Перезапуск через {RESTART_DELAY} сек...")
            time.sleep(RESTART_DELAY)

    log("=== Watchdog: достигнут лимит перезапусков. Остановка. ===")


if __name__ == "__main__":
    run()
