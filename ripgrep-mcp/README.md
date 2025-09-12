# Ripgrep MCP Server

A powerful MCP (Model Context Protocol) server that provides programmatic access to ripgrep's blazing-fast text search capabilities. This server enables AI agents and MCP clients to perform sophisticated text searches, code analysis, and pattern matching across codebases of any size.

## Features

- **High-Performance Search**: Leverage ripgrep's speed for instant results
- **Smart Filtering**: Automatic .gitignore respect and binary file handling
- **File Type Awareness**: Search specific programming languages and file types
- **Context Support**: Get surrounding lines for better understanding
- **Multiline Patterns**: Search across line boundaries
- **Statistics**: Get search performance metrics
- **Docker Ready**: Containerized deployment with security best practices

## Available Tools

### 1. `search`
Basic pattern search with regex support.

**Parameters:**
- `pattern` (string, required): Regex pattern to search
- `path` (string, optional): Directory or file to search in
- `case_sensitive` (boolean, default: true): Whether search is case sensitive
- `whole_word` (boolean, default: false): Match whole words only
- `line_numbers` (boolean, default: true): Include line numbers in results
- `max_results` (integer, default: 100): Maximum number of results

**Example:**
```json
{
  "tool": "search",
  "args": {
    "pattern": "TODO|FIXME",
    "path": "/workspace",
    "case_sensitive": false,
    "max_results": 50
  }
}
```

### 2. `search_by_type`
Search within specific file types.

**Parameters:**
- `pattern` (string, required): Regex pattern to search
- `file_type` (string, required): File type (e.g., 'python', 'rust', 'js')
- `path` (string, optional): Directory to search in
- `exclude_type` (string, optional): File types to exclude

**Example:**
```json
{
  "tool": "search_by_type",
  "args": {
    "pattern": "async def",
    "file_type": "python",
    "path": "/workspace/src"
  }
}
```

### 3. `search_with_context`
Search with surrounding context lines.

**Parameters:**
- `pattern` (string, required): Search pattern
- `before_context` (integer, default: 2): Lines before match
- `after_context` (integer, default: 2): Lines after match
- `path` (string, optional): Search path

**Example:**
```json
{
  "tool": "search_with_context",
  "args": {
    "pattern": "error",
    "before_context": 3,
    "after_context": 3,
    "path": "/workspace/logs"
  }
}
```

### 4. `replace`
Find and preview replacements (dry-run mode).

**Parameters:**
- `pattern` (string, required): Pattern to find
- `replacement` (string, required): Replacement text
- `path` (string, optional): Target path
- `dry_run` (boolean, default: true): Preview changes without applying

**Example:**
```json
{
  "tool": "replace",
  "args": {
    "pattern": "oldFunction",
    "replacement": "newFunction",
    "path": "/workspace",
    "dry_run": true
  }
}
```

### 5. `list_files`
List files matching specified criteria.

**Parameters:**
- `pattern` (string, optional): Filter by file name pattern
- `file_type` (string, optional): Filter by file type
- `path` (string, optional): Search directory
- `include_hidden` (boolean, default: false): Include hidden files

**Example:**
```json
{
  "tool": "list_files",
  "args": {
    "pattern": "*.test.js",
    "file_type": "javascript",
    "path": "/workspace",
    "include_hidden": false
  }
}
```

### 6. `search_multiline`
Search for patterns spanning multiple lines.

**Parameters:**
- `pattern` (string, required): Multiline regex pattern
- `path` (string, optional): Search path
- `pcre2` (boolean, default: false): Use PCRE2 engine for advanced patterns

**Example:**
```json
{
  "tool": "search_multiline",
  "args": {
    "pattern": "class\\s+\\w+\\s*\\{[\\s\\S]*?constructor",
    "path": "/workspace",
    "pcre2": true
  }
}
```

### 7. `stats`
Get statistics about search operations.

**Parameters:**
- `pattern` (string, required): Pattern to analyze
- `path` (string, optional): Target path

**Example:**
```json
{
  "tool": "stats",
  "args": {
    "pattern": "import",
    "path": "/workspace"
  }
}
```

### 8. `search_binary`
Search in binary files.

**Parameters:**
- `pattern` (string, required): Pattern to search
- `path` (string, optional): Target path
- `encoding` (string, default: "utf-8"): File encoding

**Example:**
```json
{
  "tool": "search_binary",
  "args": {
    "pattern": "version",
    "path": "/workspace/build",
    "encoding": "utf-8"
  }
}
```

### 9. `health_check`
Check if ripgrep is available and working.

**Parameters:** None

**Example:**
```json
{
  "tool": "health_check",
  "args": {}
}
```

