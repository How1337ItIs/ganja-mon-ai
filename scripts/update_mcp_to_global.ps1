# Update MCP Configuration to Use Global Installation
$settingsPath = "$env:APPDATA\Cursor\User\settings.json"
$globalPath = "C:\Users\natha\.npm-global\node_modules\@modelcontextprotocol\server-sequential-thinking\dist\index.js"

Write-Host "Updating MCP configuration to use global installation..." -ForegroundColor Green

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
        $settings.mcpServers | Add-Member -MemberType NoteProperty -Name "sequential-thinking" -Value @{}
    }
    
    $settings.mcpServers.'sequential-thinking'.command = "node"
    $settings.mcpServers.'sequential-thinking'.args = @($globalPath)
    
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
