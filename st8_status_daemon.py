"""ST8-AI Status Daemon — каждые 60 сек пишет status.json + git push + автоперезапуск"""
import os, sys, time, subprocess, threading
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from service_manager import (
    get_all_status, write_status_json, send_alert, log_error,
    restart_with_retries, SERVICES
)

# сервисы с автоперезапуском (jarvis обрабатывает watchdog отдельно)
AUTO_RESTART = {'meal', 'errwatch'}

_prev_status: dict = {}
_restart_locks: set = set()
_lock = threading.Lock()


def git_push_status():
    try:
        subprocess.run(
            ['git', 'add', 'st8hub/status.json'],
            cwd=str(BASE_DIR), capture_output=True, timeout=30
        )
        r = subprocess.run(
            ['git', 'commit', '-m', f'auto: status {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
            cwd=str(BASE_DIR), capture_output=True, text=True, timeout=30
        )
        if 'nothing to commit' not in (r.stdout + r.stderr):
            subprocess.run(['git', 'push'], cwd=str(BASE_DIR), capture_output=True, timeout=60)
    except Exception as e:
        log_error(f"[Dashboard] git push failed: {e}")


def _do_restart(key):
    with _lock:
        if key in _restart_locks:
            return
        _restart_locks.add(key)
    try:
        restart_with_retries(key)
    finally:
        with _lock:
            _restart_locks.discard(key)


def run():
    log_error("[Dashboard] ST8 Status Daemon запущен")
    tick = 0

    while True:
        try:
            current = get_all_status()
            changed = False

            for key, st in current.items():
                prev = _prev_status.get(key)
                was_running = prev.get('running') if prev else None
                is_running = st['running']

                if prev is not None and was_running != is_running:
                    changed = True
                    if not is_running and key in AUTO_RESTART:
                        threading.Thread(target=_do_restart, args=(key,), daemon=True).start()

            _prev_status.update(current)
            write_status_json()

            if changed or tick % 10 == 0:
                git_push_status()

            tick += 1
        except Exception as e:
            log_error(f"[Dashboard] Error in main loop: {e}")

        time.sleep(60)


if __name__ == '__main__':
    run()
