@echo off
chcp 65001 >nul
cd /d C:\st8-workspace
echo Starting Mama Bot...
.venv\Scripts\python.exe mama_bot.py
pause
