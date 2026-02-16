@echo off
title Ganja Mon Translator Dashboard
color 0A

echo ==================================================
echo    Ganja Mon Translator Dashboard Launcher
echo ==================================================
echo.

cd /d "%~dp0"

if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please ensure .env exists with XAI_API_KEY.
    pause
    exit /b
)

echo Starting server...
python grok_translate_dashboard.py

pause
