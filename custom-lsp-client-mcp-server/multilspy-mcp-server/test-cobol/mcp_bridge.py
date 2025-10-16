#!/usr/bin/env python3
"""
MCP Bridge Tool - Direct communication with MCP servers
This tool provides a bridge to communicate directly with MCP servers using proper protocol
"""
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

class MCPBridge:
    def __init__(self, server_config: Dict[str, Any]):
        self.server_config = server_config
        self.server_name = server_config.get('name', 'unknown')

    def _send_mcp_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send MCP protocol request to server"""
        if params is None:
            params = {}

        # Build Docker command - use absolute path
        docker_cmd = [
            'docker', 'run', '--rm', '-i',
            '--volume', '/home/santosh/lsp-server/multilspy-mcp-server/test-cobol:/workspace',
            self.server_config['image']
        ]

        # Prepare MCP messages with complete handshake like MCP Inspector
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "prompts": {},
                    "resources": {},
                    "tools": {}
                },
                "clientInfo": {"name": "claude-mcp-bridge", "version": "1.0"}
            }
        }

        # Send initialized notification (critical for MCP protocol)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }

        # Only send third message if method is not initialize
        if method != "initialize":
            request_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params
            }
        else:
            request_msg = None

        # Send messages with proper timing like MCP Inspector
        input_data = json.dumps(init_msg) + '\n'
        input_data += json.dumps(initialized_notification) + '\n'
        if request_msg:
            input_data += json.dumps(request_msg) + '\n'

        try:
            result = subprocess.run(
                docker_cmd,
                input=input_data,
                text=True,
                capture_output=True,
                timeout=30
            )

            # Debug output
            print(f"Docker command: {' '.join(docker_cmd)}", file=sys.stderr)
            print(f"Input: {input_data}", file=sys.stderr)
            print(f"Stdout: {result.stdout}", file=sys.stderr)
            print(f"Stderr: {result.stderr}", file=sys.stderr)
            print(f"Return code: {result.returncode}", file=sys.stderr)

            # Parse responses
            lines = result.stdout.strip().split('\n')
            responses = []
            for line in lines:
                if line.startswith('{'):
                    try:
                        responses.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            return {
                'responses': responses,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {'error': 'Request timeout', 'responses': []}
        except Exception as e:
            return {'error': str(e), 'responses': []}

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from the MCP server"""
        result = self._send_mcp_request("tools/list")

        for response in result.get('responses', []):
            if response.get('id') == 2 and 'result' in response:
                return response['result'].get('tools', [])

        return []

    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources from the MCP server"""
        result = self._send_mcp_request("resources/list")

        for response in result.get('responses', []):
            if response.get('id') == 2 and 'result' in response:
                return response['result'].get('resources', [])

        return []

    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool on the MCP server"""
        if arguments is None:
            arguments = {}

        params = {
            "name": tool_name,
            "arguments": arguments
        }

        result = self._send_mcp_request("tools/call", params)

        for response in result.get('responses', []):
            if response.get('id') == 2:
                return response

        return {'error': 'No valid response received'}

    def get_server_info(self) -> Dict[str, Any]:
        """Get basic server information"""
        result = self._send_mcp_request("initialize")

        for response in result.get('responses', []):
            if response.get('id') == 1 and 'result' in response:
                return response['result']

        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python mcp_bridge.py <server_name> [command] [args...]")
        print("Commands: list-tools, list-resources, call-tool, server-info")
        sys.exit(1)

    server_name = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "server-info"

    # Server configurations
    servers = {
        'multilspy': {
            'name': 'multilspy-mcp-server',
            'image': 'multilspy-mcp-server:superbol-official'
        },
        'ctags': {
            'name': 'ctags-mcp',
            'image': 'ctags-mcp:test'
        }
    }

    if server_name not in servers:
        print(f"Unknown server: {server_name}")
        print(f"Available servers: {', '.join(servers.keys())}")
        sys.exit(1)

    bridge = MCPBridge(servers[server_name])

    if command == "list-tools":
        tools = bridge.list_tools()
        print(json.dumps(tools, indent=2))
    elif command == "list-resources":
        resources = bridge.list_resources()
        print(json.dumps(resources, indent=2))
    elif command == "server-info":
        info = bridge.get_server_info()
        print(json.dumps(info, indent=2))
    elif command == "call-tool" and len(sys.argv) > 3:
        tool_name = sys.argv[3]
        args = {}
        if len(sys.argv) > 4:
            try:
                args = json.loads(sys.argv[4])
            except json.JSONDecodeError:
                print("Invalid JSON arguments")
                sys.exit(1)

        result = bridge.call_tool(tool_name, args)
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()