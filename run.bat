@echo off
REM Run SystemMonitor
cd /d "%~dp0"

if not exist .venv (
    echo Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python __main__.py
pause