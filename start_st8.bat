@echo off
cd C:\st8-workspace
start "Scheduler" /min cmd /c ":LOOP & .venv\Scripts\python.exe scheduler_final.py & timeout /t 5 & goto LOOP"
start "Meal" /min cmd /c ":LOOP & .venv\Scripts\python.exe meal_watchdog.py & timeout /t 5 & goto LOOP"
start "Monitor" /min cmd /c ":LOOP & .venv\Scripts\python.exe hourly_monitor.py & timeout /t 5 & goto LOOP"
start "ErrWatch" /min cmd /c ":LOOP & .venv\Scripts\python.exe error_watcher.py & timeout /t 5 & goto LOOP"
echo ST8-AI started. Press any key to stop...
pause
