# error_watcher.py
# Мониторинг логов на ошибки — 0 токенов Claude, только requests
# Запуск: python error_watcher.py (добавить в start_st8.bat)

import os
import json
import glob
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
STATE_FILE  = os.path.join(BASE_DIR, 'data', 'error_watcher_state.json')
CHECK_SEC   = 300   # каждые 5 минут
MAX_LINES   = 20    # максимум строк в одном алерте

TG_TOKEN = os.getenv('JARVIS_BOT_TOKEN', '')
ALEKSEY_ID = 6152243830

ERROR_KEYWORDS = ('ERROR', 'Traceback', 'Exception', 'CRITICAL', 'Uncaught')

LOG_PATTERNS = [
    os.path.join(BASE_DIR, 'logs', '*.log'),
    os.path.join(BASE_DIR, 'jarvis_watchdog.log'),
]


def tg_alert(text: str):
    if not TG_TOKEN:
        print('[error_watcher] TG_TOKEN не задан')
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            json={'chat_id': ALEKSEY_ID, 'text': text},
            timeout=10,
        )
    except Exception as e:
        print(f'[error_watcher] tg send failed: {e}')


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            return json.loads(open(STATE_FILE, encoding='utf-8').read())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    open(STATE_FILE, 'w', encoding='utf-8').write(json.dumps(state, ensure_ascii=False, indent=2))


def collect_log_files() -> list:
    files = []
    for pattern in LOG_PATTERNS:
        files.extend(glob.glob(pattern))
    return list(set(files))


def scan_file(path: str, last_pos: int) -> tuple[list, int]:
    """Читает файл с last_pos, возвращает (новые_ошибки, новая_позиция)."""
    errors = []
    try:
        size = os.path.getsize(path)
        if size < last_pos:
            # файл ротировался — читаем с начала
            last_pos = 0
        with open(path, encoding='utf-8', errors='replace') as f:
            f.seek(last_pos)
            for line in f:
                if any(kw in line for kw in ERROR_KEYWORDS):
                    errors.append(line.rstrip())
            new_pos = f.tell()
        return errors, new_pos
    except Exception as e:
        print(f'[error_watcher] scan {path}: {e}')
        return [], last_pos


def check_once():
    state = load_state()
    all_errors = []

    for path in collect_log_files():
        last_pos = state.get(path, 0)
        errors, new_pos = scan_file(path, last_pos)
        state[path] = new_pos
        if errors:
            fname = os.path.basename(path)
            all_errors.append(f'📄 {fname}:')
            all_errors.extend(f'  {e}' for e in errors[:MAX_LINES])
            if len(errors) > MAX_LINES:
                all_errors.append(f'  ... ещё {len(errors) - MAX_LINES} строк')

    save_state(state)

    if all_errors:
        ts = datetime.datetime.now().strftime('%H:%M')
        header = f'🚨 ОШИБКИ В ЛОГАХ [{ts}]\n'
        body = '\n'.join(all_errors)
        # обрезаем до 4000 символов (лимит Telegram)
        msg = (header + body)[:4000]
        tg_alert(msg)
        print(f'[error_watcher] Отправлен алерт: {len(all_errors)} строк')
    else:
        print(f'[error_watcher] {datetime.datetime.now().strftime("%H:%M")} — чисто')


def main():
    print(f'[error_watcher] Запущен. Проверка каждые {CHECK_SEC}с.')
    while True:
        check_once()
        time.sleep(CHECK_SEC)


if __name__ == '__main__':
    main()
