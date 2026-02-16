# VB-Cable Installer Script
# Run this as Administrator AFTER restarting Windows

Write-Host "=== VB-Cable Fresh Installation ===" -ForegroundColor Cyan
Write-Host ""

$installerPath = "C:\Users\natha\sol-cannabis\rasta-voice\VBCABLE_Driver"

# Check if installer exists
if (Test-Path "$installerPath\VBCABLE_Setup_x64.exe") {
    Write-Host "Found VB-Cable installer!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting installation..." -ForegroundColor Yellow
    Write-Host "Click 'Install Driver' in the window that appears." -ForegroundColor Yellow
    Write-Host ""

    # Run installer with admin rights
    Start-Process -FilePath "$installerPath\VBCABLE_Setup_x64.exe" -Verb RunAs -Wait

    Write-Host ""
    Write-Host "Installation complete!" -ForegroundColor Green
    Write-Host "IMPORTANT: You MUST restart Windows again for the driver to load." -ForegroundColor Red
    Write-Host ""
    $restart = Read-Host "Restart Windows now? (y/n)"
    if ($restart -eq 'y' -or $restart -eq 'Y') {
        Restart-Computer -Force
    }
} else {
    Write-Host "ERROR: VB-Cable installer not found!" -ForegroundColor Red
    Write-Host "Expected location: $installerPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please download VB-Cable from: https://vb-audio.com/Cable/" -ForegroundColor Yellow
    Write-Host "Extract the ZIP to: $installerPath" -ForegroundColor Yellow
}
