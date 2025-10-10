# Pytest MCP Server

An AI-enhanced testing framework integration that provides Model Context Protocol (MCP) server functionality for pytest, enabling AI agents and developers to access test results, track debugging progress, generate unit tests, and provide targeted debugging assistance.

**Protocol:** MCP over STDIO (Standard Input/Output)

## Features

### Test Result Analysis
- 🧪 **Test Session Management**: Record and track pytest sessions with detailed environment information
- 🔍 **Failure Analysis**: AI-powered analysis of test failures with categorization and suggestions
- 🚀 **Debugging Assistance**: Track debugging progress and generate targeted prompts for LLMs
- 📊 **Test Statistics**: Comprehensive metrics and insights about test performance
- 🔗 **Similar Failure Detection**: Find patterns across test failures to identify common issues

### Test Generation
- ✨ **Code Analysis**: Analyze Python code for testing opportunities
- 🧬 **Unit Test Generation**: Generate comprehensive unit tests for functions and classes
- 💡 **Test Case Suggestions**: Get intelligent test case recommendations
- 📝 **Test File Generation**: Create complete test files with fixtures and imports
- 📈 **Coverage Analysis**: Analyze coverage and get improvement recommendations

### Infrastructure
- 🐳 **Docker Support**: Containerized with Chainguard secure base images
- 🔒 **STDIO Protocol**: Secure communication via Model Context Protocol
- 🛠️ **Claude Code Compatible**: Ready for integration with Claude Code and MCP Inspector

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd pytest-mcp-server

# Build the Docker image
docker-compose build pytest-mcp-server

# Test the MCP server via STDIO
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker run -i pytest-mcp-server:latest
```

#### Alternative Docker Commands

```bash
# Build the Docker image directly
docker build -t pytest-mcp-server:latest .

# Run the container interactively (STDIO mode)
docker run -i pytest-mcp-server:latest

# Run with persistent data volume
docker run -i \
  -v pytest_mcp_data:/app/data \
  -e PYTEST_MCP_DB_PATH=/app/data/pytest_mcp.db \
  pytest-mcp-server:latest

# Check container images
docker images | grep pytest-mcp-server
```

#### Quick STDIO Testing

Test the MCP server via STDIO protocol:

```bash
# Test initialization and list tools
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

# Test a tool (code analysis)
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def add(a, b): return a + b"}}}
EOF
```

#### Integration with Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "pytest-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "pytest-mcp-server:latest"]
    }
  }
}
```

### Local Installation

```bash
# Install using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .

# Start the server
pytest-mcp-server serve
```

## Available Tools

The MCP server provides **14 comprehensive tools** for AI agents and developers, including both test result analysis and test generation capabilities:

### Tool Quick Reference

| Tool Name | Purpose | Required Parameters | Optional Parameters |
|-----------|---------|-------------------|-------------------|
| `record_session_start` | Initialize test session | `environment.os`, `environment.python_version` | `environment.pytest_version`, `environment.platform`, `environment.architecture` |
| `record_test_outcome` | Record test results | `nodeid`, `outcome`, `duration` | `error`, `traceback`, `stdout`, `stderr`, `markers`, `keywords`, `file_path`, `line_number` |
| `record_session_finish` | Complete test session | `summary` (with `total_tests`, `passed`, `failed`, `skipped`, `exitstatus`, `duration`) | `summary.errors`, `summary.xfailed`, `summary.xpassed` |
| `get_session_status` | Get session information | None | `session_id` |
| `get_failure_analysis` | AI-powered failure analysis | `test_nodeid` | None |
| `find_similar_failures` | Find failure patterns | None | `error_pattern`, `test_pattern`, `limit` |
| `track_debugging_progress` | Manage debugging workflow | `failure_id`, `action` | `step_description`, `hypothesis`, `resolution_status`, `notes` |
| `generate_debugging_prompt` | Create LLM debugging context | `test_nodeid` | None |
| `get_test_statistics` | Comprehensive metrics | None | None |
| `analyze_code_for_testing` | Analyze code for test opportunities | None | `source_code`, `file_path` |
| `generate_unit_tests` | Generate unit tests for code | None | `source_code`, `file_path`, `function_name`, `framework`, `include_mocks`, `include_integration` |
| `suggest_test_cases` | Suggest test cases for functions | `source_code` | `function_name` |
| `generate_test_file` | Generate complete test files | None | `source_code`, `file_path`, `framework`, `include_mocks`, `include_integration` |
| `analyze_test_coverage` | Analyze test coverage | None | `coverage_file`, `source_dir`, `test_dir` |

