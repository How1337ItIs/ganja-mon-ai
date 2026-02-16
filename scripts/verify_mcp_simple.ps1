# Simple MCP Verification Script
Write-Host "=== Sequential Thinking MCP Verification ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Node.js
Write-Host "Node.js:" -NoNewline
$nodeVer = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " $nodeVer" -ForegroundColor Green
} else {
    Write-Host " NOT FOUND" -ForegroundColor Red
    exit 1
}

# Test 2: NPX
Write-Host "NPX:" -NoNewline
$npxVer = npx --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " $npxVer" -ForegroundColor Green
} else {
    Write-Host " NOT FOUND" -ForegroundColor Red
    exit 1
}

# Test 3: NPX Path
Write-Host "NPX Path:" -NoNewline
try {
    $npxPath = (Get-Command npx).Source
    Write-Host " $npxPath" -ForegroundColor Green
} catch {
    Write-Host " Could not find" -ForegroundColor Yellow
}

# Test 4: Configuration
Write-Host "Configuration:" -NoNewline
$settingsPath = "$env:APPDATA\Cursor\User\settings.json"
if (Test-Path $settingsPath) {
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if ($settings.mcpServers.'sequential-thinking') {
            Write-Host " Found in settings.json" -ForegroundColor Green
        } else {
            Write-Host " NOT FOUND in settings" -ForegroundColor Red
        }
    } catch {
        Write-Host " Could not parse settings" -ForegroundColor Yellow
    }
} else {
    Write-Host " Settings file not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Open Cursor Settings (Ctrl+,)"
Write-Host "2. Go to Features -> MCP"
Write-Host "3. Verify 'sequential-thinking' shows as Connected (green)"
Write-Host "4. If not connected, check error messages"
Write-Host "5. Try using full NPX path: $npxPath" -ForegroundColor Yellow
