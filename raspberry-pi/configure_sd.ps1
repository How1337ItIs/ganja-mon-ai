# PowerShell script to configure SD card after flashing with Pi Imager
# Run AFTER flashing Pi OS Lite with Raspberry Pi Imager
# This copies megaphone files to the boot partition so they're available on first boot
#
# Usage: Right-click -> Run with PowerShell
#        Or: powershell -ExecutionPolicy Bypass -File configure_sd.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  CONFIGURE SD CARD FOR MEGAPHONE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Find the boot partition (FAT32 partition on the SD card)
$bootDrive = $null
$removableDrives = Get-Volume | Where-Object { $_.FileSystemLabel -eq 'bootfs' -or $_.FileSystemLabel -eq 'boot' }

if ($removableDrives) {
    $bootDrive = ($removableDrives | Select-Object -First 1).DriveLetter + ":"
    Write-Host "Found boot partition: $bootDrive" -ForegroundColor Cyan
} else {
    # Try to find by looking for removable drives with cmdline.txt
    foreach ($drive in (Get-PSDrive -PSProvider FileSystem)) {
        if (Test-Path "$($drive.Root)cmdline.txt") {
            $bootDrive = $drive.Root.TrimEnd('\')
            Write-Host "Found boot partition: $bootDrive" -ForegroundColor Cyan
            break
        }
    }
}

if (-not $bootDrive) {
    Write-Host "ERROR: Could not find Pi boot partition!" -ForegroundColor Red
    Write-Host "Make sure:"
    Write-Host "  1. SD card is inserted in card reader"
    Write-Host "  2. SD card was flashed with Raspberry Pi Imager"
    Write-Host "  3. The 'bootfs' partition is accessible"
    Read-Host "Press Enter to exit"
    exit 1
}

# Script directory (where megaphone files are)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Copy megaphone files to boot partition
Write-Host ""
Write-Host "Copying megaphone files to $bootDrive..." -ForegroundColor Yellow

$files = @("megaphone.py", "requirements.txt", ".env", "voice_config.json", "rasta-megaphone.service", "firstboot.sh")
foreach ($file in $files) {
    $src = Join-Path $scriptDir $file
    if (Test-Path $src) {
        Copy-Item $src -Destination "$bootDrive\" -Force
        Write-Host "  Copied: $file" -ForegroundColor Green
    } else {
        Write-Host "  Missing: $file (skipped)" -ForegroundColor Yellow
    }
}

# Ensure SSH is enabled (empty file named 'ssh' on boot partition)
if (-not (Test-Path "$bootDrive\ssh")) {
    New-Item -Path "$bootDrive\ssh" -ItemType File -Force | Out-Null
    Write-Host "  Created: ssh (enables SSH)" -ForegroundColor Green
}

# Create WiFi config if not already present
$wpaFile = "$bootDrive\wpa_supplicant.conf"
if (-not (Test-Path $wpaFile)) {
    $wpaContent = @"
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
    ssid="no more mr wifi"
    psk="Gr@t3fuld3ad"
    key_mgmt=WPA-PSK
}
"@
    Set-Content -Path $wpaFile -Value $wpaContent -Encoding ASCII
    Write-Host "  Created: wpa_supplicant.conf (WiFi config)" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SD CARD CONFIGURED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Safely eject the SD card"
Write-Host "  2. Insert SD card into Raspberry Pi"
Write-Host "  3. Power on the Pi"
Write-Host "  4. Wait 2-3 minutes for first boot"
Write-Host "  5. From WSL, run:" -ForegroundColor Yellow
Write-Host "     cd raspberry-pi && bash auto_deploy.sh" -ForegroundColor White
Write-Host ""
Write-Host "Or for instant setup (if firstboot.sh works):"
Write-Host "  The Pi will auto-install everything on first boot!"
Write-Host "  Just plug in mic + speaker and it should start."
Write-Host ""
Read-Host "Press Enter to exit"
