#!/usr/bin/env python3
"""
Comprehensive test script for HTTPie MCP Server tools.
Tests all three MCP tools with various scenarios.
"""

import json
import sys


def test_http_request_simple_get():
    """Test 1: Simple GET request to httpbin.org"""
    print("\n" + "="*70)
    print("TEST 1: http_request - Simple GET")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(url="https://httpbin.org/get")

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        body = result.get('body', '')
        if body and len(body) < 500:
            print(f"Response body preview: {body[:200]}...")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_post_json():
    """Test 2: POST request with JSON data"""
    print("\n" + "="*70)
    print("TEST 2: http_request - POST with JSON data")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/post",
        method="POST",
        json_data={
            "name": "HTTPie MCP Test",
            "version": "0.1.0",
            "active": True,
            "count": 42
        }
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_with_headers():
    """Test 3: GET request with custom headers"""
    print("\n" + "="*70)
    print("TEST 3: http_request - Custom headers")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/headers",
        method="GET",
        headers={
            "X-Custom-Header": "HTTPie-MCP-Server",
            "X-Test-ID": "12345",
            "User-Agent": "HTTPie-MCP/0.1.0"
        }
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        body = result.get('body', '')
        if 'X-Custom-Header' in body:
            print("✓ Custom header found in response")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_query_params():
    """Test 4: GET request with query parameters"""
    print("\n" + "="*70)
    print("TEST 4: http_request - Query parameters")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/get",
        method="GET",
        query_params={
            "page": "1",
            "limit": "10",
            "sort": "name",
            "filter": "active"
        }
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        body = result.get('body', '')
        if 'page' in body and 'limit' in body:
            print("✓ Query parameters found in response")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_basic_auth():
    """Test 5: GET request with basic authentication"""
    print("\n" + "="*70)
    print("TEST 5: http_request - Basic authentication")
    print("="*70)

    from httpie_mcp.server import http_request

    # httpbin.org/basic-auth/user/passwd expects user:passwd
    result = http_request(
        url="https://httpbin.org/basic-auth/testuser/testpass",
        method="GET",
        auth="testuser:testpass",
        auth_type="basic"
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success'] and result.get('status_code') == 200:
        print("✅ TEST PASSED")
        body = result.get('body', '')
        if 'authenticated' in body:
            print("✓ Authentication successful")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success'] and result.get('status_code') == 200


def test_http_request_form_data():
    """Test 6: POST request with form data"""
    print("\n" + "="*70)
    print("TEST 6: http_request - Form data")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/post",
        method="POST",
        form_data={
            "username": "testuser",
            "email": "test@example.com",
            "subscribe": "yes"
        }
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_timeout():
    """Test 7: Request with timeout"""
    print("\n" + "="*70)
    print("TEST 7: http_request - Timeout configuration")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/delay/2",
        method="GET",
        timeout=5  # Should complete in time
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_request_verbose():
    """Test 8: Request with verbose output"""
    print("\n" + "="*70)
    print("TEST 8: http_request - Verbose mode")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/get",
        method="GET",
        verbose=True,
        output_headers=True,
        output_body=True
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        if result.get('headers'):
            print("✓ Headers included in output")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_download():
    """Test 9: File download"""
    print("\n" + "="*70)
    print("TEST 9: http_download - Download file")
    print("="*70)

    from httpie_mcp.server import http_download

    # Download a small JSON file from httpbin
    result = http_download(
        url="https://httpbin.org/json",
        output_file="/tmp/test_download.json"
    )

    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        # Check if file was created
        import os
        if os.path.exists('/tmp/test_download.json'):
            print("✓ File downloaded successfully")
            file_size = os.path.getsize('/tmp/test_download.json')
            print(f"✓ File size: {file_size} bytes")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def test_http_session_request():
    """Test 10: Session-based requests"""
    print("\n" + "="*70)
    print("TEST 10: http_session_request - Session persistence")
    print("="*70)

    from httpie_mcp.server import http_session_request

    # First request: create session
    print("\nStep 1: Creating session...")
    result1 = http_session_request(
        session_name="test-session",
        url="https://httpbin.org/cookies/set/sessionid/test123",
        method="GET",
        follow_redirects=True
    )

    print(f"Session creation - Success: {result1['success']}")
    print(f"Command: {result1['command']}")

    # Second request: use same session
    print("\nStep 2: Reusing session...")
    result2 = http_session_request(
        session_name="test-session",
        url="https://httpbin.org/cookies",
        method="GET"
    )

    print(f"Session reuse - Success: {result2['success']}")
    print(f"Command: {result2['command']}")

    if result1['success'] and result2['success']:
        print("✅ TEST PASSED")
        body2 = result2.get('body', '')
        if 'sessionid' in body2:
            print("✓ Session cookie persisted across requests")
    else:
        print(f"❌ TEST FAILED")

    return result1['success'] and result2['success']


def test_http_request_offline_mode():
    """Test 11: Offline mode (dry-run)"""
    print("\n" + "="*70)
    print("TEST 11: http_request - Offline mode (dry-run)")
    print("="*70)

    from httpie_mcp.server import http_request

    result = http_request(
        url="https://httpbin.org/post",
        method="POST",
        json_data={"test": "data"},
        headers={"X-Test": "Value"},
        offline=True  # Don't actually send the request
    )

    print(f"Success: {result['success']}")
    print(f"Command: {result['command']}")

    if result['success']:
        print("✅ TEST PASSED")
        print("✓ Request built without sending")
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")

    return result['success']


def run_all_tests():
    """Run all tests and generate summary"""
    print("\n" + "#"*70)
    print("# HTTPie MCP Server - Comprehensive Tool Testing")
    print("#"*70)

    tests = [
        ("Simple GET request", test_http_request_simple_get),
        ("POST with JSON data", test_http_request_post_json),
        ("Custom headers", test_http_request_with_headers),
        ("Query parameters", test_http_request_query_params),
        ("Basic authentication", test_http_request_basic_auth),
        ("Form data", test_http_request_form_data),
        ("Timeout configuration", test_http_request_timeout),
        ("Verbose mode", test_http_request_verbose),
        ("File download", test_http_download),
        ("Session persistence", test_http_session_request),
        ("Offline mode", test_http_request_offline_mode),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False, str(e)))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    for test_name, passed, error in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if error:
            print(f"  Error: {error}")

    print("\n" + "-"*70)
    print(f"Total: {passed_count}/{total_count} tests passed ({passed_count*100//total_count}%)")
    print("-"*70)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
