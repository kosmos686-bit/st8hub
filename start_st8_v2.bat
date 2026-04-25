@echo off
cd /d C:\st8-workspace

echo Checking ST8-AI systems...

:: Check if jarvis_watchdog already running
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "python" > nul 2>&1
if %errorlevel% equ 0 (
    wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "jarvis_watchdog" > nul
    if %errorlevel% equ 0 (
        echo jarvis_watchdog.py: already running, skipping.
        goto check_scheduler
    )
)

echo Starting Jarvis watchdog...
start "ST8 Jarvis" .venv\Scripts\python.exe jarvis_watchdog.py

:check_scheduler
wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "scheduler.py" > nul
if %errorlevel% equ 0 (
    echo scheduler.py: already running, skipping.
) else (
    echo Starting Scheduler...
    start "ST8 Scheduler" .venv\Scripts\python.exe scheduler.py
)

wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "hourly_monitor.py" > nul
if %errorlevel% equ 0 (
    echo hourly_monitor.py: already running, skipping.
) else (
    echo Starting Hourly Monitor...
    start "ST8 Hourly Monitor" .venv\Scripts\python.exe hourly_monitor.py
)

echo Done.
