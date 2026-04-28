@echo off
REM Quick start script for backend server

echo Starting GITAM CAN-7USAT Ground Control Server...
echo.

cd /d "%~dp0"

if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m app.main

pause
