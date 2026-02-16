# GitHub MCP token (wrapper script)

Adding the token **inside** `mcp.json` can cause the GitHub MCP server to fail to start in Cursor. The fix is a **wrapper script** that reads the token from a file and runs the GitHub MCP.

## One-time setup

### 1. Create the token file

Create a file named **`.github-mcp-token`** in your user profile folder with your GitHub Personal Access Token as the only content (one line, no quotes):

- Path: **`C:\Users\natha\.github-mcp-token`**
- Content: paste your token, save, close.

```powershell
# Or from PowerShell:
Set-Content -Path $env:USERPROFILE\.github-mcp-token -Value "YOUR_TOKEN_HERE" -NoNewline
```

### 2. Wrapper script (already in place)

- Script: **`C:\Users\natha\.cursor\scripts\github-mcp.cmd`**
- It reads `%USERPROFILE%\.github-mcp-token`, sets `GITHUB_TOKEN`, and runs `npx -y @modelcontextprotocol/server-github`.

Your **`C:\Users\natha\.cursor\mcp.json`** is configured to use this script instead of calling `npx` directly.

### 3. Restart Cursor

Fully quit and restart Cursor. GitHub MCP should start with the token and give you higher API rate limits (including code search).

## If the token file is missing

You'll see an error in MCP logs: *"Create C:\Users\natha\.github-mcp-token with your GitHub token"*. Create that file and restart.

## Alternative: Windows environment variable

If you prefer not to use a file, set a **User** env var `GITHUB_TOKEN` (e.g. via System Properties → Environment Variables). Cursor may or may not pass it to the MCP process; the wrapper is more reliable.

## Security

- Don't commit `.github-mcp-token` or put it in any repo. It lives in your profile only.
- Revoke and recreate the token if it's ever exposed (e.g. in chat or logs).
