@echo off
setlocal
title Skill Finder - Stop

echo ============================================
echo   Stopping Skill Finder services...
echo ============================================
echo.

echo [1/3] Stopping backend (uvicorn)...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*uvicorn*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo        Backend stopped.
echo.

echo [2/3] Stopping frontend (vite)...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | Where-Object { $_.CommandLine -like '*vite*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='cmd.exe'\" | Where-Object { $_.CommandLine -like '*npm run dev*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo        Frontend stopped.
echo.

echo [3/3] Checking remaining windows...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='cmd.exe'\" | Where-Object { $_.CommandLine -like '*skill-finder*' -and $_.CommandLine -like '*uvicorn*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo        Launcher windows closed.
echo.

echo ============================================
echo   Done. Backend and frontend are stopped.
echo   MySQL service is left running (system service).
echo   To stop MySQL too, run:  net stop MySQL
echo ============================================
pause
