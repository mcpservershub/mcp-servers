# Hurl MCP Server

MCP (Model Context Protocol) Server for Hurl - a command-line tool for running HTTP requests and testing APIs.

## Features

This MCP server provides tools to interact with Hurl CLI:

- **run_hurl**: Execute a .hurl file and get the response
- **run_hurl_test**: Execute .hurl file in test mode
- **run_hurl_with_variables**: Execute with custom variables
- **run_hurl_parallel**: Execute multiple .hurl files in parallel
- **validate_hurl**: Validate .hurl file syntax
- **create_hurl_file**: Create .hurl files programmatically

All tools that generate output support an optional `output_file` parameter to save results to a file.

## Installation

```bash
pip install -e .
```

## Usage

### Direct execution
```bash
python -m hurl_mcp.server
```

### Docker
```bash
docker build -t hurl-mcp-server .
docker run -it hurl-mcp-server
```

## MCP Client Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "hurl": {
      "command": "python",
      "args": ["-m", "hurl_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

## Tool Examples

### run_hurl
```json
{
  "hurl_file": "api_test.hurl",
  "output_format": "json",
  "output_file": "/tmp/api_response.json",
  "verbose": true
}
```

### run_hurl_test
```json
{
  "hurl_file": "tests/",
  "report_format": "junit",
  "report_path": "/tmp/test-report.xml",
  "output_file": "/tmp/test-output.txt",
  "parallel": true,
  "jobs": 4
}
```

### run_hurl_with_variables
```json
{
  "hurl_file": "template.hurl",
  "variables": {
    "base_url": "https://api.example.com",
    "api_key": "your-key"
  },
  "output_file": "/tmp/output.txt"
}
```

### validate_hurl
```json
{
  "hurl_content": "GET https://example.com\nHTTP 200",
  "output_file": "/tmp/validation-report.json"
}
```

## Requirements

- Python 3.12+
- Hurl CLI installed and available in PATH
- mcp[cli] package

## License

MIT