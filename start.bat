@echo off
setlocal enabledelayedexpansion
title Skill Finder Launcher
set FRONTEND_PORT=10002

cd /d "%~dp0"
echo ============================================
echo   Skill Finder - AI Project Trend Tracker
echo ============================================
echo.
sc query MySQL 2>nul | findstr /i "RUNNING" >nul
if %errorlevel% equ 0 (
    echo        [1/4] MySQL is already running.
) else (
    echo        [1/4] MySQL is not running, starting...
    net start MySQL >nul 2>&1
    if !errorlevel! equ 0 (
        echo        MySQL started.
    ) else (
        echo        [WARN] Failed to start MySQL, check the service.
    )
)
echo.
echo [2/4] Checking backend...
curl.exe -s -o nul --max-time 2 --connect-timeout 2 http://127.0.0.1:8000/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo        Backend is already running.
) else (
    echo        Backend is not running, starting...
    start "SkillFinder-Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
    echo        Backend window opened.
)
echo DONE
echo.
echo [3/4] Checking frontend...
curl.exe -s -o nul --max-time 2 --connect-timeout 2 http://localhost:!FRONTEND_PORT! >nul 2>&1
if %errorlevel% equ 0 (
    echo        Frontend is already running.
) else (
    echo        Frontend is not running, starting...
    start "SkillFinder-Frontend" "%~dp0frontend\run-frontend.bat"
    echo        Frontend window opened.
)
echo.
echo [4/4] Waiting for frontend, opening browser...
set READY=0
for /L %%i in (1,1,30) do (
    curl.exe -s -o nul --max-time 2 --connect-timeout 2 http://localhost:!FRONTEND_PORT! >nul 2>&1
    if !errorlevel! equ 0 (
        set READY=1
        goto ready
    )
    ping -n 3 127.0.0.1 >nul
)
:ready
if !READY! equ 1 (
    echo        All services ready!
    start "" "http://localhost:!FRONTEND_PORT!"
) else (
    echo        [WARN] Frontend did not start in time. Open http://localhost:!FRONTEND_PORT! manually.
)
echo.
pause