### Detailed Tool Specifications

### 1. `record_session_start`

Record the start of a pytest session with environment information.

**Parameters:**
```json
{
  "environment": {
    "os": "Linux",
    "python_version": "3.12.0",
    "pytest_version": "8.0.0",
    "platform": "Linux-x86_64",
    "architecture": "x86_64"
  }
}
```

**MCP Inspector Usage:**
```json
{
  "tool": "record_session_start",
  "arguments": {
    "environment": {
      "os": "Linux",
      "python_version": "3.12.0"
    }
  }
}
```

### 2. `record_test_outcome`

Record the outcome of an individual test case.

**Parameters:**
```json
{
  "nodeid": "tests/test_example.py::test_function",
  "outcome": "failed",
  "duration": 0.123,
  "error": "AssertionError: assert 1 == 2",
  "traceback": "Full traceback...",
  "stdout": "Captured output...",
  "stderr": "Error output...",
  "markers": ["unit", "slow"],
  "keywords": ["test", "function"],
  "file_path": "tests/test_example.py",
  "line_number": 15
}
```

**MCP Inspector Usage:**
```json
{
  "tool": "record_test_outcome",
  "arguments": {
    "nodeid": "tests/test_example.py::test_failure",
    "outcome": "failed",
    "duration": 0.456,
    "error": "AssertionError: Expected 5, got 3"
  }
}
```

### 3. `record_session_finish`

Record the completion of a pytest session with summary statistics.

**Parameters:**
```json
{
  "summary": {
    "total_tests": 10,
    "passed": 7,
    "failed": 2,
    "skipped": 1,
    "errors": 0,
    "exitstatus": 1,
    "duration": 15.5
  }
}
```

### 4. `get_session_status`

Get the status and information about a test session.

**Parameters:**
```json
{
  "session_id": "optional-session-id"
}
```

### 5. `get_failure_analysis`

Get AI-powered analysis of a specific test failure.

**Parameters:**
```json
{
  "test_nodeid": "tests/test_example.py::test_failure"
}
```

### 6. `find_similar_failures`

Find similar test failures based on error patterns.

**Parameters:**
```json
{
  "error_pattern": "AssertionError",
  "test_pattern": "test_api",
  "limit": 10
}
```

### 7. `track_debugging_progress`

Track debugging progress for a specific failure.

**Parameters:**
```json
{
  "failure_id": "failure-123",
  "action": "add_step",
  "step_description": "Checked application logs",
  "hypothesis": "Network timeout issue",
  "resolution_status": "investigating",
  "notes": "Found timeout in logs"
}
```

### 8. `generate_debugging_prompt`

Generate a targeted debugging prompt for LLMs.

**Parameters:**
```json
{
  "test_nodeid": "tests/test_example.py::test_failure"
}
```

### 9. `get_test_statistics`

Get comprehensive test statistics and metrics.

**Parameters:** None

## Test Generation Tools

The following 5 tools provide comprehensive test generation capabilities:

### 10. `analyze_code_for_testing`

Analyze Python source code to identify testing opportunities and provide recommendations.

**Parameters:**
```json
{
  "source_code": "def add(a, b): return a + b",
  "file_path": "/path/to/source.py"
}
```

