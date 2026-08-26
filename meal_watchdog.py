import subprocess, time, datetime, os, sys, ctypes

_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\ST8AI_MealWatchdog")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meal_scheduler.py")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "meal_watchdog.log")
ERR_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "meal_scheduler_err.log")

def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + str(msg)
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    log("meal_watchdog started")
    while True:
        log("Starting meal_scheduler.py...")
        python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
        if not os.path.exists(python):
            python = "python"
        with open(ERR_LOG, "a", encoding="utf-8") as err_f:
            proc = subprocess.Popen(
                [python, SCRIPT],
                stderr=err_f,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            )
        rc = proc.wait()
        log(f"meal_scheduler stopped (exit code {rc}). Restart in 10s...")
        time.sleep(10)

if __name__ == "__main__":
    main()
