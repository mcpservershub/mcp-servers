# MCP Tools Usage Guide - STDIO Mode

Complete guide for using all 14 MCP tools with the Pytest MCP Server in STDIO mode.

## Table of Contents

- [Getting Started](#getting-started)
- [MCP Protocol Basics](#mcp-protocol-basics)
- [Tool Categories](#tool-categories)
- [Test Result Analysis Tools (9 tools)](#test-result-analysis-tools)
- [Test Generation Tools (5 tools)](#test-generation-tools)
- [Complete Examples](#complete-examples)

## Getting Started

### Starting the MCP Server

**Local Installation:**
```bash
pytest-mcp-server serve
```

**Docker Container:**
```bash
docker run -i pytest-mcp-server:latest
```

**Docker Compose:**
```bash
docker-compose up pytest-mcp-server
```

### MCP Protocol Communication

The server uses **STDIO (Standard Input/Output)** for communication via the Model Context Protocol (MCP).

**Basic Request Format:**
```json
{"jsonrpc":"2.0","id":REQUEST_ID,"method":"METHOD_NAME","params":PARAMETERS}
```

**Basic Response Format:**
```json
{"jsonrpc":"2.0","id":REQUEST_ID,"result":RESULT_DATA}
```

## MCP Protocol Basics

### 1. Initialize Connection

**Always start with initialization:**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"your-client","version":"1.0"}}}' | \
docker run -i pytest-mcp-server:latest
```

### 2. Send Initialized Notification

**After initialization, send notification:**
```json
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

### 3. List Available Tools

**Get all 14 tools:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```

## Tool Categories

### Test Result Analysis Tools (9 tools)
1. `record_session_start` - Initialize test session
2. `record_test_outcome` - Record individual test results
3. `record_session_finish` - Complete test session
4. `get_session_status` - Get session information
5. `get_failure_analysis` - AI-powered failure analysis
6. `find_similar_failures` - Find similar test failures
7. `track_debugging_progress` - Track debugging workflow
8. `generate_debugging_prompt` - Generate AI debugging context
9. `get_test_statistics` - Get comprehensive statistics

### Test Generation Tools (5 tools)
10. `analyze_code_for_testing` - Analyze code for testing opportunities
11. `generate_unit_tests` - Generate unit tests for code
12. `suggest_test_cases` - Suggest test cases for functions
13. `generate_test_file` - Generate complete test files
14. `analyze_test_coverage` - Analyze test coverage

---

## Test Result Analysis Tools

### 1. record_session_start

**Purpose:** Initialize a pytest session with environment information.

**Required Arguments:**
- `environment` (object): Environment information
  - `os` (string): Operating system name
  - `python_version` (string): Python version

**Optional Arguments:**
- `environment.pytest_version` (string): Pytest version
- `environment.platform` (string): Platform information
- `environment.architecture` (string): System architecture

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_session_start","arguments":{"environment":{"os":"Linux","python_version":"3.12.0","pytest_version":"8.0.0","platform":"Linux-x86_64","architecture":"x86_64"}}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-abc123",
  "start_time": "2025-10-03T12:00:00",
  "message": "Test session started successfully"
}
```

---

### 2. record_test_outcome

**Purpose:** Record the outcome of an individual test case.

**Required Arguments:**
- `nodeid` (string): Unique test node identifier (e.g., "tests/test_example.py::test_add")
- `outcome` (string): Test outcome - one of: `passed`, `failed`, `skipped`, `error`, `xfail`, `xpass`
- `duration` (number): Test duration in seconds

**Optional Arguments:**
- `error` (string): Error message if test failed
- `traceback` (string): Full traceback if available
- `stdout` (string): Captured stdout
- `stderr` (string): Captured stderr
- `markers` (array): Test markers
- `keywords` (array): Test keywords
- `file_path` (string): Test file path
- `line_number` (integer): Test line number

**Example - Passing Test:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_test_outcome","arguments":{"nodeid":"tests/test_math.py::test_addition","outcome":"passed","duration":0.123,"markers":["unit","fast"],"file_path":"tests/test_math.py","line_number":10}}}
EOF
```

**Example - Failing Test:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_test_outcome","arguments":{"nodeid":"tests/test_math.py::test_division","outcome":"failed","duration":0.045,"error":"ZeroDivisionError: division by zero","traceback":"Traceback (most recent call last):\\n  File 'test_math.py', line 15\\n    result = divide(10, 0)\\nZeroDivisionError: division by zero","file_path":"tests/test_math.py","line_number":15}}}
EOF
```

---

### 3. record_session_finish

**Purpose:** Record the completion of a pytest session.

**Required Arguments:**
- `summary` (object): Session summary
  - `total_tests` (integer): Total number of tests
  - `passed` (integer): Number of passed tests
  - `failed` (integer): Number of failed tests
  - `skipped` (integer): Number of skipped tests
  - `exitstatus` (integer): Exit status code
  - `duration` (number): Total session duration

**Optional Arguments:**
- `summary.errors` (integer): Number of error tests
- `summary.xfailed` (integer): Number of expected failures
- `summary.xpassed` (integer): Number of unexpected passes

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_session_finish","arguments":{"summary":{"total_tests":10,"passed":8,"failed":2,"skipped":0,"errors":0,"xfailed":0,"xpassed":0,"exitstatus":1,"duration":1.234}}}}
EOF
```

---

### 4. get_session_status

**Purpose:** Get the status of a test session.

**Optional Arguments:**
- `session_id` (string): Session identifier (uses current session if not provided)

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_session_status","arguments":{}}}
EOF
```

---

### 5. get_failure_analysis

**Purpose:** Get AI-powered failure analysis for a specific test.

**Required Arguments:**
- `test_nodeid` (string): Test node identifier

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_failure_analysis","arguments":{"test_nodeid":"tests/test_math.py::test_division"}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "failure_category": "runtime_error",
  "possible_causes": ["Division by zero", "Invalid input validation"],
  "suggested_fixes": ["Add zero check before division", "Validate inputs"],
  "confidence": 0.85
}
```

---

### 6. find_similar_failures

**Purpose:** Find similar test failures across sessions.

**Optional Arguments:**
- `error_pattern` (string): Error pattern to search for
- `test_pattern` (string): Test name pattern to search for
- `limit` (integer): Maximum number of results (default: 10)

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_similar_failures","arguments":{"error_pattern":"ZeroDivisionError","limit":5}}}
EOF
```

---

### 7. track_debugging_progress

**Purpose:** Track debugging progress for a specific failure.

**Required Arguments:**
- `failure_id` (string): Failure identifier
- `action` (string): Action to take - one of: `add_step`, `add_hypothesis`, `update_status`, `add_notes`

**Optional Arguments:**
- `step_description` (string): Description of debugging step taken
- `hypothesis` (string): New hypothesis to add
- `resolution_status` (string): New resolution status
- `notes` (string): Additional notes

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"track_debugging_progress","arguments":{"failure_id":"failure-123","action":"add_step","step_description":"Checked input validation logic","hypothesis":"Missing null check","resolution_status":"investigating"}}}
EOF
```

---

### 8. generate_debugging_prompt

**Purpose:** Generate a targeted debugging prompt for LLMs.

**Required Arguments:**
- `test_nodeid` (string): Test node identifier

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_debugging_prompt","arguments":{"test_nodeid":"tests/test_math.py::test_division"}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "prompt": "Analyze this test failure: ZeroDivisionError in test_division...",
  "context": {...},
  "suggestions": [...]
}
```

