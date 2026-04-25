# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import time
from datetime import datetime
from pathlib import Path

print("SYSTEM START")
print("="*70)

# Проверяем файлы
scripts = ["scheduler.py", "hourly_monitor.py", "system_dashboard.py"]

print("Checking files...")
for script in scripts:
    if Path(script).exists():
        print(f"OK: {script}")
    else:
        print(f"ERROR: {script} NOT FOUND!")

print()
print("Starting processes...")
print()

processes = []

try:
    # Scheduler
    print("Starting scheduler.py...")
    p1 = subprocess.Popen([sys.executable, "scheduler.py"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
    processes.append(("scheduler.py", p1))
    print(f"OK - PID: {p1.pid}")
    time.sleep(2)
    
    # Monitor
    print("Starting hourly_monitor.py...")
    p2 = subprocess.Popen([sys.executable, "hourly_monitor.py"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    processes.append(("hourly_monitor.py", p2))
    print(f"OK - PID: {p2.pid}")
    time.sleep(2)
    
    # Dashboard
    print("Starting system_dashboard.py...")
    p3 = subprocess.Popen([sys.executable, "system_dashboard.py"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    processes.append(("system_dashboard.py", p3))
    print(f"OK - PID: {p3.pid}")
    time.sleep(2)
    
    print()
    print("="*70)
    print("ALL SYSTEMS RUNNING!")
    print("="*70)
    print()
    print("Check Telegram for updates!")
    print()
    print("Press Ctrl+C to stop...")
    print()
    
    # Основной цикл
    while True:
        time.sleep(60)
        # Проверяем живы ли процессы
        for name, proc in processes:
            if proc.poll() is not None:
                print(f"WARNING: {name} crashed!")
        
except KeyboardInterrupt:
    print("\n\nSTOPPING...")
    for name, proc in processes:
        print(f"Stopping {name}...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except:
            proc.kill()
    print("OK - System stopped")
    
except Exception as e:
    print(f"ERROR: {e}")
