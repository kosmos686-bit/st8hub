"""Управление сервисами ST8-AI — общий модуль"""
import os, sys, json, subprocess, time, psutil, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
STATUS_JSON = BASE_DIR / "st8hub" / "status.json"

PYTHON = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")
if not Path(PYTHON).exists():
    PYTHON = sys.executable

JARVIS_BOT_TOKEN = os.getenv('JARVIS_BOT_TOKEN')
JARVIS_CHAT_ID = 6152243830

SERVICES = {
    'jarvis':   {'script': 'jarvis.py',        'name': 'Jarvis'},
    'meal':     {'script': 'meal_watchdog.py',  'name': 'Meal Watchdog'},
    'errwatch': {'script': 'error_watcher.py',  'name': 'Error Watcher'},
    'n8n':      {'n8n': True,                   'name': 'n8n'},
}


def _python_procs():
    result = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if 'python' in (p.info['name'] or '').lower():
                result.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return result


def get_service_status(key):
    svc = SERVICES.get(key, {})
    script = svc.get('script', '')

    if svc.get('n8n'):
        for p in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            try:
                if 'node' in (p.info['name'] or '').lower():
                    if 'n8n' in ' '.join(p.info['cmdline'] or []):
                        mem = p.info['memory_info'].rss // (1024 * 1024) if p.info['memory_info'] else 0
                        return {'running': True, 'pid': p.pid, 'mem_mb': mem}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return {'running': False, 'pid': None, 'mem_mb': 0}

    for p in _python_procs():
        try:
            cmd = ' '.join(p.info['cmdline'] or [])
            if script and script in cmd:
                mem = p.info['memory_info'].rss // (1024 * 1024) if p.info['memory_info'] else 0
                return {'running': True, 'pid': p.pid, 'mem_mb': mem}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return {'running': False, 'pid': None, 'mem_mb': 0}


def get_all_status():
    result = {}
    for key, svc in SERVICES.items():
        st = get_service_status(key)
        st['name'] = svc['name']
        result[key] = st
    return result


def send_alert(text, token=None):
    token = token or JARVIS_BOT_TOKEN or os.getenv('JARVIS_BOT_TOKEN')
    if not token:
        return
    data = urllib.parse.urlencode({"chat_id": JARVIS_CHAT_ID, "text": text}).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log_error(f"[Alert] send failed: {e}")


def start_service(key):
    svc = SERVICES.get(key)
    if not svc:
        return False, "неизвестный сервис"
    if svc.get('n8n'):
        cmd = ['cmd', '/c', 'start', '', 'n8n', 'start']
    else:
        cmd = [PYTHON, str(BASE_DIR / svc['script'])]
    try:
        subprocess.Popen(
            cmd, cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        return True, "запущен"
    except Exception as e:
        return False, str(e)


def stop_service(key):
    svc = SERVICES.get(key)
    if not svc:
        return False, "неизвестный сервис"
    script = svc.get('script', '')
    killed = []

    procs = []
    if svc.get('n8n'):
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'node' in (p.info['name'] or '').lower():
                    if 'n8n' in ' '.join(p.info['cmdline'] or []):
                        procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    else:
        for p in _python_procs():
            try:
                if script and script in ' '.join(p.info['cmdline'] or []):
                    procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    for p in procs:
        try:
            p.terminate()
            killed.append(str(p.pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        return True, f"остановлен (PID {', '.join(killed)})"
    return False, "процесс не найден"


def restart_with_retries(key, max_retries=3, delay=60):
    svc = SERVICES.get(key, {})
    name = svc.get('name', key)
    now_str = datetime.now().strftime('%H:%M')
    log_error(f"[Monitor] {name} упал, начинаем перезапуск")

    for attempt in range(1, max_retries + 1):
        stop_service(key)
        time.sleep(3)
        ok, _ = start_service(key)
        send_alert(
            f"⚠️ {name} упал в {now_str}. Причина: процесс завершился. "
            f"Попытка перезапуска: {'да' if ok else 'нет'} ({attempt}/{max_retries})"
        )
        if ok:
            time.sleep(15)
            if get_service_status(key)['running']:
                send_alert(f"✅ {name} перезапущен (попытка {attempt})")
                return True
        log_error(f"[Monitor] {name} попытка {attempt}/{max_retries} не удалась")
        if attempt < max_retries:
            time.sleep(delay)

    send_alert(f"❌ {name} не удалось запустить после {max_retries} попыток. Требуется ручное вмешательство.")
    return False


def write_status_json():
    STATUS_JSON.parent.mkdir(exist_ok=True)
    data = {
        "updated": datetime.now().isoformat(timespec='seconds'),
        "services": get_all_status()
    }
    STATUS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def log_error(msg):
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    with open(LOGS_DIR / "errors.log", "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())


if __name__ == '__main__':
    print("Статус сервисов ST8-AI:")
    for key, st in get_all_status().items():
        icon = "✅" if st['running'] else "🔴"
        pid = f"PID {st['pid']}" if st.get('pid') else "—"
        mem = f"  {st.get('mem_mb', 0)} MB" if st.get('running') else ""
        print(f"  {icon} {st['name']}: {pid}{mem}")
