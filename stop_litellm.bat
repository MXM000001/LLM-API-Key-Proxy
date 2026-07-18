@echo off
chcp 65001 >nul
title LiteLLM - Stop

echo ==============================
echo   Stopping LiteLLM
echo ==============================
echo.

taskkill /IM litellm.exe /F >nul 2>&1
if errorlevel 1 (
    echo [NOTE] LiteLLM not running
) else (
    echo [OK] LiteLLM stopped
)

echo.
echo Releasing port 5001...

powershell.exe -ExecutionPolicy Bypass -File "%~dp0free_port.ps1"

echo.
pause