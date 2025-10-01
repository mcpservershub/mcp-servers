import { spawn } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testMCPServer() {
  console.log('Testing MCP Server...');
  
  const serverPath = join(__dirname, 'dist', 'index.js');
  const server = spawn('node', [serverPath]);
  
  let response = '';
  
  server.stdout.on('data', (data) => {
    response += data.toString();
    console.log('Server output:', data.toString());
  });
  
  server.stderr.on('data', (data) => {
    console.log('Server stderr:', data.toString());
  });
  
  // Send a test message to the server
  setTimeout(() => {
    const testMessage = {
      jsonrpc: "2.0",
      method: "tools/list",
      id: 1
    };
    
    console.log('Sending test message:', JSON.stringify(testMessage));
    server.stdin.write(JSON.stringify(testMessage) + '\n');
    
    setTimeout(() => {
      server.kill();
      console.log('Test completed');
    }, 2000);
  }, 1000);
}

testMCPServer().catch(console.error);