**Example Response:**
```json
{
  "success": true,
  "analysis": {
    "file_path": "/path/to/source.py",
    "functions": [
      {
        "name": "add",
        "complexity": 1,
        "parameters": 2,
        "has_docstring": false
      }
    ],
    "classes": [],
    "complexity_score": 1,
    "recommendations": [
      "Function 'add' lacks documentation. Tests can help clarify expected behavior."
    ]
  }
}
```

### 11. `generate_unit_tests`

Generate comprehensive unit tests for Python functions or classes.

**Parameters:**
```json
{
  "source_code": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b",
  "function_name": "divide",
  "framework": "pytest",
  "include_mocks": true,
  "include_integration": false
}
```

**Example Response:**
```json
{
  "success": true,
  "tests": [
    {
      "name": "test_divide_happy_path",
      "description": "Test normal division operation",
      "test_code": "def test_divide_happy_path():\n    result = divide(10, 2)\n    assert result == 5.0",
      "test_type": "happy_path",
      "priority": "high"
    },
    {
      "name": "test_divide_zero_denominator",
      "description": "Test division by zero raises ValueError",
      "test_code": "def test_divide_zero_denominator():\n    with pytest.raises(ValueError, match='Cannot divide by zero'):\n        divide(10, 0)",
      "test_type": "error_case",
      "priority": "high"
    }
  ]
}
```

### 12. `suggest_test_cases`

Suggest specific test cases for a function based on its signature and complexity.

**Parameters:**
```json
{
  "source_code": "def validate_email(email: str) -> bool:\n    import re\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))",
  "function_name": "validate_email"
}
```

**Example Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "name": "test_validate_email_happy_path",
      "description": "Test normal operation with valid inputs",
      "test_type": "happy_path",
      "priority": "high"
    },
    {
      "name": "test_validate_email_empty_email",
      "description": "Test with empty string for email",
      "test_type": "edge_case",
      "priority": "medium"
    },
    {
      "name": "test_validate_email_none_email",
      "description": "Test with None value for email",
      "test_type": "error_case",
      "priority": "high"
    }
  ]
}
```

### 13. `generate_test_file`

Generate a complete test file with imports, fixtures, and comprehensive test suite.

**Parameters:**
```json
{
  "file_path": "/src/calculator.py",
  "framework": "pytest",
  "include_mocks": true,
  "include_integration": false
}
```

**Example Response:**
```json
{
  "success": true,
  "test_file": {
    "file_name": "test_calculator.py",
    "source_file": "/src/calculator.py",
    "framework": "pytest",
    "imports": [
      "import pytest",
      "from src.calculator import Calculator"
    ],
    "test_code": "# Generated test file content...",
    "estimated_coverage": 85.0,
    "test_count": 12
  }
}
```

### 14. `analyze_test_coverage`

Analyze test coverage from coverage reports and provide improvement recommendations.

**Parameters:**
```json
{
  "coverage_file": "/path/to/coverage.json",
  "source_dir": "/src",
  "test_dir": "/tests"
}
```

**Example Response:**
```json
{
  "success": true,
  "coverage_reports": [
    {
      "file_path": "/src/calculator.py",
      "total_lines": 50,
      "covered_lines": 40,
      "coverage_percentage": 80.0,
      "missing_lines": [15, 23, 35],
      "uncovered_functions": ["handle_error"]
    }
  ],
  "improvement_plan": {
    "current_coverage": 80.0,
    "target_coverage": 90.0,
    "estimated_tests_needed": 3,
    "priority_actions": [
      {
        "action": "Add tests for handle_error function",
        "impact": "Improve coverage by ~10%",
        "tests": 3
      }
    ]
  }
}
```

## Docker Container Testing via STDIO

### Complete Tool Testing Guide for Docker

The MCP server uses **STDIO protocol** (not HTTP). For complete examples with all required arguments, see [MCP_TOOLS_USAGE.md](MCP_TOOLS_USAGE.md).

Here are quick STDIO examples for testing all 14 tools in Docker:

#### Basic STDIO Testing Pattern

All tools follow this MCP protocol flow:
1. Send `initialize` request
2. Send `notifications/initialized`
3. Send `tools/call` with tool name and arguments

```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{...}}}
EOF
```

#### 1. Test `record_session_start`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_session_start","arguments":{"environment":{"os":"Linux","python_version":"3.12.0"}}}}
EOF
```

