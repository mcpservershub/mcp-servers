#!/usr/bin/env python3

import json
import subprocess
import sys
import time
import threading
import os

def test_mcp_server():
    """Test if the MCP server responds to basic protocol messages"""
    
    print("Testing PostgreSQL MCP Server locally...")
    
    # First check if we have the built files
    if not os.path.exists('dist/index.js'):
        print("❌ No dist/index.js found. Please build the project first:")
        print("   npm install && npm run build")
        return False
    
    # Start the MCP server
    process = subprocess.Popen(
        ['node', 'dist/index.js'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    def read_stderr():
        """Read stderr in a separate thread"""
        for line in process.stderr:
            print(f"Server error: {line.strip()}")
    
    # Start stderr reader thread
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()
    
    try:
        # Give server time to start
        time.sleep(0.5)
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                },
                "capabilities": {}
            },
            "id": 1
        }
        
        print("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"Initialize response: {json.dumps(response, indent=2)}")
            
            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            
            print("\nSending tools/list request...")
            process.stdin.write(json.dumps(tools_request) + '\n')
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                print(f"Tools response: {json.dumps(response, indent=2)}")
                
                if 'result' in response and 'tools' in response['result']:
                    print("\n✅ MCP Server is working! Available tools:")
                    for tool in response['result']['tools']:
                        print(f"  - {tool['name']}: {tool['description']}")
                    return True
        
        print("❌ No valid response from server")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        process.terminate()
        process.wait(timeout=2)

if __name__ == "__main__":
    # Change to postgres-mcp directory if needed
    if os.path.basename(os.getcwd()) != 'postgres-mcp':
        postgres_dir = os.path.join(os.getcwd(), 'postgres-mcp')
        if os.path.exists(postgres_dir):
            os.chdir(postgres_dir)
    
    success = test_mcp_server()
    sys.exit(0 if success else 1)