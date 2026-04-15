$WorkDir = "C:\st8-workspace"
$Python = "$WorkDir\.venv\Scripts\python.exe"
$Startup = [System.Environment]::GetFolderPath('Startup')
$BatFile = "$WorkDir\start_st8_v2.bat"
$BatTarget = "$Startup\start_st8_v2.bat"

Write-Host "ST8-AI Autostart Setup" -ForegroundColor Cyan

if (-not (Test-Path $Python)) {
    Write-Host "ERROR: Python not found at $Python" -ForegroundColor Red
    exit 1
}

$procs = wmic process where "name='python.exe'" get commandline 2>$null

if ($procs | Select-String "jarvis_watchdog") {
    Write-Host "jarvis_watchdog.py: already running" -ForegroundColor DarkYellow
} else {
    Start-Process -FilePath $Python -ArgumentList "jarvis_watchdog.py" -WorkingDirectory $WorkDir -WindowStyle Minimized
    Write-Host "jarvis_watchdog.py: started" -ForegroundColor Green
}

Start-Sleep -Milliseconds 800

$procs2 = wmic process where "name='python.exe'" get commandline 2>$null

if ($procs2 | Select-String "scheduler.py") {
    Write-Host "scheduler.py: already running" -ForegroundColor DarkYellow
} else {
    Start-Process -FilePath $Python -ArgumentList "scheduler.py" -WorkingDirectory $WorkDir -WindowStyle Minimized
    Write-Host "scheduler.py: started" -ForegroundColor Green
}

if (Test-Path $BatFile) {
    Copy-Item -Path $BatFile -Destination $BatTarget -Force
    Write-Host "Startup: start_st8_v2.bat installed" -ForegroundColor Green
} else {
    Write-Host "WARNING: $BatFile not found, skipping startup install" -ForegroundColor Red
}

Write-Host "Done." -ForegroundColor Cyan
