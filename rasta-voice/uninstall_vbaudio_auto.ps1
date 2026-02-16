# VB-Audio Uninstaller Script (Automated - No Prompts)
# Run this as Administrator

Write-Host "=== VB-Audio Driver Uninstaller (AUTOMATED) ===" -ForegroundColor Cyan
Write-Host ""

# List VB-Audio devices
Write-Host "Searching for VB-Audio drivers..." -ForegroundColor Yellow
$devices = Get-PnpDevice -FriendlyName "*VB-Audio*" -ErrorAction SilentlyContinue

if ($devices) {
    Write-Host "Found $($devices.Count) VB-Audio device(s):" -ForegroundColor Green
    $devices | Format-Table -Property FriendlyName, Status, InstanceId

    Write-Host ""
    Write-Host "AUTO-UNINSTALLING (no confirmation)..." -ForegroundColor Yellow

    foreach ($device in $devices) {
        Write-Host "Uninstalling: $($device.FriendlyName)..." -ForegroundColor Yellow
        try {
            pnputil /remove-device $device.InstanceId
            Write-Host "  Success!" -ForegroundColor Green
        } catch {
            Write-Host "  Failed: $_" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "Removing VB-Audio driver packages..." -ForegroundColor Yellow
    $drivers = pnputil /enum-drivers | Select-String -Pattern "vbaudio" -Context 0,5
    if ($drivers) {
        Write-Host "Found VB-Audio driver packages, removing..."
        pnputil /delete-driver vbaudio*.inf /uninstall /force
    }

    Write-Host ""
    Write-Host "Driver uninstallation complete!" -ForegroundColor Green
    Write-Host "IMPORTANT: You MUST restart Windows now for changes to take effect." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please restart Windows manually, then run install_vbaudio.ps1" -ForegroundColor Yellow
} else {
    Write-Host "No VB-Audio devices found!" -ForegroundColor Green
    Write-Host "Either they're already uninstalled, or you need to check Device Manager manually." -ForegroundColor Yellow
}
