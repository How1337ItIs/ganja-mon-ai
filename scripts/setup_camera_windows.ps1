# Grok & Mon - USB Camera Setup for WSL
# ======================================
# Run this in Windows PowerShell (as Administrator)
#
# This script sets up USBIPD-WIN to pass USB webcam to WSL2

Write-Host "Grok & Mon - USB Camera Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell > Run as Administrator" -ForegroundColor Yellow
    exit 1
}

# Check if usbipd is installed
$usbipd = Get-Command usbipd -ErrorAction SilentlyContinue
if (-not $usbipd) {
    Write-Host "Installing USBIPD-WIN..." -ForegroundColor Yellow
    winget install usbipd
    Write-Host "Please restart this script after installation completes." -ForegroundColor Cyan
    exit 0
}

Write-Host "USBIPD-WIN is installed." -ForegroundColor Green
Write-Host ""

# List USB devices
Write-Host "Available USB Devices:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
usbipd list
Write-Host ""

# Find webcam (common VIDs: 046d=Logitech, 0c45=Microdia, 04f2=Chicony)
Write-Host "Looking for webcams..." -ForegroundColor Yellow
$devices = usbipd list | Select-String -Pattern "video|camera|webcam|046d|0c45|04f2" -CaseSensitive:$false

if ($devices) {
    Write-Host "Potential webcams found:" -ForegroundColor Green
    $devices | ForEach-Object { Write-Host $_ }
    Write-Host ""

    # Extract BUSID from first match
    $firstDevice = $devices[0].ToString()
    $busid = ($firstDevice -split '\s+')[0]

    Write-Host "Attaching device $busid to WSL..." -ForegroundColor Yellow

    # Bind the device (one-time)
    usbipd bind --busid $busid 2>$null

    # Attach to WSL
    usbipd attach --wsl --busid $busid

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "SUCCESS! Camera attached to WSL" -ForegroundColor Green
        Write-Host ""
        Write-Host "In WSL, run: ls /dev/video*" -ForegroundColor Cyan
        Write-Host "Then test with: python test_webcam.py" -ForegroundColor Cyan
    } else {
        Write-Host "Failed to attach. Try manually:" -ForegroundColor Red
        Write-Host "  usbipd bind --busid <BUSID>" -ForegroundColor Yellow
        Write-Host "  usbipd attach --wsl --busid <BUSID>" -ForegroundColor Yellow
    }
} else {
    Write-Host "No webcam detected automatically." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please identify your webcam from the list above and run:" -ForegroundColor Cyan
    Write-Host "  usbipd bind --busid <BUSID>" -ForegroundColor Yellow
    Write-Host "  usbipd attach --wsl --busid <BUSID>" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
