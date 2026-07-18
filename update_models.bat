@echo off
chcp 65001 >nul
title LiteLLM - Update Model List

netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [NOTE] LiteLLM server not running - OK
) else (
    echo [WARNING] LiteLLM server is running!
    set /p choice="Continue anyway? (y/n): "
    if /i not "!choice!"=="y" exit /b 1
)

echo.
echo ==============================
echo   Updating Model List
echo ==============================
echo.

if exist "%~dp0.env_litellm" (
    for /f "usebackq eol=# delims=" %%a in ("%~dp0.env_litellm") do set "%%a"
)

if defined NVIDIA_NIM_API_KEY (
    echo [OK] API key loaded
) else (
    echo [ERROR] NVIDIA_NIM_API_KEY not found
    pause
    exit /b 1
)

echo.
echo Fetching models from NVIDIA NIM . . .
echo.

F:\miniconda3\python.exe "%~dp0update_models.py"

echo.
if errorlevel 1 (
    echo [FAILED] Update failed
) else (
    echo [OK] Done!
)
echo.
pause