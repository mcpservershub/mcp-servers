#!/usr/bin/env python3
"""Integration test for Hurl MCP Server."""

import json
import subprocess
import time


def test_docker_mcp_server():
    """Test the MCP server running in Docker."""
    print("Starting MCP server integration test...")
    
    # Start the container
    proc = subprocess.Popen(
        ["docker", "run", "-i", "--rm", "-v", f"{subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip()}/examples:/app/examples:ro", "hurl-mcp-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "0.1.0"
                }
            },
            "id": 1
        }
        
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read initialization response
        init_response = proc.stdout.readline()
        print(f"Init response: {init_response.strip()}")
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        proc.stdin.write(json.dumps(initialized) + "\n")
        proc.stdin.flush()
        
        # Now list tools
        list_tools = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        proc.stdin.write(json.dumps(list_tools) + "\n")
        proc.stdin.flush()
        
        # Read tools response
        tools_response = proc.stdout.readline()
        print(f"Tools response: {tools_response.strip()}")
        
        # Parse and display tools
        tools_data = json.loads(tools_response)
        if "result" in tools_data and "tools" in tools_data["result"]:
            print(f"\nFound {len(tools_data['result']['tools'])} tools:")
            for tool in tools_data["result"]["tools"]:
                print(f"  - {tool['name']}")
        
        # Test running a simple hurl file
        run_hurl = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "validate_hurl",
                "arguments": {
                    "hurl_content": "GET https://example.com\\nHTTP 200"
                }
            },
            "id": 3
        }
        proc.stdin.write(json.dumps(run_hurl) + "\n")
        proc.stdin.flush()
        
        # Read response
        validate_response = proc.stdout.readline()
        print(f"\nValidate response: {validate_response.strip()}")
        
    finally:
        # Cleanup
        proc.terminate()
        proc.wait()
    
    print("\nIntegration test completed!")


if __name__ == "__main__":
    test_docker_mcp_server()