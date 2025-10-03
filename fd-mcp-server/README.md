# fd-mcp-server

A Model Context Protocol (MCP) Server for the `fd` CLI tool - a simple, fast, and user-friendly alternative to the traditional `find` command.

## Overview

This MCP server enables developers and AI agents to leverage the power of `fd` for fuzzy file and directory searching. It provides a rich set of tools for finding files based on patterns, extensions, types, sizes, modification times, and more.

### Key Features

- **Fast Search**: Leverages fd's parallel directory traversal
- **Flexible Filtering**: Search by pattern, extension, type, size, and time
- **Smart Defaults**: Case-insensitive search with .gitignore support
- **Rich Options**: Hidden files, symlinks, depth control, and exclusions
- **Command Execution**: Execute commands on search results
- **Production Ready**: Docker support with multi-stage builds

## Prerequisites

- Python 3.12+
- `fd` or `fd-find` installed on the system
- `uv` for package management (optional but recommended)

### Installing fd

**Ubuntu/Debian:**
```bash
apt install fd-find
# Create symlink if needed
ln -s $(which fdfind) ~/.local/bin/fd
```

**macOS:**
```bash
brew install fd
```

**Other platforms:** See [fd installation guide](https://github.com/sharkdp/fd#installation)

## Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .

# For development
uv pip install -e ".[dev]"
```

### Using pip

```bash
pip install -e .
```

## Running the MCP Server

### Standalone

```bash
# Run directly
python -m src.fd_mcp_server

# Or using the installed package
python src/fd_mcp_server.py
```

### With Docker

**Build the image:**
```bash
docker build -t fd-mcp-server .
```

**Run the container:**
```bash
docker run -i --rm fd-mcp-server
```

**Run with volume mount (to search host files):**
```bash
docker run -i --rm -v /path/to/search:/workspace fd-mcp-server
```

## Testing

### Run Tests

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_fd_mcp_server.py -v
```

## MCP Configuration

### For Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fd-search": {
      "command": "python",
      "args": ["/absolute/path/to/fuzzy/src/fd_mcp_server.py"]
    }
  }
}
```

### With Docker

```json
{
  "mcpServers": {
    "fd-search": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/search:/workspace",
        "fd-mcp-server"
      ]
    }
  }
}
```

### For Other MCP Clients

```json
{
  "mcpServers": {
    "fd-search": {
      "command": "python",
      "args": ["-m", "src.fd_mcp_server"],
      "cwd": "/absolute/path/to/fuzzy"
    }
  }
}
```

## Available Tools

### 1. `fd_search`

Main search tool with comprehensive options.

**Arguments:**
- `pattern` (optional): Search pattern (regex by default, glob if `glob=True`)
- `path` (optional): Root directory for search
- `hidden` (bool): Include hidden files and directories
- `no_ignore` (bool): Don't respect .gitignore files
- `case_sensitive` (bool): Force case-sensitive search
- `ignore_case` (bool): Force case-insensitive search
- `glob` (bool): Use glob-based search instead of regex
- `absolute_path` (bool): Show absolute paths
- `follow_symlinks` (bool): Follow symbolic links
- `full_path` (bool): Match pattern against full path
- `max_depth` (int): Maximum search depth
- `type_filter` (str): Filter by type (f/file, d/dir, l/symlink, x/executable, e/empty)
- `extension` (str): Filter by file extension
- `size` (str): Filter by size (e.g., '+10k', '-1m')
- `max_results` (int): Limit number of results

**Example:**
```json
{
  "pattern": "test.*\\.py$",
  "path": "/workspace",
  "extension": "py",
  "max_depth": 3
}
```

### 2. `fd_search_by_extension`

Search for files with specific extensions.

**Arguments:**
- `extension` (required): File extension (e.g., 'py', 'md', 'txt')
- `path` (optional): Root directory
- `pattern` (optional): Additional pattern to match
- `hidden` (bool): Include hidden files
- `no_ignore` (bool): Don't respect .gitignore

**Example:**
```json
{
  "extension": "py",
  "path": "/workspace",
  "pattern": "test"
}
```

### 3. `fd_search_by_type`

Search by file type.

**Arguments:**
- `type_filter` (required): Type - 'f' (file), 'd' (dir), 'l' (symlink), 'x' (executable), 'e' (empty)
- `path` (optional): Root directory
- `pattern` (optional): Search pattern
- `hidden` (bool): Include hidden entries
- `max_depth` (int): Maximum depth

**Example:**
```json
{
  "type_filter": "d",
  "path": "/workspace",
  "max_depth": 2
}
```

### 4. `fd_list_all`

List all files and directories recursively.

**Arguments:**
- `path` (optional): Root directory
- `hidden` (bool): Include hidden entries
- `no_ignore` (bool): Don't respect ignore files
- `max_depth` (int): Maximum depth
- `type_filter` (str): Filter by type

**Example:**
```json
{
  "path": "/workspace",
  "max_depth": 2,
  "type_filter": "f"
}
```

### 5. `fd_exclude_pattern`

Search with exclusion patterns.

**Arguments:**
- `pattern` (optional): Search pattern
- `exclude` (list): List of glob patterns to exclude
- `path` (optional): Root directory
- `hidden` (bool): Include hidden files

**Example:**
```json
{
  "pattern": ".*",
  "exclude": ["*.pyc", "node_modules", "__pycache__"],
  "path": "/workspace"
}
```

### 6. `fd_changed_within`

Find files modified within a time period.

**Arguments:**
- `duration` (required): Time duration (e.g., '10min', '2h', '1d', '3weeks')
- `path` (optional): Root directory
- `pattern` (optional): Search pattern
- `type_filter` (str): Filter by type

**Example:**
```json
{
  "duration": "2h",
  "path": "/workspace",
  "type_filter": "f"
}
```

### 7. `fd_changed_before`

Find files modified before a time period.

**Arguments:**
- `duration` (required): Time duration (e.g., '10min', '2h', '1d', '3weeks')
- `path` (optional): Root directory
- `pattern` (optional): Search pattern
- `type_filter` (str): Filter by type

**Example:**
```json
{
  "duration": "1d",
  "path": "/workspace"
}
```

### 8. `fd_size_filter`

Find files by size.

**Arguments:**
- `size` (required): Size filter (e.g., '+10k', '-1m', '500b')
  - Prefix: '+' (larger), '-' (smaller), none (exact)
  - Units: b, k, m, g, t (or ki, mi, gi, ti for binary)
- `path` (optional): Root directory
- `pattern` (optional): Search pattern
- `extension` (str): File extension filter

**Example:**
```json
{
  "size": "+1m",
  "extension": "log",
  "path": "/workspace"
}
```

### 9. `fd_exec_command`

Execute command for search results.

**Arguments:**
- `command` (required): Command to execute (use {} for file placeholder)
- `pattern` (optional): Search pattern
- `path` (optional): Root directory
- `extension` (str): File extension filter
- `type_filter` (str): Type filter
- `batch_mode` (bool): Single command with all results vs. parallel execution

**Example:**
```json
{
  "command": "wc -l {}",
  "extension": "py",
  "path": "/workspace"
}
```

## Testing with MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a tool for testing MCP servers.

### Install MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

### Test the Server

```bash
# Start the inspector
npx @modelcontextprotocol/inspector python src/fd_mcp_server.py

