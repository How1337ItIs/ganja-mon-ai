# Fix HOME environment variable for Playwright/Antigravity browser subagent
# This sets HOME at the user level so it persists across sessions

$homePath = $env:USERPROFILE
[Environment]::SetEnvironmentVariable("HOME", $homePath, "User")

# Verify it was set
$verifyHome = [Environment]::GetEnvironmentVariable("HOME", "User")
Write-Host "HOME environment variable set to: $verifyHome"
Write-Host ""
Write-Host "SUCCESS! Please restart Antigravity/VS Code for changes to take effect."
