@echo off
color 0A
title Smart Agriculture AI - System Launch

echo ===================================================
echo     SMART AGRICULTURE AI - SYSTEM INITIALIZATION
echo ===================================================
echo.

:: Force correct working directory (where this bat file lives)
cd /d "%~dp0"

echo [INFO] Working directory: %cd%
echo.

:: Check for virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo [FIX]  Run: python -m venv venv
    echo [FIX]  Then: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b
)

:: Check for streamlit
if not exist "venv\Scripts\streamlit.exe" (
    echo [ERROR] Streamlit not installed in venv!
    echo [FIX]  Run: venv\Scripts\pip install streamlit
    pause
    exit /b
)

:: Check for dashboard file
if not exist "app\dashboard.py" (
    echo [ERROR] dashboard.py not found in app\ folder!
    pause
    exit /b
)

echo [1/3] Starting Hardware Telemetry Link ^(Serial Collector^)...
:: Start the collector in a background window
start "" /B "venv\Scripts\python.exe" "edge\serial_collector.py"

echo [2/3] Waiting for hardware connection...
timeout /t 3 /nobreak >nul

echo [3/3] Launching AI Dashboard in your browser...
echo.
echo      Dashboard will open at: http://localhost:8501
echo      Press Ctrl+C in this window to stop the system.
echo.

:: Start streamlit (this blocks until user closes it)
"venv\Scripts\streamlit.exe" run "app\dashboard.py" --server.headless true

echo.
echo [INFO] Dashboard closed. Shutting down hardware link...
taskkill /F /IM python.exe /T >nul 2>&1

echo [INFO] System shut down cleanly. Good luck with the review!
pause
