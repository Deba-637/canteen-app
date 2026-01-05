@echo off
TITLE Canteen Setup
ECHO Installing Dependencies...
ECHO.

:: Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed! Please install Python 3 first.
    PAUSE
    EXIT /B
)

:: Install Requirements
pip install -r requirements.txt

ECHO.
ECHO Setup Complete!
PAUSE