# Or with uv
npx @modelcontextprotocol/inspector uv run python src/fd_mcp_server.py
```

### Example Tool Calls in Inspector

**Search for Python files:**
```json
{
  "tool": "fd_search_by_extension",
  "args": {
    "extension": "py",
    "path": "."
  }
}
```

**Find large files:**
```json
{
  "tool": "fd_size_filter",
  "args": {
    "size": "+1m",
    "path": "."
  }
}
```

**Find recently modified files:**
```json
{
  "tool": "fd_changed_within",
  "args": {
    "duration": "1h",
    "type_filter": "f"
  }
}
```

**Complex search:**
```json
{
  "tool": "fd_search",
  "args": {
    "pattern": "test_.*\\.py$",
    "path": ".",
    "hidden": false,
    "max_depth": 3,
    "type_filter": "f"
  }
}
```

## Use Cases

### For Developers

- **Quick File Discovery**: Find files matching patterns across large codebases
- **Code Analysis**: Locate specific file types for analysis
- **Build Systems**: Find changed files for incremental builds
- **Cleanup**: Find old or large files for cleanup

### For AI Agents

- **Context Gathering**: Search for relevant files to include in LLM context
- **Codebase Understanding**: Discover project structure and file organization
- **Targeted Analysis**: Find specific files for code review or refactoring
- **Dynamic Workflows**: Adapt search based on project characteristics

## Architecture

```
fd-mcp-server/
├── src/
│   ├── __init__.py
│   └── fd_mcp_server.py      # Main MCP server implementation
├── tests/
│   ├── __init__.py
│   └── test_fd_mcp_server.py # Comprehensive test suite
├── pyproject.toml             # Project configuration
├── Dockerfile                 # Multi-stage Docker build
├── .dockerignore
└── README.md
```

## Error Handling

All tools return JSON with the following structure:

```json
{
  "success": true,
  "return_code": 0,
  "results": ["file1.py", "file2.py"],
  "error": null,
  "command": "fd --extension py ."
}
```

On error:

```json
{
  "success": false,
  "return_code": 1,
  "results": [],
  "error": "Error message here",
  "command": "fd invalid_command"
}
```

## Performance Tips

1. **Limit Depth**: Use `max_depth` to avoid deep traversals
2. **Use Type Filters**: Filter by type (file/dir) to reduce results
3. **Leverage .gitignore**: Let fd skip ignored directories (default behavior)
4. **Limit Results**: Use `max_results` for faster response when you only need a few matches
5. **Be Specific**: More specific patterns = faster searches

## Troubleshooting

### fd not found

**Error**: "fd is not installed"

**Solution**: Install fd-find and ensure it's in PATH:
```bash
# Ubuntu/Debian
apt install fd-find
ln -s $(which fdfind) ~/.local/bin/fd

# macOS
brew install fd
```

### Permission Denied

**Issue**: Some directories return permission errors

**Solution**: Use Docker with appropriate user permissions or run with necessary privileges

### No Results Found

**Issue**: Search returns empty results

**Solution**:
- Check if fd is respecting .gitignore (use `no_ignore: true`)
- Include hidden files with `hidden: true`
- Verify the path is correct
- Test pattern with `fd` command directly

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest`
2. Code follows Python best practices
3. New tools include tests
4. Documentation is updated

## License

MIT License - See LICENSE file for details

## Links

- [fd GitHub Repository](https://github.com/sharkdp/fd)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)

## Support

For issues and questions:
- fd-related: [fd issues](https://github.com/sharkdp/fd/issues)
- MCP server issues: Open an issue in this repository