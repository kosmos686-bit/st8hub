@echo off
cd C:\st8-workspace
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
.venv\Scripts\python.exe scheduler.py
