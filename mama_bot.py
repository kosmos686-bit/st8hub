"""
mama_bot.py — независимый сторожевой бот (MAMA_BOT_TOKEN)
- /статус — краткий статус всех сервисов
- Алерт если Jarvis не отвечает 5 минут
- Полностью независим от jarvis.py: отдельный токен, отдельный процесс
"""
import os, sys, time, json, threading, urllib.request, urllib.parse, urllib.error
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

MAMA_BOT_TOKEN = os.getenv('MAMA_BOT_TOKEN')
ALEXEY_CHAT_ID = 6152243830
JARVIS_SCRIPT  = 'jarvis.py'
JARVIS_DOWN_THRESHOLD = 5 * 60   # 5 минут в секундах
POLL_TIMEOUT = 20

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / 'mama_bot.log'


# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


# ── Telegram API (raw urllib, без зависимостей) ───────────────────────────────

def _api(method: str, params: dict = None) -> dict | None:
    url = f'https://api.telegram.org/bot{MAMA_BOT_TOKEN}/{method}'
    data = urllib.parse.urlencode(params or {}).encode() if params else None
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f'[API] {method} error: {e}')
        return None


def send(chat_id: int, text: str):
    _api('sendMessage', {'chat_id': chat_id, 'text': text})


# ── Статус сервисов ───────────────────────────────────────────────────────────

def _py_running(script: str) -> int | None:
    import psutil
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            args = p.info['cmdline'] or []
            if any(
                arg == script or arg.endswith('/' + script) or arg.endswith('\\' + script)
                for arg in args
            ):
                return p.info['pid']
        except Exception:
            pass
    return None


def _port_open(port: int) -> bool:
    import socket
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.5):
            return True
    except OSError:
        return False


CHECKS = [
    ('Jarvis',          lambda: _py_running('jarvis.py')),
    ('Watchdog',        lambda: _py_running('jarvis_watchdog.py')),
    ('Meal Watchdog',   lambda: _py_running('meal_watchdog.py')),
    ('Dashboard',       lambda: _py_running('st8_status_daemon.py')),
    ('Mama Bot',        lambda: _py_running('mama_bot.py')),
    ('n8n',             lambda: _port_open(5678)),
]


def build_status() -> str:
    lines = ['🖥 ST8-AI СЕРВИСЫ\n']
    all_ok = True
    for name, check in CHECKS:
        result = check()
        if result:
            pid_str = f' (PID {result})' if isinstance(result, int) else ''
            lines.append(f'✅ {name} — работает{pid_str}')
        else:
            lines.append(f'🔴 {name} — остановлен')
            all_ok = False
    lines.append('')
    lines.append('Всё штатно.' if all_ok else '⚠️ Есть проблемы — проверь.')
    return '\n'.join(lines)


# ── Мониторинг Jarvis (алерт через 5 мин простоя) ────────────────────────────

def _monitor_jarvis():
    jarvis_down_since: float | None = None

    while True:
        try:
            pid = _py_running(JARVIS_SCRIPT)
            if pid:
                jarvis_down_since = None
            else:
                now = time.time()
                if jarvis_down_since is None:
                    jarvis_down_since = now
                    log('[Monitor] Jarvis не найден, запускаем таймер')
                elif now - jarvis_down_since >= JARVIS_DOWN_THRESHOLD:
                    elapsed = int((now - jarvis_down_since) // 60)
                    log(f'[Monitor] Jarvis не отвечает {elapsed} мин — отправляем алерт')
                    send(
                        ALEXEY_CHAT_ID,
                        f'❌ Jarvis упал {elapsed} мин назад.\n'
                        f'Открой Cowork и напиши: запусти jarvis'
                    )
                    jarvis_down_since = now  # сбрасываем чтобы не спамить
        except Exception as e:
            log(f'[Monitor] Ошибка: {e}')
        time.sleep(60)


# ── Polling ───────────────────────────────────────────────────────────────────

def poll():
    if not MAMA_BOT_TOKEN:
        log('MAMA_BOT_TOKEN не задан — выход')
        sys.exit(1)

    log('=== Mama Bot запущен ===')

    # Запускаем мониторинг Jarvis в фоне
    t = threading.Thread(target=_monitor_jarvis, daemon=True)
    t.start()

    offset = 0
    while True:
        result = _api('getUpdates', {'offset': offset, 'timeout': POLL_TIMEOUT, 'allowed_updates': ['message']})
        if not result or not result.get('ok'):
            time.sleep(5)
            continue

        for update in result.get('result', []):
            offset = update['update_id'] + 1
            msg = update.get('message', {})
            chat_id = msg.get('chat', {}).get('id')
            text = (msg.get('text') or '').strip().lower()

            if not chat_id:
                continue

            if text in ('/статус', '/status', 'статус', 'статус системы'):
                log(f'[Poll] /статус от chat_id={chat_id}')
                send(chat_id, build_status())
            elif text == '/start':
                send(chat_id, '🤖 Mama Bot активен. Команды:\n/статус — статус сервисов')


if __name__ == '__main__':
    poll()
