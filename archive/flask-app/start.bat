@echo off
REM AI Digest Web App Startup Script (Windows)

echo ==================================
echo AI News Digest Web App
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting server...
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ==================================
echo.

REM Run the app
python app.py

pause
