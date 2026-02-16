# Sequential Thinking MCP Setup Guide

## Overview
Sequential Thinking MCP is an Anthropic MCP server that helps break down complex problems into structured, numbered steps. It enables you to revise previous thoughts, explore alternative approaches through branching, and test hypotheses with evidence-based reasoning.

## Prerequisites
- **Cursor version 0.4.5.9 or later** (required for MCP support)
- Node.js installed (for npx command)
- Internet connection (npx downloads package on first use)

## Installation in Cursor (Official Method)

### Via Cursor Settings UI (Recommended)
1. Open Cursor Settings (`Ctrl+,` or `Cmd+,`)
2. Navigate to **Features** → **MCP**
3. Click **"+ Add New MCP Server"**
4. Configure as follows:
   - **Name:** `sequential-thinking`
   - **Type/Transport:** `stdio`
   - **Command:** `npx`
   - **Args:** `-y @modelcontextprotocol/server-sequential-thinking`
5. Click **Save** or **Add**
6. **Refresh** the MCP servers list to populate tools
7. Restart Cursor if tools don't appear

### Alternative: Manual Configuration File

If you need to configure via file (e.g., for automation), the configuration should be:

**Configuration:**
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

**Note:** Cursor primarily uses the Settings UI for MCP configuration. File-based configuration may vary by Cursor version.

### Method 3: Using Docker (Alternative)
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

## Verification

After installation and restart, verify the tools are available:
1. Check Cursor Settings > Features > MCP - you should see "sequential-thinking" listed
2. The Composer Agent will automatically use MCP tools when relevant
3. Tool calls will be displayed for approval before execution
4. Available tools: `create_thoughts`, `revise_thought`, `branch_thought`, `summarize`

## Usage

Once configured, simply ask Claude/Composer to use sequential thinking:
- "Use Sequential Thinking to plan [task]"
- "Break down [problem] using Sequential Thinking"
- "Create a sequential thinking plan for [goal]"

**Note:** The Composer Agent automatically uses MCP tools when relevant. You don't need to explicitly call the tools - just describe what you want analyzed.

## Available Tools

| Tool | Purpose |
|------|---------|
| `create_thoughts` | Create initial sequence of thoughts |
| `revise_thought` | Revise any previous thought and auto-evaluate subsequent steps |
| `branch_thought` | Branch into alternative approaches |
| `summarize` | Generate summary of the thinking process |

## Troubleshooting

1. **Tools not appearing:**
   - Ensure Cursor version is **0.4.5.9 or later**
   - Restart Cursor completely after adding configuration
   - Click **Refresh** button in MCP settings to repopulate tools
   - Check that Node.js is installed (`node --version`)
   - Verify npx is available (`npx --version`)

2. **Connection errors:**
   - Ensure internet connection (npx downloads package on first use)
   - Check Cursor logs for MCP server errors (Help > Toggle Developer Tools)
   - Try the Docker method if npx fails

3. **Permission issues:**
   - Ensure Cursor has permission to execute npx
   - On Windows, may need to run Cursor as administrator
   - Check firewall/antivirus isn't blocking npx

4. **MCP server not connecting:**
   - Verify the server appears in Settings > Features > MCP
   - Check for error messages in the MCP server status
   - Try removing and re-adding the server configuration

## References

- [Official Sequential Thinking MCP Guide](https://mcp-hunt.com/blog/sequential-thinking-mcp-guide)
- [Cursor Directory - Sequential Thinking](https://cursor.directory/mcp/sequential-thinking)
- [Anthropic MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)
- [NPM Package](https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking)
- [Cursor Community Forum - Sequential Thinking](https://forum.cursor.com/t/how-to-use-sequential-thinking/50374)
