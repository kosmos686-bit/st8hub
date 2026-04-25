import subprocess
import time
import sys
from datetime import datetime

PYTHON = r"C:\st8-workspace\.venv\Scripts\python.exe"
WORKDIR = r"C:\st8-workspace"

scripts = {
    "Scheduler": "scheduler_final.py",
    "Monitor": "hourly_monitor.py",
}

processes = {}

def start_all():
    for name, script in scripts.items():
        log = open(f"C:/st8-workspace/logs/{name.lower()}.log", "a", encoding="utf-8")
        p = subprocess.Popen(
            [PYTHON, script],
            cwd=WORKDIR,
            stdout=log,
            stderr=log
        )
        processes[name] = (p, script, log)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {name} запущен (PID {p.pid})")

def watchdog():
    print("ST8-AI запущен. Ctrl+C для остановки.")
    start_all()
    while True:
        time.sleep(30)
        for name, (p, script, log) in list(processes.items()):
            if p.poll() is not None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {name} упал — перезапускаю...")
                log2 = open(f"C:/st8-workspace/logs/{name.lower()}.log", "a", encoding="utf-8")
                p2 = subprocess.Popen([PYTHON, script], cwd=WORKDIR, stdout=log2, stderr=log2)
                processes[name] = (p2, script, log2)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {name} перезапущен (PID {p2.pid})")

if __name__ == "__main__":
    try:
        watchdog()
    except KeyboardInterrupt:
        print("Останавливаю...")
        for name, (p, script, log) in processes.items():
            p.terminate()
        print("Остановлено.")
