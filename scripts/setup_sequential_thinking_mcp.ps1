# Setup Sequential Thinking MCP for Cursor
# Run this script to configure Sequential Thinking MCP in Cursor

Write-Host "Setting up Sequential Thinking MCP for Cursor..." -ForegroundColor Green

# Possible Cursor settings locations
$possiblePaths = @(
    "$env:APPDATA\Cursor\User\settings.json",
    "$env:USERPROFILE\.cursor\mcp.json",
    "$env:APPDATA\Cursor\mcp.json"
)

$mcpConfig = @{
    mcpServers = @{
        "sequential-thinking" = @{
            command = "npx"
            args = @("-y", "@modelcontextprotocol/server-sequential-thinking")
        }
    }
}

# Try to find existing settings file
$settingsPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $settingsPath = $path
        Write-Host "Found settings file at: $path" -ForegroundColor Yellow
        break
    }
}

if (-not $settingsPath) {
    Write-Host "Cursor settings file not found in standard locations." -ForegroundColor Yellow
    Write-Host "Please manually add the following to your Cursor MCP configuration:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host (($mcpConfig | ConvertTo-Json -Depth 10) -replace '`n', "`n") -ForegroundColor White
    Write-Host ""
    Write-Host "To find your Cursor settings:" -ForegroundColor Cyan
    Write-Host "1. Open Cursor Settings (Ctrl+,)" -ForegroundColor White
    Write-Host "2. Go to Features > MCP" -ForegroundColor White
    Write-Host "3. Click '+ Add New MCP Server'" -ForegroundColor White
    Write-Host "4. Use the configuration above" -ForegroundColor White
    exit
}

# Read existing settings
try {
    $existingSettings = Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable
} catch {
    Write-Host "Could not parse existing settings. Creating new configuration..." -ForegroundColor Yellow
    $existingSettings = @{}
}

# Merge MCP configuration
if (-not $existingSettings.mcpServers) {
    $existingSettings.mcpServers = @{}
}

if ($existingSettings.mcpServers."sequential-thinking") {
    Write-Host "Sequential Thinking MCP already configured!" -ForegroundColor Green
} else {
    $existingSettings.mcpServers."sequential-thinking" = $mcpConfig.mcpServers."sequential-thinking"
    
    # Backup original
    $backupPath = "$settingsPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $settingsPath $backupPath
    Write-Host "Backup created: $backupPath" -ForegroundColor Yellow
    
    # Write updated settings
    $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
    Write-Host "Sequential Thinking MCP configured successfully!" -ForegroundColor Green
    Write-Host "Please restart Cursor for changes to take effect." -ForegroundColor Cyan
}