---

### 9. get_test_statistics

**Purpose:** Get overall test statistics and metrics.

**No Arguments Required**

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_test_statistics","arguments":{}}}
EOF
```

---

## Test Generation Tools

### 10. analyze_code_for_testing

**Purpose:** Analyze source code to identify testing opportunities.

**Optional Arguments (at least one required):**
- `file_path` (string): Path to Python source file
- `source_code` (string): Python source code as string

**Example with source_code:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def calculate_total(items):\\n    if not items:\\n        return 0\\n    return sum(item['price'] * item['quantity'] for item in items)"}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "file_path": "inline_code",
  "functions": [
    {
      "name": "calculate_total",
      "signature": "calculate_total(items)",
      "complexity": 3,
      "is_async": false
    }
  ],
  "classes": [],
  "complexity_score": 3,
  "recommendations": [
    "Function 'calculate_total' has moderate complexity - consider edge case tests",
    "Test with empty list, single item, multiple items"
  ],
  "estimated_tests": 5
}
```

---

### 11. generate_unit_tests

**Purpose:** Generate unit tests for Python code.

**Optional Arguments (at least source_code or file_path required):**
- `source_code` (string): Python source code to generate tests for
- `file_path` (string): Path to Python source file
- `function_name` (string): Specific function name to test
- `class_name` (string): Specific class name to test
- `framework` (string): Test framework - `pytest` (default) or `unittest`
- `include_mocks` (boolean): Include mock-based tests (default: true)

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_unit_tests","arguments":{"source_code":"def validate_email(email: str) -> bool:\\n    if not email or '@' not in email:\\n        return False\\n    return True","function_name":"validate_email","framework":"pytest","include_mocks":false}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "tests": [
    {
      "name": "test_validate_email_valid",
      "description": "Test with valid email",
      "test_code": "def test_validate_email_valid():\\n    assert validate_email('user@example.com') == True",
      "test_type": "happy_path",
      "priority": "high"
    },
    {
      "name": "test_validate_email_empty",
      "description": "Test with empty email",
      "test_code": "def test_validate_email_empty():\\n    assert validate_email('') == False",
      "test_type": "edge_case",
      "priority": "high"
    }
  ]
}
```

---

### 12. suggest_test_cases

**Purpose:** Suggest test cases for a specific function.

**Required Arguments:**
- `function_name` (string): Name of the function to suggest tests for

**Optional Arguments:**
- `source_code` (string): Python source code containing the function
- `file_path` (string): Path to Python file containing the function

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"suggest_test_cases","arguments":{"function_name":"process_payment","source_code":"def process_payment(amount: float, currency: str) -> dict:\\n    if amount <= 0:\\n        raise ValueError('Invalid amount')\\n    return {'status': 'success', 'amount': amount, 'currency': currency}"}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "name": "test_process_payment_valid",
      "description": "Test with valid amount and currency",
      "test_type": "happy_path",
      "priority": "high"
    },
    {
      "name": "test_process_payment_zero_amount",
      "description": "Test with zero amount raises ValueError",
      "test_type": "error_case",
      "priority": "high"
    },
    {
      "name": "test_process_payment_negative_amount",
      "description": "Test with negative amount raises ValueError",
      "test_type": "error_case",
      "priority": "high"
    }
  ]
}
```

