# HTTPie MCP Server

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/anthropics/fastmcp)

**Production-ready Model Context Protocol (MCP) Server for HTTPie CLI** - Empower AI agents and developers to efficiently interact with HTTP/S APIs through a standardized, AI-friendly interface.

## 🚀 Overview

The HTTPie MCP Server provides a robust bridge between the powerful [HTTPie CLI tool](https://httpie.io) and AI agents via the Model Context Protocol. It enables LLMs and automated workflows to make HTTP requests, download files, and manage persistent sessions with comprehensive error handling, input validation, and detailed logging.

### Key Features

- **🎯 Complete HTTPie Integration**: Full access to HTTPie's rich feature set including JSON support, authentication, sessions, file uploads, and SSL options
- **🚀 Advanced Tools**: 9 specialized MCP tools including multipart uploads, streaming, retry logic, status validation, JSON schema validation, and data extraction
- **🔒 Security First**: Input validation, command injection prevention, and secure subprocess execution
- **📊 Structured Responses**: Consistent JSON response format for easy parsing by AI agents
- **🔁 Resilient Operations**: Built-in retry logic with exponential backoff for handling transient failures
- **🐳 Docker Ready**: Optimized multi-stage Dockerfile for containerized deployments
- **✅ Comprehensive Testing**: Full test coverage with unit and integration tests
- **📖 Type-Safe**: Complete type hints and Pydantic schemas for all interfaces
- **🔍 Observable**: Detailed logging for debugging and monitoring

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Standalone Installation](#standalone-installation)
  - [Docker Installation](#docker-installation)
- [Usage](#usage)
  - [Starting the Server](#starting-the-server)
  - [MCP Configuration](#mcp-configuration)
  - [Testing with MCP Inspector](#testing-with-mcp-inspector)
- [Available Tools](#available-tools)
  - [http_request](#http_request)
  - [http_download](#http_download)
  - [http_session_request](#http_session_request)
  - [http_multipart_upload](#http_multipart_upload)
  - [http_check_status](#http_check_status)
  - [http_stream](#http_stream)
  - [http_validate_json_schema](#http_validate_json_schema)
  - [http_retry](#http_retry)
  - [http_response_extract](#http_response_extract)
- [Examples](#examples)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Python 3.12+** (required)
- **HTTPie CLI** (required in runtime environment)
- **Docker** (optional, for containerized deployment)
- **MCP Client** (Claude Desktop, custom MCP client, or MCP Inspector for testing)

## Installation

### Standalone Installation

1. **Clone or create the project directory:**

```bash
cd /path/to/httpie-mcp-server
```

2. **Create and activate a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install the package with dependencies:**

```bash
# Install using pip
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Or install with extraction tools (JSON schema validation, JSONPath)
pip install -e ".[extraction]"

# Or install everything (dev + extraction)
pip install -e ".[dev,extraction]"
```

4. **Install HTTPie (if not already installed):**

```bash
pip install httpie>=3.2.0
```

5. **Verify installation:**

```bash
# Check HTTPie
http --version

# Check MCP server
python -m httpie_mcp.server --help
```

### Docker Installation

**Build the Docker image:**

```bash
docker build -t httpie-mcp-server:latest .
```

**Run the container:**

```bash
docker run -i httpie-mcp-server:latest
```

**For integration with MCP clients, use STDIO mode:**

```bash
docker run -i --rm httpie-mcp-server:latest
```

## Usage

### Starting the Server

The HTTPie MCP Server runs in **STDIO mode** for MCP client communication:

**Standalone:**

```bash
python -m httpie_mcp.server
```

**Using the installed script:**

```bash
httpie-mcp-server
```

**Docker:**

```bash
docker run -i --rm httpie-mcp-server:latest
```

### MCP Configuration

To integrate with Claude Desktop or other MCP clients, add the following configuration to your MCP settings file:

**For Standalone Installation** (`~/.config/claude/claude_desktop_config.json` on macOS/Linux):

```json
{
  "mcpServers": {
    "httpie": {
      "command": "python",
      "args": ["-m", "httpie_mcp.server"],
      "env": {}
    }
  }
}
```

**For Docker Installation:**

```json
{
  "mcpServers": {
    "httpie": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "httpie-mcp-server:latest"],
      "env": {}
    }
  }
}
```

**With Custom Python/Virtual Environment:**

```json
{
  "mcpServers": {
    "httpie": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "httpie_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/httpie-mcp-server/src"
      }
    }
  }
}
```

### Testing with MCP Inspector

The [MCP Inspector](https://github.com/anthropics/mcp-inspector) is a valuable tool for testing and debugging MCP servers:

1. **Install MCP Inspector:**

```bash
npm install -g @modelcontextprotocol/inspector
```

2. **Run the inspector:**

```bash
mcp-inspector python -m httpie_mcp.server
```

Or with Docker:

```bash
mcp-inspector docker run -i --rm httpie-mcp-server:latest
```

3. **Open the web interface** (usually `http://localhost:6274`) to interactively test the MCP tools.

## Available Tools

### http_request

Make HTTP requests with comprehensive options.

**Signature:**

```python
def http_request(
    url: str,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    raw_data: Optional[str] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    follow_redirects: bool = False,
    verify_ssl: bool = True,
    proxy: Optional[str] = None,
    session: Optional[str] = None,
    output_headers: bool = True,
    output_body: bool = True,
    output_metadata: bool = False,
    verbose: bool = False,
    pretty_print: str = "all",
    cert: Optional[str] = None,
    cert_key: Optional[str] = None,
    download: bool = False,
    output_file: Optional[str] = None,
    max_redirects: Optional[int] = None,
    offline: bool = False,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target URL (e.g., `https://api.example.com/users`)
- `method`: HTTP method (GET, POST, PUT, DELETE, etc.)
- `headers`: Custom headers as dict (e.g., `{"Authorization": "Bearer token"}`)
- `query_params`: URL parameters (e.g., `{"page": "1", "limit": "10"}`)
- `json_data`: JSON body data (e.g., `{"name": "John", "age": 30}`)
- `form_data`: Form data (sets `Content-Type: application/x-www-form-urlencoded`)
- `raw_data`: Raw string body data
- `auth`: Credentials in format `username:password` or `token`
- `auth_type`: Authentication type (`basic`, `bearer`, or `digest`)
- `timeout`: Request timeout in seconds (0 = no timeout)
- `follow_redirects`: Follow 3xx redirects
- `verify_ssl`: Verify SSL certificates
- `proxy`: Proxy URL
- `session`: Session name for persistent state
- `verbose`: Enable verbose output
- `offline`: Build request without sending (dry-run)

**Returns:**

```json
{
  "success": true,
  "status_code": 200,
  "headers": "HTTP/1.1 200 OK\nContent-Type: application/json\n...",
  "body": "{\"message\": \"success\"}",
  "metadata": null,
  "error": null,
  "command": "http GET https://api.example.com/data"
}
```

### http_download

Download files from URLs with resume capability.

**Signature:**

```python
def http_download(
    url: str,
    output_file: Optional[str] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    resume: bool = False,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): URL of file to download
- `output_file`: Save location (auto-detected if omitted)
- `auth`: Authentication credentials
- `auth_type`: Authentication type
- `resume`: Resume interrupted download (requires `output_file`)
- `timeout`: Download timeout in seconds
- `verify_ssl`: Verify SSL certificates
- `headers`: Custom headers

### http_session_request

Make requests with persistent sessions (cookies, auth, headers).

**Signature:**

```python
def http_session_request(
    session_name: str,
    url: str,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    read_only: bool = False,
    follow_redirects: bool = False,
    verify_ssl: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]
```

**Parameters:**

- `session_name` (required): Session identifier
- `url` (required): Target URL
- `read_only`: Read session without updating it
- Other parameters same as `http_request`

### http_multipart_upload

Upload files using multipart/form-data encoding (RFC 2388).

**Signature:**

```python
def http_multipart_upload(
    url: str,
    files: Dict[str, str],
    form_data: Optional[Dict[str, str]] = None,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
    boundary: Optional[str] = None,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target URL for upload
- `files` (required): Dict mapping field names to file paths (e.g., `{"document": "/tmp/file.pdf"}`)
- `form_data`: Additional form fields (e.g., `{"title": "My Document", "description": "..."}`)
- `method`: HTTP method (typically POST or PUT)
- `boundary`: Custom multipart boundary string (auto-generated if omitted)
- Other parameters same as `http_request`

**Use Cases:** File uploads, multi-file uploads, form submissions with files

### http_check_status

Make HTTP request and validate status code against expected values.

**Signature:**

```python
def http_check_status(
    url: str,
    expected_status: List[int] = [200],
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target URL to check
- `expected_status`: List of acceptable status codes (default: `[200]`)
- Other parameters same as `http_request`

**Returns:**

```json
{
  "status_check": "passed",
  "expected": [200, 201],
  "actual": 200,
  "response_time_ms": 150
}
```

**Use Cases:** Health checks, API monitoring, endpoint validation, uptime checks

### http_stream

Stream HTTP responses line by line (for Server-Sent Events, streaming APIs, logs).

**Signature:**

```python
def http_stream(
    url: str,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    max_lines: Optional[int] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target streaming URL
- `max_lines`: Maximum number of lines to capture (omit for unlimited)
- Other parameters same as `http_request`

**Use Cases:** Server-Sent Events (SSE), streaming APIs, real-time logs, chat streams

### http_validate_json_schema

Make HTTP request and validate response body against a JSON schema.

**Signature:**

```python
def http_validate_json_schema(
    url: str,
    json_schema: Dict[str, Any],
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target API URL
- `json_schema` (required): JSON Schema (draft-07) to validate against
- Other parameters same as `http_request`

**Returns:**

```json
{
  "validation_passed": true,
  "validation_errors": []
}
```

**Requirements:** Install optional dependency: `pip install -e ".[extraction]"`

**Use Cases:** API contract testing, response validation, schema enforcement, integration testing

### http_retry

Make HTTP request with automatic retry logic and exponential backoff.

**Signature:**

```python
def http_retry(
    url: str,
    max_retries: int = 3,
    retry_delay_ms: int = 1000,
    retry_on_status: List[int] = [500, 502, 503, 504],
    exponential_backoff: bool = True,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target URL
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_delay_ms`: Initial delay between retries in milliseconds (default: 1000)
- `retry_on_status`: Status codes that trigger retry (default: 5xx errors)
- `exponential_backoff`: Use exponential backoff (2^attempt * delay) (default: true)
- Other parameters same as `http_request`

**Returns:**

```json
{
  "attempts": 3,
  "retry_history": [
    {"attempt": 1, "status_code": 503, "success": false, "delay_ms": 0},
    {"attempt": 2, "status_code": 502, "success": false, "delay_ms": 1000},
    {"attempt": 3, "status_code": 200, "success": true, "delay_ms": 2000}
  ]
}
```

**Use Cases:** Resilient API calls, handling transient failures, unstable endpoints, rate-limited APIs

### http_response_extract

Make HTTP request and extract specific data from response using JSONPath or regex.

**Signature:**

```python
def http_response_extract(
    url: str,
    extractor: str,
    expressions: Dict[str, str],
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]
```

**Parameters:**

- `url` (required): Target URL
- `extractor` (required): Extraction method (`"jsonpath"` or `"regex"`)
- `expressions` (required): Dict mapping field names to extraction expressions
  - JSONPath: `{"user_name": "$.data.user.name", "user_id": "$.data.user.id"}`
  - Regex: `{"emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}`
- Other parameters same as `http_request`

**Returns:**

```json
{
  "extracted_data": {
    "user_name": ["John Doe"],
    "user_id": [123]
  },
  "extraction_errors": {}
}
```

**Requirements:** Install optional dependency: `pip install -e ".[extraction]"`

**Use Cases:** Data scraping, API response parsing, extracting specific fields, transformation pipelines

## Examples

### Example 1: Simple GET Request

```python
# Via MCP client or tool call
http_request(url="https://httpbin.org/get")
```

**Expected Response:**

```json
{
  "success": true,
  "status_code": 200,
  "body": "{\"args\": {}, \"headers\": {...}, \"origin\": \"...\", \"url\": \"https://httpbin.org/get\"}"
}
```

### Example 2: POST JSON Data

```python
http_request(
    url="https://httpbin.org/post",
    method="POST",
    json_data={"name": "Alice", "email": "alice@example.com", "active": True}
)
```

### Example 3: Authenticated API Request

```python
http_request(
    url="https://api.github.com/user/repos",
    auth="username:ghp_yourtoken",
    auth_type="basic",
    headers={"Accept": "application/vnd.github.v3+json"}
)
```

### Example 4: Download File

```python
http_download(
    url="https://releases.ubuntu.com/22.04/ubuntu-22.04.3-desktop-amd64.iso",
    output_file="/tmp/ubuntu.iso",
    resume=True
)
```

### Example 5: Session-Based Workflow

```python
# Step 1: Login and create session
http_session_request(
    session_name="my-app-session",
    url="https://api.example.com/auth/login",
    method="POST",
    json_data={"username": "user", "password": "pass"}
)

# Step 2: Make authenticated request using the same session
http_session_request(
    session_name="my-app-session",
    url="https://api.example.com/user/profile"
)

# Step 3: Make another request (session persists cookies/auth)
http_session_request(
    session_name="my-app-session",
    url="https://api.example.com/user/settings",
    method="PUT",
    json_data={"theme": "dark"}
)
```

### Example 6: Form Data Upload

```python
http_request(
    url="https://httpbin.org/post",
    method="POST",
    form_data={
        "field1": "value1",
        "field2": "value2"
    },
    headers={"X-Custom-Header": "CustomValue"}
)
```

### Example 7: Offline Mode (Dry-Run)

```python
# Build and inspect request without sending
http_request(
    url="https://api.example.com/data",
    method="POST",
    json_data={"key": "value"},
    auth="user:pass",
    offline=True
)
```

### Example 8: Proxy and SSL Options

```python
http_request(
    url="https://api.example.com/data",
    proxy="http://proxy.company.com:8080",
    verify_ssl=False,  # Skip SSL verification (use cautiously!)
    timeout=30
)
```

### Example 9: Multipart File Upload

```python
# Upload multiple files with form data
http_multipart_upload(
    url="https://api.example.com/documents/upload",
    files={
        "document": "/home/user/report.pdf",
        "attachment": "/home/user/data.csv",
        "thumbnail": "/home/user/preview.jpg"
    },
    form_data={
        "title": "Q4 Financial Report",
        "category": "finance",
        "visibility": "private"
    },
    headers={"Authorization": "Bearer token123"}
)
```

### Example 10: Health Check with Status Validation

```python
# Monitor API endpoint health
http_check_status(
    url="https://api.example.com/health",
    expected_status=[200, 204],
    timeout=5
)

# Response:
# {
#   "status_check": "passed",
#   "expected": [200, 204],
#   "actual": 200,
#   "response_time_ms": 145
# }
```

### Example 11: Streaming Server-Sent Events

```python
# Connect to SSE endpoint and capture events
http_stream(
    url="https://api.example.com/events/stream",
    headers={"Accept": "text/event-stream"},
    max_lines=100  # Capture first 100 lines
)

# Use case: Real-time notifications, chat messages, live updates
```

### Example 12: JSON Schema Validation (API Contract Testing)

```python
# Validate API response matches expected schema
user_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "active": {"type": "boolean"}
    },
    "required": ["id", "name", "email"]
}

http_validate_json_schema(
    url="https://api.example.com/users/123",
    json_schema=user_schema
)

# Response:
# {
#   "validation_passed": true,
#   "validation_errors": []
# }
```

### Example 13: Resilient API Call with Retry Logic

```python
# Handle transient failures with exponential backoff
http_retry(
    url="https://api.example.com/data",
    max_retries=5,
    retry_delay_ms=1000,
    retry_on_status=[500, 502, 503, 504, 429],  # Include rate-limit errors
    exponential_backoff=True,
    headers={"Authorization": "Bearer token123"}
)

# Delays: 1s, 2s, 4s, 8s, 16s between retries
# Returns detailed retry history for debugging
```

### Example 14: Extract Data with JSONPath

```python
# Extract specific fields from complex API response
http_response_extract(
    url="https://api.github.com/repos/httpie/cli",
    extractor="jsonpath",
    expressions={
        "repo_name": "$.name",
        "stars": "$.stargazers_count",
        "owner": "$.owner.login",
        "topics": "$.topics[*]"
    }
)

# Response:
# {
#   "extracted_data": {
#     "repo_name": ["cli"],
#     "stars": [34567],
#     "owner": ["httpie"],
#     "topics": [["http", "cli", "api", "python"]]
#   },
#   "extraction_errors": {}
# }
```

### Example 15: Extract Data with Regex

```python
# Extract emails and phone numbers from HTML page
http_response_extract(
    url="https://example.com/contact",
    extractor="regex",
    expressions={
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phones": r"\+?1?\d{9,15}"
    }
)

# Response:
# {
#   "extracted_data": {
#     "emails": ["info@example.com", "support@example.com"],
#     "phones": ["+1234567890", "+9876543210"]
#   },
#   "extraction_errors": {}
# }
```

## Development

### Project Structure

```
httpie-mcp-server/
├── src/
│   └── httpie_mcp/
│       ├── __init__.py
│       ├── server.py          # FastMCP server with tool definitions
│       ├── httpie_client.py   # HTTPie subprocess wrapper
│       └── schemas.py          # Pydantic validation schemas
├── tests/
│   ├── __init__.py
│   └── test_server.py         # Comprehensive test suite
├── Dockerfile                 # Multi-stage production Dockerfile
├── pyproject.toml             # Project metadata and dependencies
├── README.md                  # This file
└── mcp-config.json            # Sample MCP configuration
```

### Setting Up Development Environment

1. **Clone the repository:**

```bash
git clone <repository-url>
cd httpie-mcp-server
```

2. **Create virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate
```

3. **Install development dependencies:**

```bash
pip install -e ".[dev]"
```

4. **Install pre-commit hooks (optional):**

```bash
pip install pre-commit
pre-commit install
```

### Code Quality

The project uses:

- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Black** (via Ruff): Code formatting

**Run linter:**

```bash
ruff check src/ tests/
```

**Run type checker:**

```bash
mypy src/
```

**Format code:**

```bash
ruff format src/ tests/
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=httpie_mcp --cov-report=html --cov-report=term
```

### Run Specific Test File

```bash
pytest tests/test_server.py -v
```

### Run Specific Test

```bash
pytest tests/test_server.py::TestHTTPieClient::test_make_request_simple_get -v
```

### Test with MCP Inspector

```bash
mcp-inspector python -m httpie_mcp.server
```

Then use the web UI to manually test each tool with various inputs.

## Troubleshooting

### HTTPie Not Found Error

**Problem:** `HTTPie executable 'http' not found`

**Solution:**

```bash
# Install HTTPie
pip install httpie

# Verify installation
http --version
```

### Permission Denied in Docker

**Problem:** Permission errors when running in Docker

**Solution:** Ensure the container runs as the correct user:

```dockerfile
USER mcpuser  # Already configured in Dockerfile
```

### SSL Verification Errors

**Problem:** SSL certificate verification failures

**Solution:**

```python
http_request(url="https://...", verify_ssl=False)
```

⚠️ **Security Note:** Only disable SSL verification for testing or trusted internal services.

### Timeout Issues

**Problem:** Requests timeout

**Solution:** Increase timeout or set to 0 (unlimited):

```python
http_request(url="https://...", timeout=60)  # 60 seconds
```

### Session Data Location

HTTPie sessions are stored in:

- **Linux/macOS:** `~/.config/httpie/sessions/`
- **Windows:** `%APPDATA%\httpie\sessions\`

To inspect or clear sessions:

```bash
ls ~/.config/httpie/sessions/
rm -rf ~/.config/httpie/sessions/my-session-name/
```

### Debugging Tips

1. **Enable verbose output:**

```python
http_request(url="https://...", verbose=True)
```

2. **Check logs:** The server logs to stderr with detailed information:

```bash
python -m httpie_mcp.server 2> server.log
```

3. **Test offline mode:** Verify request construction without sending:

```python
http_request(url="https://...", offline=True)
```

4. **Inspect the generated command:** Check the `command` field in responses to see the exact HTTPie command executed.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Client                           │
│                   (Claude Desktop, etc.)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │ STDIO (MCP Protocol)
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    FastMCP Server                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MCP Tools (http_request, http_download, etc.)      │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼────────────────────────────────────┐   │
│  │         HTTPie Client Wrapper                        │   │
│  │  - Input validation (Pydantic schemas)               │   │
│  │  - Command building                                  │   │
│  │  - Security (injection prevention)                   │   │
│  │  - Error handling                                    │   │
│  └────────────────┬────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────┘
                    │ Subprocess
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                    HTTPie CLI                               │
│              (http / https commands)                        │
└─────────────────────────────────────────────────────────────┘
```

### Security Measures

1. **Input Validation:** All inputs validated with Pydantic schemas
2. **Command Injection Prevention:** Headers and values sanitized
3. **Subprocess Safety:** Using `subprocess.run()` with argument lists (not shell=True)
4. **Timeouts:** Configurable timeouts prevent hanging
5. **Non-root Execution:** Docker container runs as non-root user
6. **Minimal Dependencies:** Reduced attack surface

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Run linting (`ruff check`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Acknowledgments

- [HTTPie](https://httpie.io) - Modern, user-friendly command-line HTTP client
- [Anthropic MCP](https://github.com/anthropics/mcp) - Model Context Protocol
- [FastMCP](https://github.com/anthropics/fastmcp) - FastMCP framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation

## Support

- **Issues:** [GitHub Issues](https://github.com/httpie/mcp-server/issues)
- **Discussions:** [GitHub Discussions](https://github.com/httpie/mcp-server/discussions)
- **Documentation:** [HTTPie Docs](https://httpie.io/docs)

---

**Built with ❤️ for the AI and developer community**
