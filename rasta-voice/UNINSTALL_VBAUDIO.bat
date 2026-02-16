@echo off
echo ============================================
echo VB-Audio Driver Uninstaller
echo ============================================
echo.
echo This will remove ALL VB-Audio drivers
echo.
pause

echo.
echo Removing VB-Audio devices...
echo.

for /f "tokens=*" %%i in ('powershell -Command "Get-PnpDevice -FriendlyName '*VB-Audio*' | Select-Object -ExpandProperty InstanceId"') do (
    echo Removing device: %%i
    pnputil /remove-device "%%i"
)

echo.
echo Removing VB-Audio driver packages...
echo.
pnputil /delete-driver vbaudio*.inf /uninstall /force 2>nul

echo.
echo ============================================
echo Uninstall complete!
echo ============================================
echo.
echo IMPORTANT: You MUST restart Windows now!
echo.
pause

echo.
set /p RESTART="Restart Windows now? (y/n): "
if /i "%RESTART%"=="y" shutdown /r /t 5 /c "Restarting for VB-Audio uninstall"

echo.
echo Please restart Windows manually before proceeding.
pause