---

### 13. generate_test_file

**Purpose:** Generate a complete test file for a Python module.

**Required Arguments:**
- `file_path` (string): Path to Python source file

**Optional Arguments:**
- `output_path` (string): Path for generated test file
- `framework` (string): Test framework to use - `pytest` (default) or `unittest`
- `include_integration` (boolean): Include integration tests (default: false)

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_test_file","arguments":{"file_path":"/app/src/calculator.py","framework":"pytest","include_integration":false}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "test_file": {
    "file_name": "test_calculator.py",
    "source_file": "/app/src/calculator.py",
    "framework": "pytest",
    "imports": [
      "import pytest",
      "from calculator import Calculator"
    ],
    "test_code": "# Generated test file content...",
    "estimated_coverage": 85.0,
    "test_count": 12,
    "estimated_runtime": 0.5
  }
}
```

---

### 14. analyze_test_coverage

**Purpose:** Analyze test coverage and provide improvement recommendations.

**Required Arguments:**
- `source_dir` (string): Directory containing source code

**Optional Arguments:**
- `test_dir` (string): Directory containing tests
- `coverage_file` (string): Path to existing coverage report file

**Example:**
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_test_coverage","arguments":{"source_dir":"/app/src","test_dir":"/app/tests"}}}
EOF
```

