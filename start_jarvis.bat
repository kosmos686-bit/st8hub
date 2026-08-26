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

:: Jarvis watchdog — manages jarvis.py lifecycle (has mutex, no duplicates)
wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "jarvis_watchdog" > nul
if %errorlevel% neq 0 (
    start "ST8 Jarvis" /min cmd /c ":LOOP & .venv\Scripts\python.exe jarvis_watchdog.py & timeout /t 10 /nobreak & goto LOOP"
)

:: Meal watchdog — restarts meal_scheduler.py
start "ST8 Meal" /min .venv\Scripts\python.exe meal_watchdog.py

:: Hourly monitor — Kwork inbox monitoring (Юлия replies) — ОТКЛЮЧЁН
:: start "ST8 Monitor" /min .venv\Scripts\python.exe hourly_monitor.py

:: Error watcher — log monitoring, 0 API tokens
start "ST8 ErrWatch" /min .venv\Scripts\python.exe error_watcher.py

:: Status daemon — пишет status.json, автоперезапуск сервисов, git push
start "ST8 Dashboard" /min .venv\Scripts\python.exe st8_status_daemon.py

:: Mama Bot — независимый сторожевой бот, алерт если Jarvis упал
start "ST8 MamaBot" /min .venv\Scripts\python.exe mama_bot.py

:: ST8 Dark — Next.js production server (standalone output)
start "ST8 Dark Server" /min cmd /c "cd /d C:\st8-workspace\st8-dark\st8-dark\frontend && node .next/standalone/server.js"

:: ST8 Dark — Cloudflare tunnel (публичный доступ к демо)
timeout /t 8 /nobreak > nul
start "ST8 Dark Tunnel" /min cmd /c "cloudflared tunnel --url http://localhost:3000 >> C:\st8-workspace\logs\cf_tunnel.log 2>&1"

:: Autopilot — FastAPI бэкенд (лиды, DDG поиск, агенты, КП)
start "ST8 Autopilot" /min /d C:\st8-workspace\autopilot ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

echo ST8-AI started at %DATE% %TIME%
