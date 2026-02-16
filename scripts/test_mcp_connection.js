// Test MCP Server Connection
// This script tests if the Sequential Thinking MCP server can start and respond

const { spawn } = require('child_process');
const path = require('path');

const mcpServerPath = path.join(
  process.env.USERPROFILE || process.env.HOME,
  '.npm-global',
  'node_modules',
  '@modelcontextprotocol',
  'server-sequential-thinking',
  'dist',
  'index.js'
);

console.log('Testing Sequential Thinking MCP Server...');
console.log('Path:', mcpServerPath);
console.log('');

// Test 1: Check if file exists
const fs = require('fs');
if (!fs.existsSync(mcpServerPath)) {
  console.error('❌ MCP server file not found at:', mcpServerPath);
  process.exit(1);
}
console.log('✅ MCP server file exists');

// Test 2: Try to start the server
console.log('Attempting to start MCP server...');
const server = spawn('node', [mcpServerPath], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let output = '';
let errorOutput = '';

server.stdout.on('data', (data) => {
  output += data.toString();
  console.log('STDOUT:', data.toString().trim());
});

server.stderr.on('data', (data) => {
  errorOutput += data.toString();
  console.log('STDERR:', data.toString().trim());
});

server.on('close', (code) => {
  console.log('');
  console.log('Server exited with code:', code);
  if (output.includes('Sequential Thinking') || output.includes('MCP')) {
    console.log('✅ MCP server appears to be working!');
  } else {
    console.log('⚠️  Server started but output unclear');
  }
  process.exit(0);
});

// Send a test MCP message (initialize)
setTimeout(() => {
  const initMessage = JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {
        name: 'test-client',
        version: '1.0.0'
      }
    }
  }) + '\n';
  
  server.stdin.write(initMessage);
  
  setTimeout(() => {
    server.kill();
  }, 2000);
}, 500);