**Response:**
```json
{
  "success": true,
  "coverage_reports": [
    {
      "file_path": "/app/src/calculator.py",
      "total_lines": 100,
      "covered_lines": 85,
      "coverage_percentage": 85.0,
      "missing_lines": [15, 23, 35, 42, 67],
      "uncovered_functions": ["error_handler", "validate_input"]
    }
  ],
  "improvement_plan": {
    "current_coverage": 85.0,
    "target_coverage": 90.0,
    "estimated_tests_needed": 5,
    "priority_actions": [
      {
        "action": "Add tests for error_handler function",
        "impact": "Improve coverage by ~3%",
        "tests": 2
      }
    ]
  }
}
```

---

## Complete Examples

### Example 1: Full Test Session Workflow

```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_session_start","arguments":{"environment":{"os":"Linux","python_version":"3.12.0","pytest_version":"8.0.0"}}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"record_test_outcome","arguments":{"nodeid":"tests/test_calc.py::test_add","outcome":"passed","duration":0.1}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"record_test_outcome","arguments":{"nodeid":"tests/test_calc.py::test_divide","outcome":"failed","duration":0.05,"error":"ZeroDivisionError"}}}
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"record_session_finish","arguments":{"summary":{"total_tests":2,"passed":1,"failed":1,"skipped":0,"exitstatus":1,"duration":0.15}}}}
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"get_test_statistics","arguments":{}}}
EOF
```

### Example 2: Test Generation Workflow

```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def multiply(a, b):\\n    return a * b"}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"generate_unit_tests","arguments":{"source_code":"def multiply(a, b):\\n    return a * b","framework":"pytest"}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"suggest_test_cases","arguments":{"function_name":"multiply","source_code":"def multiply(a, b):\\n    return a * b"}}}
EOF
```

### Example 3: Using Shell Script

Create a file `test_mcp.sh`:

```bash
#!/bin/bash

# Test MCP Server with multiple tools
docker run -i pytest-mcp-server:latest 2>/dev/null <<REQUESTS | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def add(a, b): return a + b"}}}
REQUESTS
```

Make it executable and run:
```bash
chmod +x test_mcp.sh
./test_mcp.sh
```

### Example 4: Pretty Print Responses

Using `jq` for formatted JSON output:

```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | jq .
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def add(a, b): return a + b"}}}
EOF
```

---

## Troubleshooting

### Issue: Empty or No Response

**Problem:** Not receiving JSON responses

**Solution:** Make sure to:
1. Send the `initialize` request first
2. Send the `notifications/initialized` notification
3. Redirect stderr to /dev/null: `2>/dev/null`

### Issue: Invalid Request Parameters Error

**Problem:** Receiving `-32602` error code

**Solution:** Check that:
1. You've sent the initialized notification
2. Arguments match the required format
3. Required arguments are provided

### Issue: Tool Not Found

**Problem:** Tool name not recognized

**Solution:**
1. Run `tools/list` to see all available tools
2. Check spelling of tool name (case-sensitive)
3. Ensure server is properly initialized

---

## Integration with Claude Code

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "pytest-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "pytest-mcp-server:latest"
      ]
    }
  }
}
```

---

## Additional Resources

- **Main README:** See [README.md](README.md) for installation and setup
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Docker Documentation:** For container-specific operations
- **Examples Directory:** See `/examples/` for Python client examples

---

**Last Updated:** 2025-10-03
**MCP Server Version:** 0.1.0
**Protocol:** MCP over STDIO