@echo off
REM SystemMonitor Setup - Run once on each PC
cd /d "%~dp0"

echo ====================================
echo   SystemMonitor Setup
echo ====================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Create venv if needed
if not exist .venv (
    echo.
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ====================================
echo   Setup Complete!
echo ====================================
echo.
echo Run the app with: run.bat
pause