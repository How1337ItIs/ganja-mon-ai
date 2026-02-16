@echo off
color 0A
echo.
echo ================================================================
echo        VB-CABLE COMPLETE FIX - AUTOMATED WALKTHROUGH
echo ================================================================
echo.
echo This script will guide you through:
echo   1. Uninstalling corrupted VB-Audio drivers
echo   2. Restarting Windows
echo   3. Installing fresh VB-Cable
echo   4. Testing the voice pipeline
echo.
echo IMPORTANT: This batch file MUST be run as Administrator!
echo            Right-click and select "Run as administrator"
echo.
pause

:STEP1
cls
echo.
echo ================================================================
echo STEP 1: UNINSTALL CORRUPTED DRIVERS
echo ================================================================
echo.
echo About to remove all VB-Audio devices and drivers
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
echo [OK] Drivers removed!
echo.
pause

:RESTART1
cls
echo.
echo ================================================================
echo STEP 2: FIRST RESTART REQUIRED
echo ================================================================
echo.
echo Windows MUST restart now to complete the uninstallation.
echo After restart, run this script again as Administrator.
echo.
echo When you return, the script will continue from installation.
echo.
set /p RESTART="Restart Windows now? (y/n): "
if /i "%RESTART%"=="y" (
    echo.
    echo Creating resume marker...
    echo INSTALL > vbcable_fix_state.txt
    echo.
    echo Restarting in 10 seconds...
    echo After restart: Run this script again as Administrator!
    timeout /t 10
    shutdown /r /t 0 /c "VB-Audio cleanup - Restart 1 of 2"
    exit
) else (
    echo.
    echo Please restart Windows manually, then run this script again.
    pause
    exit
)

:INSTALL
cls
echo.
echo ================================================================
echo STEP 3: INSTALL FRESH VB-CABLE
echo ================================================================
echo.
echo About to install clean VB-Cable driver
echo.
pause

if not exist "VBCABLE_Driver\VBCABLE_Setup_x64.exe" (
    echo [ERROR] VB-Cable installer not found!
    echo Expected: VBCABLE_Driver\VBCABLE_Setup_x64.exe
    echo.
    pause
    exit /b 1
)

echo.
echo Starting installer...
echo CLICK "INSTALL DRIVER" IN THE WINDOW
echo.

start /wait VBCABLE_Driver\VBCABLE_Setup_x64.exe

echo.
echo [OK] Installation complete!
echo.
pause

:RESTART2
cls
echo.
echo ================================================================
echo STEP 4: SECOND RESTART REQUIRED
echo ================================================================
echo.
echo Windows MUST restart again to load the new driver.
echo After restart, run this script again as Administrator to test.
echo.
set /p RESTART="Restart Windows now? (y/n): "
if /i "%RESTART%"=="y" (
    echo.
    echo Creating resume marker...
    echo TEST > vbcable_fix_state.txt
    echo.
    echo Restarting in 10 seconds...
    echo After restart: Run this script again to test!
    timeout /t 10
    shutdown /r /t 0 /c "VB-Audio install - Restart 2 of 2"
    exit
) else (
    echo.
    echo Please restart Windows manually, then run this script again.
    pause
    exit
)

:TEST
cls
echo.
echo ================================================================
echo STEP 5: TESTING VB-CABLE
echo ================================================================
echo.
echo Running status check...
echo.

cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe check_status.py
) else (
    echo [ERROR] Python virtual environment not found!
    echo Please ensure venv is set up correctly.
    pause
    exit /b 1
)

echo.
echo.
echo ================================================================
echo VERIFICATION COMPLETE
echo ================================================================
echo.
echo If the output shows a clean installation (2 devices only):
echo   - CABLE Input (OUTPUT device)
echo   - CABLE Output (INPUT device)
echo.
echo Then you're ready to test the voice pipeline!
echo.
echo Next steps:
echo   1. Open terminal in this folder
echo   2. Run: venv\Scripts\python.exe rasta_live.py --test
echo   3. If voice sounds good, run: venv\Scripts\python.exe rasta_live.py
echo.
echo Full instructions: VB_CABLE_FIX_STEPS.md
echo.
del vbcable_fix_state.txt 2>nul
pause
exit

:ENTRY_POINT
REM Check if resuming from restart
if exist "vbcable_fix_state.txt" (
    set /p STATE=<vbcable_fix_state.txt
    if "%STATE%"=="INSTALL" goto INSTALL
    if "%STATE%"=="TEST" goto TEST
)
goto STEP1
