@echo off
chcp 65001 >nul
title LiteLLM Proxy

if exist "%~dp0.env_litellm" (
    for /f "usebackq eol=# delims=" %%a in ("%~dp0.env_litellm") do set "%%a"
    echo [OK] Loaded .env_litellm
) else (
    echo [NOTE] .env_litellm not found
)

echo.
echo ==============================
echo   LiteLLM Proxy
echo ==============================
echo.
echo Config: %~dp0config_litellm.yaml
echo Port:   5000
echo URL:    http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop
echo ==============================
echo.

F:\miniconda3\Scripts\litellm.exe --config "%~dp0config_litellm.yaml" --port 5000 --host 127.0.0.1

echo.
echo Server stopped.
pause