@echo off
echo Creating Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Failed to create shortcut.
    echo Please verify "create_shortcut.ps1" exists in this folder.
    pause
    exit /b
)
echo.
pause
