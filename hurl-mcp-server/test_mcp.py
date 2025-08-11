#!/usr/bin/env python3
"""Simple test script to verify MCP server functionality."""

import json
import subprocess
import sys


def test_mcp_server():
    """Test the MCP server with a simple request."""
    # Test tool listing request
    list_tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    # Run the server and send request
    process = subprocess.Popen(
        [sys.executable, "-m", "hurl_mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request
    process.stdin.write(json.dumps(list_tools_request) + "\n")
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline()
    
    # Terminate process
    process.terminate()
    
    try:
        response = json.loads(response_line)
        print("MCP Server Response:")
        print(json.dumps(response, indent=2))
        
        # Check if we got tools
        if "result" in response and "tools" in response["result"]:
            print(f"\nFound {len(response['result']['tools'])} tools:")
            for tool in response["result"]["tools"]:
                print(f"  - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
            return True
        else:
            print("ERROR: No tools found in response")
            return False
            
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse response: {e}")
        print(f"Response line: {response_line}")
        return False


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)