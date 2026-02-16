@echo off
echo ============================================
echo VB-Cable Fresh Installation
echo ============================================
echo.
echo This will install VB-Cable (standard version)
echo.
pause

if not exist "VBCABLE_Driver\VBCABLE_Setup_x64.exe" (
    echo ERROR: VB-Cable installer not found!
    echo Please ensure VBCABLE_Driver\VBCABLE_Setup_x64.exe exists
    pause
    exit /b 1
)

echo.
echo Starting VB-Cable installer...
echo Click "Install Driver" in the window that appears
echo.

start /wait VBCABLE_Driver\VBCABLE_Setup_x64.exe

echo.
echo ============================================
echo Installation complete!
echo ============================================
echo.
echo IMPORTANT: You MUST restart Windows now!
echo.
pause

echo.
set /p RESTART="Restart Windows now? (y/n): "
if /i "%RESTART%"=="y" shutdown /r /t 5 /c "Restarting for VB-Audio install"

echo.
echo Please restart Windows manually before testing.
pause
