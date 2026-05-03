@echo off
REM Setup script for SystemMonitor - Run this once on each PC
cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python 3.9+
    pause
    exit /b 1
)

echo Creating virtual environment...
if not exist .venv (
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To run the app:
echo   .venv\Scripts\python.exe __main__.py
echo.
echo Or use: run.bat
pause