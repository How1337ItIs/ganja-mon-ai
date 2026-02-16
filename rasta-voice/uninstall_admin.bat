@echo off
:: Batch file to run uninstaller with UAC elevation
echo Requesting Administrator privileges...
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0uninstall_vbaudio_auto.ps1\"' -Verb RunAs"
