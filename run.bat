@echo off
echo ==============================================
echo   Harvey - Local Runner
echo ==============================================

echo [1/3] Checking for Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not added to PATH. Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

echo [2/3] Setting up virtual environment and installing dependencies...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [3/3] Starting Harvey...
echo.
echo NOTE: Since the app uses global keyboard hooks to listen to inputs (F2 / F3 / F4 / F5),
echo you may need to run this batch file as Administrator if the hotkeys do not register.
echo.

python main.py

pause
