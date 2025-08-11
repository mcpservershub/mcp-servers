#!/usr/bin/env node

/**
 * Test script for verifying output_file functionality
 * Run with: node test-output-files.js
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

// Test output directory
const OUTPUT_DIR = 'test-outputs';

// Create test output directory
async function setupTestDir() {
  try {
    await fs.mkdir(OUTPUT_DIR, { recursive: true });
    console.log(`✓ Created test directory: ${OUTPUT_DIR}`);
  } catch (error) {
    console.error('Failed to create test directory:', error);
  }
}

// Test cases for tools with output_file
const testCases = [
  {
    name: 'Navigate with output',
    tool: 'puppeteer_navigate',
    args: {
      url: 'https://example.com',
      output_file: `${OUTPUT_DIR}/navigation-result.json`
    },
    validate: async (file) => {
      const content = JSON.parse(await fs.readFile(file, 'utf-8'));
      return content.url && content.title && content.status;
    }
  },
  {
    name: 'Screenshot with output',
    tool: 'puppeteer_screenshot',
    args: {
      fullPage: true,
      format: 'png',
      output_file: `${OUTPUT_DIR}/screenshot.png`
    },
    validate: async (file) => {
      const stats = await fs.stat(file);
      return stats.size > 0;
    }
  },
  {
    name: 'Get content with output',
    tool: 'puppeteer_get_content',
    args: {
      type: 'text',
      output_file: `${OUTPUT_DIR}/page-content.txt`
    },
    validate: async (file) => {
      const content = await fs.readFile(file, 'utf-8');
      return content.length > 0;
    }
  },
  {
    name: 'Extract links with output',
    tool: 'puppeteer_extract_links',
    args: {
      includeText: true,
      output_file: `${OUTPUT_DIR}/links.json`
    },
    validate: async (file) => {
      const content = JSON.parse(await fs.readFile(file, 'utf-8'));
      return Array.isArray(content) && content.length > 0;
    }
  },
  {
    name: 'Evaluate script with output',
    tool: 'puppeteer_evaluate',
    args: {
      script: 'return { title: document.title, url: window.location.href }',
      output_file: `${OUTPUT_DIR}/eval-result.json`
    },
    validate: async (file) => {
      const content = JSON.parse(await fs.readFile(file, 'utf-8'));
      return content.title !== undefined;
    }
  },
  {
    name: 'PDF generation with output',
    tool: 'puppeteer_pdf',
    args: {
      format: 'A4',
      output_file: `${OUTPUT_DIR}/page.pdf`
    },
    validate: async (file) => {
      const stats = await fs.stat(file);
      return stats.size > 1000; // PDF should be at least 1KB
    }
  }
];

// Run tests using the MCP server
async function runTests() {
  console.log('Starting Puppeteer MCP Server tests with file output...\n');
  
  await setupTestDir();
  
  // Start the MCP server
  const server = spawn('node', ['dist/index.js'], {
    cwd: process.cwd(),
    stdio: ['pipe', 'pipe', 'pipe']
  });

  // Give server time to start
  await new Promise(resolve => setTimeout(resolve, 2000));

  let passedTests = 0;
  let failedTests = 0;

  // Simulate MCP tool calls
  for (const test of testCases) {
    console.log(`\nTesting: ${test.name}`);
    console.log(`Tool: ${test.tool}`);
    console.log(`Output file: ${test.args.output_file}`);
    
    // Send tool call to server (in a real scenario, this would use MCP protocol)
    const toolCall = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: test.tool,
        arguments: test.args
      },
      id: Math.floor(Math.random() * 10000)
    };
    
    try {
      // Write to server stdin
      server.stdin.write(JSON.stringify(toolCall) + '\n');
      
      // Wait for operation to complete
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Check if output file was created
      try {
        await fs.access(test.args.output_file);
        
        // Validate file content
        if (await test.validate(test.args.output_file)) {
          console.log(`✓ Test passed: File created and validated`);
          passedTests++;
        } else {
          console.log(`✗ Test failed: File created but validation failed`);
          failedTests++;
        }
      } catch (error) {
        console.log(`✗ Test failed: Output file not created`);
        failedTests++;
      }
    } catch (error) {
      console.log(`✗ Test failed: ${error.message}`);
      failedTests++;
    }
  }

  // Cleanup
  server.kill();
  
  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('Test Summary:');
  console.log(`✓ Passed: ${passedTests}`);
  console.log(`✗ Failed: ${failedTests}`);
  console.log(`Total: ${testCases.length}`);
  console.log('='.repeat(50));
  
  // List created files
  console.log('\nCreated files:');
  try {
    const files = await fs.readdir(OUTPUT_DIR);
    for (const file of files) {
      const filePath = path.join(OUTPUT_DIR, file);
      const stats = await fs.stat(filePath);
      console.log(`  - ${file} (${stats.size} bytes)`);
    }
  } catch (error) {
    console.log('  Error listing files:', error.message);
  }
  
  process.exit(failedTests > 0 ? 1 : 0);
}

// Handle errors
process.on('unhandledRejection', (error) => {
  console.error('Unhandled error:', error);
  process.exit(1);
});

// Run the tests
runTests().catch(console.error);