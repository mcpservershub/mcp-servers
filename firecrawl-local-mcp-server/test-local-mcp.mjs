#!/usr/bin/env node

// Test script for Firecrawl Local MCP Server
// This script tests the MCP server in local mode

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Set environment variables for local mode
const env = {
  ...process.env,
  FIRECRAWL_API_URL: 'http://localhost:3002',
  FIRECRAWL_MODE: 'local',
  LOGGING_LEVEL: 'debug'
};

console.log('🚀 Starting Firecrawl Local MCP Server Test');
console.log('📍 API URL:', env.FIRECRAWL_API_URL);
console.log('🔧 Mode:', env.FIRECRAWL_MODE);
console.log('');

// Start the MCP server
const serverPath = path.join(__dirname, 'dist', 'index.js');
const mcp = spawn('node', [serverPath], { 
  env,
  stdio: ['pipe', 'pipe', 'pipe']
});

let outputBuffer = '';
let errorBuffer = '';

// Handle server output
mcp.stdout.on('data', (data) => {
  outputBuffer += data.toString();
  // Look for initialization message
  if (outputBuffer.includes('Running in LOCAL mode')) {
    console.log('✅ Server detected local mode successfully');
  }
  if (outputBuffer.includes('MCP Server initialized')) {
    console.log('✅ MCP Server initialized successfully');
    
    // Send a test request after initialization
    setTimeout(() => {
      console.log('\n📋 Sending test request to list tools...');
      const testRequest = {
        jsonrpc: '2.0',
        method: 'tools/list',
        id: 1
      };
      
      mcp.stdin.write(JSON.stringify(testRequest) + '\n');
    }, 1000);
  }
  
  // Check for tools response
  if (outputBuffer.includes('firecrawl_scrape')) {
    console.log('✅ Tools listing successful - found firecrawl_scrape');
    console.log('✅ All tests passed!');
    
    // Clean exit
    setTimeout(() => {
      mcp.kill();
      process.exit(0);
    }, 500);
  }
});

// Handle server errors
mcp.stderr.on('data', (data) => {
  errorBuffer += data.toString();
  // Check for expected local mode message
  if (errorBuffer.includes('Running in LOCAL mode')) {
    console.log('✅ Local mode confirmed');
  }
  // Only show actual errors, not info messages
  if (!errorBuffer.includes('Running in') && !errorBuffer.includes('MCP Server')) {
    console.error('Server stderr:', data.toString());
  }
});

// Handle server exit
mcp.on('close', (code) => {
  if (code !== 0 && code !== null) {
    console.error(`❌ Server exited with code ${code}`);
    console.error('Error output:', errorBuffer);
    process.exit(1);
  }
});

// Handle errors
mcp.on('error', (err) => {
  console.error('❌ Failed to start server:', err);
  process.exit(1);
});

// Timeout after 10 seconds
setTimeout(() => {
  console.error('❌ Test timeout - server did not respond');
  mcp.kill();
  process.exit(1);
}, 10000);

console.log('⏳ Waiting for server to initialize...');