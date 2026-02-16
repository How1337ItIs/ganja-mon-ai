# Fix MCP Configuration with Full NPX Path
# This updates the config to use full path to npx

$settingsPath = "$env:APPDATA\Cursor\User\settings.json"
$npxPath = "C:\Program Files\nodejs\npx.ps1"

Write-Host "Updating MCP configuration with full NPX path..." -ForegroundColor Green

if (-not (Test-Path $settingsPath)) {
    Write-Host "Settings file not found!" -ForegroundColor Red
    exit 1
}

try {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    
    if (-not $settings.mcpServers) {
        $settings | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value @{}
    }
    
    if (-not $settings.mcpServers.'sequential-thinking') {
        Write-Host "Creating sequential-thinking configuration..." -ForegroundColor Yellow
        $settings.mcpServers | Add-Member -MemberType NoteProperty -Name "sequential-thinking" -Value @{
            command = $npxPath
            args = @("-y", "@modelcontextprotocol/server-sequential-thinking")
        }
    } else {
        Write-Host "Updating sequential-thinking configuration..." -ForegroundColor Yellow
        $settings.mcpServers.'sequential-thinking'.command = $npxPath
    }
    
    # Backup
    $backupPath = "$settingsPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $settingsPath $backupPath
    Write-Host "Backup created: $backupPath" -ForegroundColor Gray
    
    # Save
    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
    Write-Host "Configuration updated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Updated configuration:" -ForegroundColor Cyan
    $settings.mcpServers.'sequential-thinking' | ConvertTo-Json -Depth 5
    Write-Host ""
    Write-Host "Please restart Cursor for changes to take effect." -ForegroundColor Yellow
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
