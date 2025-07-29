# Semgrep MCP Server

An MCP (Model Context Protocol) server that provides tools for running Semgrep static analysis and security scanning on code. This server enables AI assistants to perform comprehensive code analysis, security checks, and custom pattern matching using Semgrep's powerful capabilities.

## Overview

The Semgrep MCP server exposes several tools for code analysis:

### Core Scanning Tools
- **semgrep_scan**: Run Semgrep scans with default or custom configurations
- **semgrep_scan_with_custom_rule**: Scan code with custom-written Semgrep rules
- **security_check**: Perform fast security checks on code

### Utility Tools
- **semgrep_rule_schema**: Get the schema for writing Semgrep rules
- **get_supported_languages**: List all languages supported by Semgrep
- **get_abstract_syntax_tree**: Generate AST for code analysis

## Prerequisites

- Docker installed on your system
- Semgrep CLI (automatically included in the Docker image)
- MCP-compatible client (e.g., Claude Desktop, Cline)

## Available Tools

### 1. `semgrep_scan`
Runs a Semgrep scan on provided code content with optional configuration.

**Parameters:**
- `code_files` (required): List of dictionaries with 'filename' and 'content' keys
- `config` (optional): Semgrep configuration (e.g., 'p/python', 'p/security', 'auto')

**Returns:** SemgrepScanResult with findings in JSON format

### 2. `semgrep_scan_with_custom_rule`
Scans code using custom Semgrep rules that you provide.

**Parameters:**
- `code_files` (required): List of dictionaries with 'filename' and 'content' keys
- `rule` (required): Semgrep YAML rule string

**Returns:** SemgrepScanResult with findings in JSON format

### 3. `security_check`
Performs a fast security check on code and returns any issues found.

**Parameters:**
- `code_files` (required): List of dictionaries with 'filename' and 'content' keys

**Returns:** String summary of security issues found

### 4. `semgrep_rule_schema`
Retrieves the schema for writing Semgrep rules.

**Parameters:** None

**Returns:** Schema in JSON format

### 5. `get_supported_languages`
Lists all programming languages supported by Semgrep.

**Parameters:** None

**Returns:** List of supported language names

### 6. `get_abstract_syntax_tree`
Generates the Abstract Syntax Tree (AST) for provided code.

**Parameters:**
- `code` (required): The code to analyze
- `language` (required): Programming language of the code

**Returns:** AST in JSON format

## Configuration

### Docker Configuration

To use the Semgrep MCP server with Docker, add the following configuration to your MCP client's settings:

```json
{
  "mcpServers": {
    "semgrep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "santoshkal/semgrep-mcp"
      ]
    }
  }
}
```

### Advanced Configuration with Volume Mounts

If you need to scan files on disk or use custom rule files:

```json
{
  "mcpServers": {
    "semgrep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--volume=/path/to/rules:/rules:ro",
        "--volume=/path/to/code:/code:ro",
        "santoshkal/semgrep-mcp"
      ]
    }
  }
}
```

## Usage Examples

### Basic Security Scan

```
Tool: security_check
Arguments:
{
  "code_files": [
    {
      "filename": "app.py",
      "content": "import os\nos.system(user_input)"
    }
  ]
}
```

### Scan with Specific Configuration

```
Tool: semgrep_scan
Arguments:
{
  "code_files": [
    {
      "filename": "main.py",
      "content": "def process_data(data):\n    eval(data)"
    }
  ],
  "config": "p/python"
}
```

### Custom Rule Scan

```
Tool: semgrep_scan_with_custom_rule
Arguments:
{
  "code_files": [
    {
      "filename": "test.js",
      "content": "const password = 'hardcoded123';"
    }
  ],
  "rule": "rules:\n  - id: hardcoded-password\n    pattern: |
      $VAR = '...'\n    pattern-either:\n      - metavariable-regex:\n          metavariable: $VAR\n          regex: (password|passwd|pwd)\n    message: Hardcoded password detected\n    severity: ERROR\n    languages: [javascript]"
}
```

### Get AST for Code Analysis

```
Tool: get_abstract_syntax_tree
Arguments:
{
  "code": "function hello() { return 'world'; }",
  "language": "javascript"
}
```

### Check Supported Languages

```
Tool: get_supported_languages
Arguments: {}
```

## Prompts

The server also provides a prompt for writing custom Semgrep rules:

### `write_custom_semgrep_rule`
Helps generate custom Semgrep rules for specific code patterns.

**Parameters:**
- `code`: The code to analyze
- `language`: Programming language of the code

## Resources

The server provides access to Semgrep resources:

- `semgrep://rule/schema`: Semgrep rule YAML syntax specification
- `semgrep://rule/{rule_id}/yaml`: Full Semgrep rule from the registry

## Transport Modes

The server supports multiple transport protocols:
- **stdio** (default for local usage)
- **streamable-http** (for HTTP-based communication)
- **sse** (Server-Sent Events, legacy)

## Security Considerations

- The server validates all file paths to prevent directory traversal
- Temporary files are created securely and cleaned up after use
- Code is analyzed in isolated temporary directories
- All user inputs are validated before processing

## Building the Docker Image

If you want to build the image yourself:

```bash
cd semgrep-mcp
docker build -t semgrep-mcp .
```

## Troubleshooting

### Common Issues

1. **"Semgrep is not installed" error**
   - The Docker image includes Semgrep automatically
   - If running locally, install with: `pip install semgrep`

2. **"Invalid code files format" error**
   - Ensure code_files is a list of dictionaries
   - Each dictionary must have 'filename' and 'content' keys
   - Filenames must be relative paths, not absolute

3. **Timeout errors**
   - Large codebases may take longer to scan
   - Default timeout is 5 minutes (300 seconds)

### File Path Requirements

- All filenames in `code_files` must be relative paths
- The server creates temporary directories for scanning
- No need to mount volumes unless using files from disk

## License

This MCP server is distributed under the MIT license. Semgrep itself has its own licensing terms.
---
*Last updated: 2025-07-29 16:13:12 UTC*
