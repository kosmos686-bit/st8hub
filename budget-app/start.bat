@echo off
cd /d %~dp0
echo Starting Budget App...
echo Open in browser: http://localhost:5173
echo.
node node_modules\vite\bin\vite.js
pause
