@echo off
rem ------------------------------------------------------------
rem Smart Classroom Attendance System – start script
rem ------------------------------------------------------------

rem Change to the project directory (relative to the location of this .bat)
cd /d "%~dp0"

rem Activate the virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run "python -m venv venv" first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

rem Ensure dependencies are installed (skip if already satisfied)
pip install -r requirements.txt >nul 2>&1

rem Initialise the database if not present
if not exist "database\smart_attendance.db" (
    echo Initialising database ...
    flask initdb
)

rem Start the Flask development server
echo Starting Flask server on http://127.0.0.1:5000
flask run

pause
