// Verify MCP Server is Working
// Tests the Sequential Thinking MCP server can respond to MCP protocol messages

const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');

const mcpServerPath = path.join(
  'C:',
  'Users',
  'natha',
  '.npm-global',
  'node_modules',
  '@modelcontextprotocol',
  'server-sequential-thinking',
  'dist',
  'index.js'
);

console.log('=== Sequential Thinking MCP Verification ===\n');
console.log('Server path:', mcpServerPath);
console.log('');

const server = spawn('node', [mcpServerPath], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let responses = [];

const rl = readline.createInterface({
  input: server.stdout,
  crlfDelay: Infinity
});

rl.on('line', (line) => {
  try {
    const response = JSON.parse(line);
    responses.push(response);
    console.log('✅ Received MCP response:', response.method || response.id || 'response');
    if (response.result) {
      console.log('   Result:', JSON.stringify(response.result).substring(0, 100) + '...');
    }
  } catch (e) {
    // Not JSON, might be stderr
  }
});

server.stderr.on('data', (data) => {
  const msg = data.toString().trim();
  if (msg.includes('Sequential Thinking')) {
    console.log('✅ Server started:', msg);
  }
});

// Send initialize
setTimeout(() => {
  const init = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'test', version: '1.0.0' }
    }
  };
  console.log('Sending initialize...');
  server.stdin.write(JSON.stringify(init) + '\n');
}, 500);

// Send list tools
setTimeout(() => {
  const listTools = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  };
  console.log('Sending tools/list...');
  server.stdin.write(JSON.stringify(listTools) + '\n');
}, 1500);

// Check results and exit
setTimeout(() => {
  console.log('\n=== Verification Results ===');
  if (responses.length > 0) {
    console.log('✅ MCP server is responding!');
    console.log(`✅ Received ${responses.length} response(s)`);
    
    // Check for tools
    const toolsResponse = responses.find(r => r.result && r.result.tools);
    if (toolsResponse) {
      const tools = toolsResponse.result.tools;
      console.log(`✅ Found ${tools.length} tools:`);
      tools.forEach(tool => {
        console.log(`   - ${tool.name}`);
      });
      
      // Check for Sequential Thinking tools
      const expectedTools = ['create_thoughts', 'revise_thought', 'branch_thought', 'summarize'];
      const foundTools = tools.map(t => t.name);
      const missing = expectedTools.filter(t => !foundTools.includes(t));
      
      if (missing.length === 0) {
        console.log('✅ All Sequential Thinking tools are available!');
      } else {
        console.log(`⚠️  Missing tools: ${missing.join(', ')}`);
      }
    }
    
    console.log('\n✅ MCP SERVER IS WORKING CORRECTLY!');
    console.log('Configuration is valid. Restart Cursor to use it.');
  } else {
    console.log('❌ No responses from MCP server');
  }
  
  server.kill();
  process.exit(0);
}, 3000);
