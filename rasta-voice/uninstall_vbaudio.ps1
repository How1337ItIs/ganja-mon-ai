# VB-Audio Uninstaller Script
# Run this as Administrator

Write-Host "=== VB-Audio Driver Uninstaller ===" -ForegroundColor Cyan
Write-Host ""

# List VB-Audio devices
Write-Host "Searching for VB-Audio drivers..." -ForegroundColor Yellow
$devices = Get-PnpDevice -FriendlyName "*VB-Audio*" -ErrorAction SilentlyContinue

if ($devices) {
    Write-Host "Found $($devices.Count) VB-Audio device(s):" -ForegroundColor Green
    $devices | Format-Table -Property FriendlyName, Status, InstanceId

    Write-Host ""
    $confirm = Read-Host "Do you want to uninstall these devices? (y/n)"

    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
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
            Write-Host "Found VB-Audio driver packages"
            pnputil /delete-driver vbaudio*.inf /uninstall /force
        }

        Write-Host ""
        Write-Host "Driver uninstallation complete!" -ForegroundColor Green
        Write-Host "IMPORTANT: You MUST restart Windows now for changes to take effect." -ForegroundColor Red
        Write-Host ""
        $restart = Read-Host "Restart Windows now? (y/n)"
        if ($restart -eq 'y' -or $restart -eq 'Y') {
            Restart-Computer -Force
        }
    }
} else {
    Write-Host "No VB-Audio devices found!" -ForegroundColor Green
    Write-Host "Either they're already uninstalled, or you need to check Device Manager manually." -ForegroundColor Yellow
}
