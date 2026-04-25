@echo off
cd /d C:\st8-workspace

:: Wait for network to be available
timeout /t 15 /nobreak > nul

:: Kill any leftover python processes from this workspace
wmic process where "name='python.exe'" get processid,commandline 2>nul | findstr "st8-workspace" > nul
if %errorlevel% equ 0 (
    wmic process where "name='python.exe' and CommandLine like '%%st8-workspace%%'" delete 2>nul
    timeout /t 3 /nobreak > nul
)

:: Jarvis — main bot + scheduler thread
start "ST8 Jarvis" /min .venv\Scripts\python.exe -u jarvis.py

:: Meal watchdog — restarts meal_scheduler.py
start "ST8 Meal" /min .venv\Scripts\python.exe meal_watchdog.py

:: Hourly monitor — Kwork inbox monitoring (Юлия replies) — ОТКЛЮЧЁН
:: start "ST8 Monitor" /min .venv\Scripts\python.exe hourly_monitor.py

:: Error watcher — log monitoring, 0 API tokens
start "ST8 ErrWatch" /min .venv\Scripts\python.exe error_watcher.py

echo ST8-AI started at %DATE% %TIME%
