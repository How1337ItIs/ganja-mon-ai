# Test Sequential Thinking MCP Server
# This script verifies the MCP server can run and provides diagnostics

Write-Host "Testing Sequential Thinking MCP Server..." -ForegroundColor Green
Write-Host ""

# Test 1: Node.js version
Write-Host "Test 1: Node.js Version" -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -lt 18) {
        Write-Host "  ⚠️  Warning: Node.js 18+ recommended" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Node.js not found!" -ForegroundColor Red
    exit 1
}

# Test 2: NPX availability
Write-Host ""
Write-Host "Test 2: NPX Availability" -ForegroundColor Yellow
try {
    $npxVersion = npx --version
    Write-Host "  ✅ NPX: $npxVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ NPX not found!" -ForegroundColor Red
    exit 1
}

# Test 3: Test MCP server package download
Write-Host ""
Write-Host "Test 3: MCP Server Package Test" -ForegroundColor Yellow
Write-Host "  Testing package download and execution..." -ForegroundColor Gray
try {
    $testOutput = npx -y @modelcontextprotocol/server-sequential-thinking --help 2>&1 | Out-String
    if ($testOutput -match "Sequential Thinking|stdio|MCP") {
        Write-Host "  ✅ MCP server package works!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Package runs but output unexpected:" -ForegroundColor Yellow
        Write-Host "  $testOutput" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ Failed to run MCP server package!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 4: Check Cursor settings file
Write-Host ""
Write-Host "Test 4: Cursor Configuration" -ForegroundColor Yellow
$settingsPath = "$env:APPDATA\Cursor\User\settings.json"
if (Test-Path $settingsPath) {
    Write-Host "  ✅ Settings file found: $settingsPath" -ForegroundColor Green
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if ($settings.mcpServers.'sequential-thinking') {
            Write-Host "  ✅ Sequential Thinking MCP configured" -ForegroundColor Green
            Write-Host "  Configuration:" -ForegroundColor Gray
            $settings.mcpServers.'sequential-thinking' | ConvertTo-Json -Depth 5 | Write-Host
        } else {
            Write-Host "  ❌ Sequential Thinking MCP not found in settings!" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ⚠️  Could not parse settings file: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  Settings file not found at: $settingsPath" -ForegroundColor Yellow
}

# Test 5: Find npx full path
Write-Host ""
Write-Host "Test 5: NPX Full Path" -ForegroundColor Yellow
try {
    $npxPath = (Get-Command npx).Source
    Write-Host "  ✅ NPX path: $npxPath" -ForegroundColor Green
    Write-Host "  💡 If MCP doesn't work, try using this full path in Cursor settings" -ForegroundColor Cyan
} catch {
    Write-Host "  ⚠️  Could not find npx path" -ForegroundColor Yellow
}

# Test 6: Check if package is installed globally
Write-Host ""
Write-Host "Test 6: Global Package Check" -ForegroundColor Yellow
try {
    $globalCheck = npm list -g @modelcontextprotocol/server-sequential-thinking 2>&1 | Out-String
    if ($globalCheck -match "@modelcontextprotocol/server-sequential-thinking") {
        Write-Host "  ✅ Package installed globally" -ForegroundColor Green
        $globalPath = npm root -g
        Write-Host "  Global modules: $globalPath" -ForegroundColor Gray
    } else {
        Write-Host "  ℹ️  Package not installed globally (using npx is fine)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️  Could not check global packages" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify in Cursor: Settings -> Features -> MCP" -ForegroundColor White
Write-Host "2. Check if 'sequential-thinking' shows as 'Connected' (green)" -ForegroundColor White
Write-Host "3. If not connected, check for error messages" -ForegroundColor White
Write-Host "4. Try using full path to npx if connection fails" -ForegroundColor White
Write-Host "5. Check Cursor version (needs 0.4.5.9+)" -ForegroundColor White
Write-Host ""
Write-Host "If still not working, try:" -ForegroundColor Yellow
Write-Host "- Install package globally: npm install -g @modelcontextprotocol/server-sequential-thinking" -ForegroundColor White
Write-Host "- Use full node path in Cursor settings" -ForegroundColor White
Write-Host "- Check Cursor Developer Tools for errors" -ForegroundColor White
