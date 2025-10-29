#!/usr/bin/env python3
"""
Test MCP protocol communication with the HTTPie MCP Server.
This simulates what MCP Inspector or Claude Desktop would do.
"""

import json
import subprocess
import sys


def send_mcp_message(process, message):
    """Send a JSON-RPC message to the MCP server."""
    msg = json.dumps(message) + "\n"
    process.stdin.write(msg)
    process.stdin.flush()


def receive_mcp_message(process):
    """Receive a JSON-RPC message from the MCP server."""
    line = process.stdout.readline()
    if line:
        return json.loads(line)
    return None


def test_mcp_initialize():
    """Test MCP server initialization."""
    print("\n" + "="*70)
    print("TEST: MCP Protocol - Initialize")
    print("="*70)

    # Start the MCP server
    proc = subprocess.Popen(
        ["docker", "run", "-i", "--rm", "httpie-mcp-server:latest"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print(f"Sending: {json.dumps(init_request, indent=2)}")
        send_mcp_message(proc, init_request)

        # Wait for response (with timeout)
        import select
        import time

        timeout = 10
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if there's data to read
            if proc.stdout in select.select([proc.stdout], [], [], 1)[0]:
                response = receive_mcp_message(proc)
                if response:
                    print(f"\n✅ Received response:")
                    print(json.dumps(response, indent=2))
                    return True

        print("\n❌ Timeout waiting for response")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_tools_list():
    """Test listing available MCP tools."""
    print("\n" + "="*70)
    print("TEST: MCP Protocol - List Tools")
    print("="*70)

    # Start the MCP server
    proc = subprocess.Popen(
        ["docker", "run", "-i", "--rm", "httpie-mcp-server:latest"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        print(f"Sending: {json.dumps(tools_request, indent=2)}")
        send_mcp_message(proc, tools_request)

        # Wait for response
        import select
        import time

        timeout = 10
        start_time = time.time()

        while time.time() - start_time < timeout:
            if proc.stdout in select.select([proc.stdout], [], [], 1)[0]:
                response = receive_mcp_message(proc)
                if response:
                    print(f"\n✅ Received response:")
                    print(json.dumps(response, indent=2))

                    # Check if tools are listed
                    if 'result' in response and 'tools' in response['result']:
                        tools = response['result']['tools']
                        print(f"\n✅ Found {len(tools)} tools:")
                        for tool in tools:
                            print(f"  - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
                        return True

        print("\n❌ Timeout waiting for response")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        proc.terminate()
        proc.wait(timeout=5)


def main():
    """Run MCP protocol tests."""
    print("\n" + "#"*70)
    print("# HTTPie MCP Server - MCP Protocol Testing")
    print("#"*70)

    print("\nNote: These tests verify MCP protocol communication.")
    print("For interactive testing, use: mcp-inspector docker run -i --rm httpie-mcp-server:latest")

    # Run tests
    tests = [
        ("MCP Initialize", test_mcp_initialize),
        ("MCP List Tools", test_mcp_tools_list),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*70)
    print("MCP PROTOCOL TEST SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "-"*70)
    print(f"Total: {passed_count}/{total_count} tests passed")
    print("-"*70)

    if passed_count == total_count:
        print("\n✅ All MCP protocol tests passed!")
        print("\nTo test interactively with MCP Inspector:")
        print("  npx @modelcontextprotocol/inspector docker run -i --rm httpie-mcp-server:latest")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
