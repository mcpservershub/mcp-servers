#!/usr/bin/env node

// Simple test to verify the MCP server starts correctly
import { spawn } from 'child_process';
import { writeFileSync, unlinkSync } from 'fs';

console.log('Testing PostgreSQL MCP Server...');

// Create a test request to list available tools
const testRequest = {
  jsonrpc: '2.0',
  method: 'tools/list',
  id: 1
};

// Start the MCP server
const serverProcess = spawn('node', ['dist/index.js'], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let responseBuffer = '';

serverProcess.stdout.on('data', (data) => {
  responseBuffer += data.toString();
  
  // Try to parse complete JSON responses
  const lines = responseBuffer.split('\n');
  for (let i = 0; i < lines.length - 1; i++) {
    const line = lines[i].trim();
    if (line) {
      try {
        const response = JSON.parse(line);
        console.log('Response:', JSON.stringify(response, null, 2));
        
        if (response.result && response.result.tools) {
          console.log('\n✅ MCP Server is working! Available tools:');
          response.result.tools.forEach(tool => {
            console.log(`  - ${tool.name}: ${tool.description}`);
          });
          
          // Clean exit
          serverProcess.kill();
          process.exit(0);
        }
      } catch (e) {
        // Not a complete JSON yet, continue
      }
    }
  }
  
  // Keep the last incomplete line in the buffer
  responseBuffer = lines[lines.length - 1];
});

serverProcess.stderr.on('data', (data) => {
  console.error('Server error:', data.toString());
});

serverProcess.on('error', (error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

serverProcess.on('close', (code) => {
  if (code !== 0) {
    console.error(`Server exited with code ${code}`);
    process.exit(1);
  }
});

// Send test request after a short delay
setTimeout(() => {
  console.log('Sending test request...');
  serverProcess.stdin.write(JSON.stringify(testRequest) + '\n');
}, 500);

// Timeout after 5 seconds
setTimeout(() => {
  console.error('❌ Test timeout - no response from server');
  serverProcess.kill();
  process.exit(1);
}, 5000);