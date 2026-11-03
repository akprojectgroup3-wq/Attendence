@echo off
title AI and IoT Smart Classroom Attendance System
color 0b

echo ============================================================
echo   AI and IoT SMART CLASSROOM ATTENDANCE SYSTEM
echo   Face Recognition (OpenCV LBPH) and IoT Architecture
echo ============================================================
echo.

cd /d "%~dp0"

:: Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo [*] Activating virtual environment...
    call "venv\Scripts\activate.bat"
    set "PY_EXEC=venv\Scripts\python.exe"
) else (
    echo [!] Virtual environment not detected. Using system Python...
    set "PY_EXEC=python"
)

echo [*] Starting Flask web server on http://127.0.0.1:5000
echo [*] Default Login: admin / admin123
echo [*] Opening application in your browser...
echo.

:: Automatically open default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Start Flask server
"%PY_EXEC%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Server stopped with error code %ERRORLEVEL%.
    pause
)
