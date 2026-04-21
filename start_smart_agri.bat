@echo off
color 0A
title Smart Agriculture AI - System Launch

echo ===================================================
echo     SMART AGRICULTURE AI - SYSTEM INITIALIZATION
echo ===================================================
echo.

:: Check for virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup first.
    pause
    exit /b
)

echo [1/3] Starting Hardware Telemetry Link ^(Serial Collector^)...
:: Start the collector in a hidden background window
start /B "Serial Collector" "venv\Scripts\python.exe" "edge\serial_collector.py"

echo [2/3] Waiting for hardware connection...
timeout /t 3 /nobreak >nul

echo [3/3] Launching AI Dashboard in your browser...
:: Start streamlit
"venv\Scripts\streamlit.exe" run "app\dashboard.py"

echo.
echo [INFO] Dashboard closed. Shutting down hardware link...
:: Kill the background python process we started for the collector
taskkill /F /IM python.exe /T >nul 2>&1

echo [INFO] System shut down cleanly. Good luck with the review!
timeout /t 3 >nul
exit
