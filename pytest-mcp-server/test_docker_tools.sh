#!/bin/bash
# Docker Container Testing Script for Pytest MCP Server
# This script tests all 14 MCP tools through the Docker container

set -e  # Exit on error

BASE_URL="http://localhost:8000"
TIMEOUT=30

echo "🧪 Testing Pytest MCP Server Docker Container"
echo "=============================================="
echo "Server URL: $BASE_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Function to check if server is running
check_server() {
    echo "Checking if server is running..."
    if ! curl -f -s --max-time 5 $BASE_URL/health > /dev/null 2>&1; then
        echo "❌ Server is not running or not accessible at $BASE_URL"
        echo "   Please start the Docker container first:"
        echo "   docker-compose up pytest-mcp-server"
        echo "   or"
        echo "   docker run -p 8000:8000 pytest-mcp-server:latest"
        exit 1
    fi
    echo "✅ Server is running and accessible"
    echo ""
}

# Function to test a tool
test_tool() {
    local tool_name="$1"
    local json_data="$2"
    local description="$3"

    echo "Testing: $tool_name - $description"

    response=$(curl -s --max-time $TIMEOUT -X POST "$BASE_URL/tools/$tool_name" \
        -H "Content-Type: application/json" \
        -d "$json_data" 2>/dev/null)

    if [ $? -eq 0 ]; then
        success=$(echo "$response" | jq -r '.success // false' 2>/dev/null)
        if [ "$success" = "true" ]; then
            echo "✅ $tool_name: SUCCESS"
        else
            echo "❌ $tool_name: FAILED"
            echo "   Response: $response" | head -200
        fi
    else
        echo "❌ $tool_name: NETWORK ERROR"
    fi
    echo ""
}

# Check server availability
check_server

# Test 1: Health check
echo "1. Testing server health endpoint..."
health_response=$(curl -s --max-time 5 $BASE_URL/health)
echo "Health response: $health_response"
echo ""

# Test 2: List available tools
echo "2. Listing available MCP tools..."
tools_response=$(curl -s --max-time 5 $BASE_URL/tools)
if command -v jq >/dev/null 2>&1; then
    echo "Available tools:"
    echo "$tools_response" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "$tools_response"
else
    echo "$tools_response"
fi
echo ""

echo "3. Testing all MCP tools..."
echo "=========================="

# Test 3: record_session_start
test_tool "record_session_start" '{
  "environment": {
    "os": "Linux",
    "python_version": "3.12.0",
    "pytest_version": "8.0.0",
    "platform": "Linux-x86_64-docker",
    "architecture": "x86_64"
  }
}' "Record test session start"

# Test 4: record_test_outcome (passing test)
test_tool "record_test_outcome" '{
  "nodeid": "tests/test_example.py::test_addition",
  "outcome": "passed",
  "duration": 0.123,
  "markers": ["unit", "fast"],
  "keywords": ["test", "addition"],
  "file_path": "tests/test_example.py",
  "line_number": 10
}' "Record passing test outcome"

# Test 5: record_test_outcome (failing test)
test_tool "record_test_outcome" '{
  "nodeid": "tests/test_example.py::test_assertion_failure",
  "outcome": "failed",
  "duration": 0.456,
  "error": "AssertionError: assert 1 == 2",
  "traceback": "Traceback (most recent call last):\\n  File \"tests/test_example.py\", line 15\\n    assert 1 == 2\\nAssertionError: assert 1 == 2",
  "markers": ["unit"],
  "keywords": ["test", "assertion"],
  "file_path": "tests/test_example.py",
  "line_number": 15
}' "Record failing test outcome"

# Test 6: record_session_finish
test_tool "record_session_finish" '{
  "summary": {
    "total_tests": 2,
    "passed": 1,
    "failed": 1,
    "skipped": 0,
    "errors": 0,
    "xfailed": 0,
    "xpassed": 0,
    "exitstatus": 1,
    "duration": 0.579
  }
}' "Record session completion"

# Test 7: get_session_status
test_tool "get_session_status" '{}' "Get current session status"

# Test 8: get_failure_analysis
test_tool "get_failure_analysis" '{
  "test_nodeid": "tests/test_example.py::test_assertion_failure"
}' "Get AI failure analysis"

# Test 9: find_similar_failures
test_tool "find_similar_failures" '{
  "error_pattern": "AssertionError",
  "limit": 5
}' "Find similar failures by error pattern"

# Test 10: track_debugging_progress
test_tool "track_debugging_progress" '{
  "failure_id": "failure-demo-123",
  "action": "add_step",
  "step_description": "Reviewed the assertion logic and expectations"
}' "Track debugging progress"

# Test 11: generate_debugging_prompt
test_tool "generate_debugging_prompt" '{
  "test_nodeid": "tests/test_example.py::test_assertion_failure"
}' "Generate AI debugging prompt"

# Test 12: get_test_statistics
test_tool "get_test_statistics" '{}' "Get comprehensive test statistics"

# NEW TEST GENERATION TOOLS

# Test 13: analyze_code_for_testing
test_tool "analyze_code_for_testing" '{
  "source_code": "def add(a: int, b: int) -> int:\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n\ndef divide(a: float, b: float) -> float:\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b"
}' "Analyze code for testing opportunities"

# Test 14: generate_unit_tests
test_tool "generate_unit_tests" '{
  "source_code": "def factorial(n: int) -> int:\n    if n < 0:\n        raise ValueError(\"Factorial not defined for negative numbers\")\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
  "function_name": "factorial",
  "framework": "pytest",
  "include_mocks": true
}' "Generate unit tests for function"

# Test 15: suggest_test_cases
test_tool "suggest_test_cases" '{
  "source_code": "def validate_password(password: str) -> bool:\n    if len(password) < 8:\n        return False\n    if not any(c.isupper() for c in password):\n        return False\n    if not any(c.isdigit() for c in password):\n        return False\n    return True",
  "function_name": "validate_password"
}' "Suggest test cases for function"

# Test 16: generate_test_file
test_tool "generate_test_file" '{
  "source_code": "class Calculator:\n    def add(self, a, b):\n        return a + b\n    \n    def subtract(self, a, b):\n        return a - b",
  "framework": "pytest",
  "include_mocks": false
}' "Generate complete test file"

# Test 17: analyze_test_coverage
test_tool "analyze_test_coverage" '{
  "source_dir": "/app/src",
  "test_dir": "/app/tests"
}' "Analyze test coverage and recommendations"

echo "=============================================="
echo "🎉 Docker container testing completed!"
echo ""
echo "Summary:"
echo "- Tested all 14 MCP tools (9 analysis + 5 test generation)"
echo "- Tested health endpoint"
echo "- Tested tools listing"
echo ""
echo "Next steps:"
echo "1. Use MCP Inspector at http://localhost:5173"
echo "2. Connect to server: http://localhost:8000"
echo "3. Test tools interactively with the JSON examples from README.md"
echo ""
echo "For more detailed testing, see the complete examples in README.md"