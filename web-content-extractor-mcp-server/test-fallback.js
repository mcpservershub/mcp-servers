import { spawn } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testMCPServer() {
  console.log('Testing MCP Server with get_content tool...');
  
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
  
  // First test: list tools
  setTimeout(() => {
    const listToolsMessage = {
      jsonrpc: "2.0",
      method: "tools/list",
      id: 1
    };
    
    console.log('Sending tools/list message...');
    server.stdin.write(JSON.stringify(listToolsMessage) + '\n');
    
    // Second test: call get_content tool
    setTimeout(() => {
      const getContentMessage = {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
          name: "get_content",
          arguments: {
            url: "https://google.com",
            output_file_path: "./output/test.json"
          }
        },
        id: 2
      };
      
      console.log('Sending get_content call...');
      server.stdin.write(JSON.stringify(getContentMessage) + '\n');
      
      setTimeout(() => {
        server.kill();
        console.log('Test completed');
      }, 5000);
    }, 2000);
  }, 1000);
}

testMCPServer().catch(console.error);