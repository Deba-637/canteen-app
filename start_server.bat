@echo off
cd /d "%~dp0"
TITLE Canteen Server
ECHO Starting Canteen Management System...
ECHO.

:: Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed or not in PATH.
    PAUSE
    EXIT /B
)

:: Activate Virtual Environment if it exists (optional but good practice)
IF EXIST ".venv\Scripts\activate.bat" (
    CALL .venv\Scripts\activate.bat
)

:: Start Print Service (Minimized)
ECHO Starting Print Service...
start /MIN "Canteen Print Service" cmd /k python print_service.py

:: Start Web Server (in this window)
ECHO Starting Web Server...
start "Canteen Web Server" python app.py

:: Wait a moment for server to boot
timeout /t 3 /nobreak >nul

:: Open Browser
ECHO Opening Application...
start http://localhost:8000/

ECHO.
ECHO System is running. Do not close the black windows!
ECHO You can minimize them.
ECHO.
PAUSE
