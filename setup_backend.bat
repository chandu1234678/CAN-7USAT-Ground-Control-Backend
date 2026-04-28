@echo off
REM ============================================================================
REM GITAM CAN-7USAT Backend Setup Script (Windows)
REM Production-grade Python virtual environment setup
REM ============================================================================

echo.
echo ============================================================================
echo GITAM CAN-7USAT Ground Control Backend Setup
echo ============================================================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.11+ is required
    python --version
    pause
    exit /b 1
)
echo [OK] Python version is compatible
echo.

echo [2/6] Creating virtual environment...
cd backend
if exist venv (
    echo [WARNING] Virtual environment already exists. Removing...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

echo [4/6] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)
echo [OK] Pip upgraded
echo.

echo [5/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [6/6] Running tests...
pytest tests/ -v
if errorlevel 1 (
    echo [WARNING] Some tests failed. Please review.
) else (
    echo [OK] All tests passed
)
echo.

echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo To start the server:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run server: python -m app.main
echo.
echo Or use the quick start script: run_server.bat
echo ============================================================================
echo.

pause
