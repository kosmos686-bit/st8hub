@echo off
REM Добавление no_sleep.bat в автозапуск
set SCRIPT_PATH=%~dp0no_sleep.bat
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v NoSleep /t REG_SZ /d "%SCRIPT_PATH%" /f
echo no_sleep.bat добавлен в автозапуск.
pause