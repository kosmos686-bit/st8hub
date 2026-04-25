import subprocess, time, datetime, os

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meal_scheduler.py")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "meal_watchdog.log")

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
        proc = subprocess.Popen([python, SCRIPT])
        proc.wait()
        log("meal_scheduler stopped. Restart in 10s...")
        time.sleep(10)

if __name__ == "__main__":
    main()