#### 2. Test `record_test_outcome`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_test_outcome","arguments":{"nodeid":"tests/test_example.py::test_failure","outcome":"failed","duration":0.456,"error":"AssertionError: assert 1 == 2"}}}
EOF
```

#### 3. Test `record_session_finish`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"record_session_finish","arguments":{"summary":{"total_tests":10,"passed":7,"failed":2,"skipped":1,"errors":0,"exitstatus":1,"duration":15.5}}}}
EOF
```

#### 4. Test `get_session_status`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_session_status","arguments":{}}}
EOF
```

#### 5. Test `get_failure_analysis`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_failure_analysis","arguments":{"test_nodeid":"tests/test_example.py::test_failure"}}}
EOF
```

#### 6. Test `find_similar_failures`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_similar_failures","arguments":{"error_pattern":"AssertionError","limit":5}}}
EOF
```

#### 7. Test `track_debugging_progress`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"track_debugging_progress","arguments":{"failure_id":"fail-123","action":"add_step","step_description":"Reviewed assertion logic"}}}
EOF
```

#### 8. Test `generate_debugging_prompt`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_debugging_prompt","arguments":{"test_nodeid":"tests/test_example.py::test_failure"}}}
EOF
```

#### 9. Test `get_test_statistics`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_test_statistics","arguments":{}}}
EOF
```

#### 10. Test `analyze_code_for_testing`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_code_for_testing","arguments":{"source_code":"def add(a, b): return a + b"}}}
EOF
```

#### 11. Test `generate_unit_tests`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_unit_tests","arguments":{"source_code":"def multiply(x, y): return x * y","framework":"pytest"}}}
EOF
```

#### 12. Test `suggest_test_cases`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"suggest_test_cases","arguments":{"source_code":"def validate_email(email): return '@' in email","function_name":"validate_email"}}}
EOF
```

#### 13. Test `generate_test_file`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_test_file","arguments":{"source_code":"class Calculator:\n    def add(self, a, b): return a + b","framework":"pytest"}}}
EOF
```

#### 14. Test `analyze_test_coverage`
```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_test_coverage","arguments":{"source_dir":"/app/src","test_dir":"/app/tests"}}}
EOF
```

### List All Available Tools

```bash
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc" | tail -1
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```

### Using with Claude Code

Add to your Claude Code configuration (`claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "pytest-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "pytest-mcp-server:latest"]
    }
  }
}
```

### Docker Environment Variables

Configure the container with environment variables:

```bash
docker run -i \
  --name pytest-mcp-server \
  -v pytest_mcp_data:/app/data \
  -e PYTEST_MCP_DB_PATH=/app/data/pytest_mcp.db \
  -e PYTEST_MCP_LOG_LEVEL=DEBUG \
  pytest-mcp-server:latest
```

Available environment variables:
- `PYTEST_MCP_DB_PATH`: Database file path (default: `/app/data/pytest_mcp.db`)
- `PYTEST_MCP_LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## Usage Examples

### With Claude Code

The recommended way to use this MCP server is with Claude Code. Add to your configuration:

```json
{
  "mcpServers": {
    "pytest-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "pytest-mcp-server:latest"]
    }
  }
}
```

Claude Code will automatically communicate with the server via STDIO

### With Pytest Integration

1. Install the pytest plugin:
   ```bash
   pip install -e .
   ```

2. Run pytest with MCP integration:
   ```bash
   pytest --mcp tests/
   ```

3. View results in the MCP server or generated JSON file

### Programmatic Usage

```python
from pytest_mcp_server import create_server
import asyncio

# Create server instance
app = create_server()

