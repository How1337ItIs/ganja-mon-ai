# Sequential Thinking MCP Troubleshooting Guide

## Quick Verification Steps

### 1. Check Cursor MCP Settings
1. Open Cursor Settings (`Ctrl+,`)
2. Navigate to **Features** → **MCP**
3. Look for "sequential-thinking" in the list
4. Check status:
   - ✅ **Green/Connected** = Working
   - ⚠️ **Yellow/Disconnected** = Not connected
   - ❌ **Red/Error** = Configuration issue

### 2. If Not Connected

**Option A: Use Full Path to NPX**
1. Find npx path: Run `where npx` or `(Get-Command npx).Source` in PowerShell
2. In Cursor MCP settings, change command from `npx` to full path:
   ```
   C:\Program Files\nodejs\npx.cmd
   ```
   (Use your actual path)

**Option B: Install Package Globally**
```bash
npm install -g @modelcontextprotocol/server-sequential-thinking
```

Then in Cursor settings, use:
- Command: `node`
- Args: `C:\Users\[YourUser]\AppData\Roaming\npm\node_modules\@modelcontextprotocol\server-sequential-thinking\dist\index.js`
(Adjust path to your npm global modules location)

**Option C: Check Cursor Version**
- Requires Cursor 0.4.5.9 or later
- Check: Help → About
- Update if needed

### 3. Check Developer Tools for Errors
1. Help → Toggle Developer Tools
2. Check Console tab for MCP errors
3. Look for messages about "sequential-thinking" or MCP connection failures

### 4. Verify Configuration File
Location: `%APPDATA%\Cursor\User\settings.json`

Should contain:
```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### 5. Test MCP Server Manually
Run in terminal:
```bash
npx -y @modelcontextprotocol/server-sequential-thinking
```

If this works but Cursor doesn't connect, it's a Cursor configuration issue.

## Common Issues & Solutions

### Issue: "Client closed" or "Connection failed"
**Solution:** 
- Restart Cursor completely
- Check Node.js is in PATH
- Try using full path to npx/node

### Issue: "Package not found"
**Solution:**
- Check internet connection
- Try: `npm cache clean --force`
- Re-run: `npx -y @modelcontextprotocol/server-sequential-thinking`

### Issue: Tools not appearing
**Solution:**
- MCP tools appear in Composer Agent, not regular chat
- Try asking: "Use Sequential Thinking to plan [task]"
- Check MCP status shows "Connected"

### Issue: Permission denied
**Solution:**
- Run Cursor as Administrator (Windows)
- Check antivirus isn't blocking npx
- Verify Node.js installation

## Verification Checklist

- [ ] Node.js installed (v18+)
- [ ] NPX available in PATH
- [ ] MCP server package can run manually
- [ ] Cursor version 0.4.5.9+
- [ ] Configuration in settings.json
- [ ] MCP shows as "Connected" in Cursor settings
- [ ] No errors in Developer Tools console
- [ ] Tried restarting Cursor

## Still Not Working?

1. **Remove and re-add MCP server:**
   - Delete from Cursor settings
   - Restart Cursor
   - Add again with full path to npx

2. **Try Docker method:**
   ```json
   {
     "mcpServers": {
       "sequential-thinking": {
         "command": "docker",
         "args": ["run", "--rm", "-i", "mcp/sequentialthinking"]
       }
     }
   }
   ```

3. **Check Cursor logs:**
   - `%APPDATA%\Cursor\logs\` directory
   - Look for MCP-related errors

4. **Post on Cursor Forum:**
   - Include error messages
   - Include your configuration (sanitized)
   - Include Cursor version
