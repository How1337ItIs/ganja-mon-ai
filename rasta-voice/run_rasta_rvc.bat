@echo off
echo Starting Rasta Voice Pipeline (RVC)...
cd /d "%~dp0"
.venv-rvc\Scripts\python.exe rasta_live_rvc.py %*
pause
