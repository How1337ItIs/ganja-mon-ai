# Fix Windows audio default after OBS closes
# This script ensures VB-Cable never stays as default output

# First, install AudioDeviceCmdlets if not present (requires admin, one-time)
# Install-Module -Name AudioDeviceCmdlets -Force

# Alternative: Use SoundVolumeView (NirSoft free utility)
# Download from: https://www.nirsoft.net/utils/sound_volume_view.html
# Then use: SoundVolumeView.exe /SetDefault "Speakers\Device\Realtek" all

Write-Host "Opening Sound Settings - please manually set default output device"
Start-Process "ms-settings:sound"

Write-Host @"

Manual steps:
1. Under 'Choose your output device', select your speakers or headphones
2. Scroll down to 'Advanced sound options'
3. Click 'App volume and device preferences'  
4. Set each app's output to your preferred device

To prevent this permanently:
- In OBS Settings > Audio, uncheck 'Disable Windows audio ducking'
- Don't set VB-Cable as Windows default - only use it in specific apps
"@