## Installation

### Prerequisites
- Python 3.12+
- ripgrep (rg) installed on the system
- UV package manager (for development)
- Docker (for containerized deployment)

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ripgrep-mcp.git
cd ripgrep-mcp
```

2. Install with UV:
```bash
uv pip install -e .
```

3. Or install with pip:
```bash
pip install -e .
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t ripgrep-mcp:latest .
```

2. Run the container:
```bash
docker run -v $(pwd):/workspace ripgrep-mcp:latest
```

## Usage

### Standalone Application

Run the MCP server directly:
```bash
python -m ripgrep_mcp.server
```

### With MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "ripgrep": {
      "command": "python",
      "args": ["-m", "ripgrep_mcp.server"],
      "env": {
        "RG_MAX_RESULTS": "1000",
        "RG_TIMEOUT": "30",
        "RG_DEFAULT_PATH": "/path/to/workspace"
      }
    }
  }
}
```

### Docker Configuration

For Docker deployment:

```json
{
  "mcpServers": {
    "ripgrep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "${PWD}:/workspace",
        "ripgrep-mcp:latest"
      ],
      "env": {
        "RG_MAX_RESULTS": "1000",
        "RG_TIMEOUT": "30"
      }
    }
  }
}
```

## Testing with MCP Inspector

MCP Inspector is a tool for testing and debugging MCP servers. Here's how to test the Ripgrep MCP Server:

### Installation

```bash
npm install -g @modelcontextprotocol/inspector
```

### Running the Inspector

1. Start the inspector:
```bash
mcp-inspector python -m ripgrep_mcp.server
```

2. The inspector will open in your browser at `http://localhost:5173`

### Testing Tools

Use these example requests in the MCP Inspector:

1. **Basic Search Test:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "pattern": "def",
      "path": ".",
      "case_sensitive": true,
      "line_numbers": true,
      "max_results": 10
    }
  }
}
```

2. **Search by File Type Test:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_by_type",
    "arguments": {
      "pattern": "class",
      "file_type": "python",
      "path": "."
    }
  }
}
```

3. **List Files Test:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "list_files",
    "arguments": {
      "file_type": "python",
      "path": ".",
      "include_hidden": false
    }
  }
}
```

4. **Health Check Test:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "health_check",
    "arguments": {}
  }
}
```

## Environment Variables

Configure the server behavior with these environment variables:

- `RG_BINARY_PATH`: Path to ripgrep binary (default: auto-detect)
- `RG_MAX_RESULTS`: Maximum results per search (default: 1000)
- `RG_TIMEOUT`: Search timeout in seconds (default: 30)
- `RG_DEFAULT_PATH`: Default search path (default: current directory)
- `RG_ALLOW_OUTSIDE_WORKSPACE`: Allow searches outside workspace (default: false)

## Development

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=ripgrep_mcp --cov-report=term-missing

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/
```

### Project Structure

```
ripgrep-mcp/
   src/
      ripgrep_mcp/
          __init__.py       # Package initialization
          server.py         # MCP server implementation
          tools.py          # Tool implementations
          validators.py     # Input/output validation
          utils.py          # Utility functions
   tests/
      test_tools.py         # Comprehensive tests
   Dockerfile                # Multi-stage Docker build
   pyproject.toml           # Project configuration
   README.md                # This file
```

## Security Considerations

- Path traversal protection with validation
- Command injection prevention using subprocess arrays
- Resource limits on search results and timeouts
- Non-root user in Docker container
- Workspace isolation by default

## Performance

The Ripgrep MCP Server inherits ripgrep's excellent performance characteristics:

- Uses Rust's regex engine for speed
- Parallel directory traversal
- Memory-mapped file access
- Smart filtering reduces search space
- Typical searches complete in milliseconds

## Troubleshooting

### Ripgrep not found

Ensure ripgrep is installed:
```bash
# Ubuntu/Debian
sudo apt-get install ripgrep

# macOS
brew install ripgrep

# Check installation
rg --version
```

### Permission denied errors

Ensure the search path is readable:
```bash
chmod -R r+X /path/to/search
```

### Timeout errors

Increase the timeout:
```bash
export RG_TIMEOUT=60
```

### Docker volume issues

Ensure proper volume mounting:
```bash
docker run -v $(pwd):/workspace:ro ripgrep-mcp:latest
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) - The amazing ripgrep tool
- [Anthropic MCP](https://github.com/anthropics/mcp) - Model Context Protocol framework
- [FastMCP](https://github.com/anthropics/fastmcp) - Fast MCP server implementation

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Consult the ripgrep documentation for search syntax