# Call tools directly
result = app.call_tool("record_session_start", {
    "environment": {
        "os": "Linux",
        "python_version": "3.12.0"
    }
})
```

## Configuration

### MCP Client Configuration

For Claude Code or other MCP clients using STDIO:

```json
{
  "mcpServers": {
    "pytest-mcp": {
      "command": "docker",
      "args": ["run", "-i", "pytest-mcp-server:latest"],
      "env": {
        "PYTEST_MCP_DB_PATH": "/app/data/pytest_mcp.db",
        "PYTEST_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Standalone (Non-Docker) Configuration

For local development without Docker:

```json
{
  "mcpServers": {
    "pytest-mcp": {
      "command": "python",
      "args": ["-m", "pytest_mcp_server.cli", "serve"],
      "env": {
        "PYTEST_MCP_DB_PATH": "./pytest_mcp.db",
        "PYTEST_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTEST_MCP_DB_PATH` | Path to SQLite database | `:memory:` |
| `PYTEST_MCP_LOG_LEVEL` | Logging level | `INFO` |

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd pytest-mcp-server

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pytest_mcp_server --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m "integration"  # Only integration tests
```

### Development with Docker

```bash
# Start development server
docker-compose --profile dev up pytest-mcp-dev

# Run tests in container
docker-compose exec pytest-mcp-dev pytest

# Access container shell
docker-compose exec pytest-mcp-dev bash
```

## Docker Support

### Production Deployment

```bash
# Build production image using docker-compose
docker-compose build pytest-mcp-server

# Test the server via STDIO
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
```

### Development Environment

```bash
# Build development image
docker build --target development -t pytest-mcp-server:dev .

# Run development container with interactive STDIO
docker run -it \
  --name pytest-mcp-dev \
  -v $(pwd):/app/src:ro \
  -v pytest_mcp_data:/app/data \
  pytest-mcp-server:dev
```

### Docker Compose

The project includes a `docker-compose.yml` file for building the MCP server. The server runs in STDIO mode and does not expose any ports.

```bash
# Build the image
docker-compose build pytest-mcp-server

# Test via STDIO
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```

## Testing the MCP Server

### Unit Tests

```bash
# Run all unit tests
pytest tests/ -v

# Test specific modules
pytest tests/test_models.py -v
pytest tests/test_server.py -v
pytest tests/test_analysis.py -v
```

### Integration Testing

```bash
# Test with actual MCP client
pytest tests/test_integration.py -v

# Test Docker container
docker-compose exec pytest-mcp-server pytest
```

### Manual Testing via STDIO

Test the server manually using STDIO protocol:

```bash
# Test with echo/pipe
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
python -m pytest_mcp_server.cli serve 2>/dev/null | grep "jsonrpc"

# Test with Docker
cat <<EOF | docker run -i pytest-mcp-server:latest 2>/dev/null | grep "jsonrpc"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```

## API Reference

### MCP Protocol

The server uses the Model Context Protocol (MCP) via STDIO. All communication follows JSON-RPC 2.0 format:

**Initialize:**
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"client","version":"1.0"}}}
```

**List Tools:**
```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

**Call Tool:**
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"tool_name","arguments":{...}}}
```

### CLI Commands

```bash
# Start server in STDIO mode
pytest-mcp-server serve [--db-path PATH]

# Note: The server only runs in STDIO mode
# Use with MCP clients like Claude Code
```

## Architecture

The server consists of several key components:

- **Server Layer** (`server.py`): FastMCP-based server with tool definitions
- **Storage Layer** (`storage.py`): SQLite-based persistent storage
- **Analysis Engine** (`analysis.py`): AI-powered failure analysis and debugging assistance
- **Data Models** (`models.py`): Pydantic models for type safety and validation
- **Pytest Plugin** (`plugin.py`): Integration hooks for pytest
- **CLI Interface** (`cli.py`): Command-line interface for server management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:

- 📧 Email: developer@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/pytest-mcp-server/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-repo/pytest-mcp-server/discussions)

## Acknowledgments

- Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for MCP server functionality
- Inspired by the need for AI-enhanced debugging in software testing
- Thanks to the pytest community for the excellent testing framework