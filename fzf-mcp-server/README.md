# fzf MCP Server

MCP Server implementation for [fzf](https://github.com/junegunn/fzf) - A command-line fuzzy finder.

## Overview

This MCP server provides tools for fuzzy finding and filtering files, directories, and text content using the powerful fzf CLI tool. It enables AI agents and developers to leverage fzf's fuzzy matching capabilities for searching codebases, filtering lists, and exploring file systems.

## Features

- **Fuzzy Filtering**: Filter any list of items with fzf's fuzzy matching algorithm
- **File Search**: Find files and directories with fuzzy matching
- **Content Search**: Search for text within files and filter results
- **Line Selection**: Select specific lines from files using fuzzy matching
- **Git Integration**: Search and filter git repository files
- **Directory Browsing**: Explore directory trees with fuzzy filtering

## Prerequisites

- **Python 3.12+**
- **fzf** - Must be installed on the host system
- **uv** - For dependency management (optional, but recommended)
- **Docker** - For containerized deployment (optional)

### Installing fzf

#### Linux
```bash
# Debian/Ubuntu
sudo apt install fzf

# Fedora
sudo dnf install fzf

# Arch Linux
sudo pacman -S fzf

# From source
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

#### macOS
```bash
brew install fzf
```

## Installation

### Local Installation

1. Clone or create the project:
```bash
cd fzf-mcp-server
```

2. Create a virtual environment and install dependencies:
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. Verify installation:
```bash
python -c "import fzf_mcp_server; print(fzf_mcp_server.__version__)"
```

### Docker Installation

Build the Docker image:
```bash
docker build -t fzf-mcp-server .
```

Run the container:
```bash
docker run -i fzf-mcp-server
```

## Available Tools

### 1. fuzzy_filter

Filter a list of items using fzf's fuzzy matching algorithm.

**Arguments:**
- `items` (list[str], required): List of items to filter
- `query` (str, optional): Search query to filter items
- `exact` (bool, optional): Enable exact matching (default: false)
- `case_sensitive` (bool, optional): Enable case-sensitive matching (default: false)

**Example:**
```json
{
  "items": ["apple.py", "application.js", "app.go", "banana.py"],
  "query": "app",
  "exact": false
}
```

**Output:**
```json
{
  "selected": ["apple.py", "application.js", "app.go"],
  "count": 3,
  "query": "app",
  "status": "success"
}
```

### 2. fuzzy_find_files

Find files in a directory using fuzzy matching.

**Arguments:**
- `directory` (str, optional): Directory to search (default: ".")
- `query` (str, optional): Fuzzy search query for filenames
- `file_type` (str, optional): Type of files - "all", "file", "dir" (default: "all")
- `hidden` (bool, optional): Include hidden files (default: false)
- `follow_symlinks` (bool, optional): Follow symbolic links (default: true)
- `max_depth` (int, optional): Maximum directory depth to search
- `exact` (bool, optional): Enable exact matching (default: false)

**Example:**
```json
{
  "directory": "/home/user/project",
  "query": "test",
  "file_type": "file",
  "hidden": false,
  "max_depth": 3
}
```

### 3. fuzzy_search_content

Search for content within files and filter results with fuzzy matching.

**Arguments:**
- `directory` (str, optional): Directory to search (default: ".")
- `search_pattern` (str, required): Pattern to search for in files
- `file_pattern` (str, optional): File pattern to search (default: "*")
- `query` (str, optional): Additional fuzzy query to filter results
- `case_sensitive` (bool, optional): Case-sensitive search (default: false)
- `max_results` (int, optional): Maximum results to return (default: 1000)

**Example:**
```json
{
  "directory": "/home/user/project",
  "search_pattern": "def main",
  "file_pattern": "*.py",
  "query": "server"
}
```

### 4. fuzzy_select_lines

Select lines from a file using fuzzy matching.

**Arguments:**
- `file_path` (str, required): Path to the file to read
- `query` (str, optional): Fuzzy search query for filtering lines
- `line_range` (str, optional): Line range to read (e.g., "1-100", "50-", "-100")
- `exact` (bool, optional): Enable exact matching (default: false)

**Example:**
```json
{
  "file_path": "/var/log/application.log",
  "query": "ERROR",
  "line_range": "1-1000"
}
```

### 5. fuzzy_git_files

Find and filter git repository files using fuzzy matching.

**Arguments:**
- `repository` (str, optional): Path to git repository (default: ".")
- `query` (str, optional): Fuzzy search query for filenames
- `staged_only` (bool, optional): Only show staged files (default: false)
- `modified_only` (bool, optional): Only show modified files (default: false)
- `untracked` (bool, optional): Include untracked files (default: false)

**Example:**
```json
{
  "repository": "/home/user/project",
  "query": "server",
  "modified_only": true
}
```

### 6. fuzzy_directory_tree

Browse directory tree with fuzzy filtering.

**Arguments:**
- `directory` (str, optional): Root directory to browse (default: ".")
- `query` (str, optional): Fuzzy search query for filtering paths
- `max_depth` (int, optional): Maximum depth of tree (default: 3)
- `show_hidden` (bool, optional): Include hidden files (default: false)

**Example:**
```json
{
  "directory": "/home/user/project",
  "query": "src",
  "max_depth": 4,
  "show_hidden": false
}
```

## Running the Server

### Standalone Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python -m fzf_mcp_server.server
```

### With MCP Inspector

To test the server with MCP Inspector:

1. Install MCP Inspector:
```bash
npx @modelcontextprotocol/inspector
```

2. Run the server with inspector:
```bash
# In one terminal, start the server
python -m fzf_mcp_server.server

# In another terminal, use the inspector
npx @modelcontextprotocol/inspector python -m fzf_mcp_server.server
```

3. Open the provided URL in your browser to interact with the tools.

### Docker Mode

```bash
# Build the image
docker build -t fzf-mcp-server .

# Run the container
docker run -i fzf-mcp-server
```

For Docker with volume mounts (to access host files):
```bash
docker run -i -v /path/to/search:/workspace fzf-mcp-server
```

## MCP Client Configuration

### Standalone Application

Add this configuration to your MCP client settings:

```json
{
  "mcpServers": {
    "fzf": {
      "command": "python",
      "args": ["-m", "fzf_mcp_server.server"],
      "env": {}
    }
  }
}
```

With absolute path to virtual environment:
```json
{
  "mcpServers": {
    "fzf": {
      "command": "/absolute/path/to/fzf-mcp-server/.venv/bin/python",
      "args": ["-m", "fzf_mcp_server.server"],
      "env": {}
    }
  }
}
```

### Docker Container

```json
{
  "mcpServers": {
    "fzf": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/search:/workspace",
        "fzf-mcp-server"
      ],
      "env": {}
    }
  }
}
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "fzf": {
      "command": "/absolute/path/to/fzf-mcp-server/.venv/bin/python",
      "args": ["-m", "fzf_mcp_server.server"]
    }
  }
}
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Use Cases

### 1. Finding Files in a Codebase
Use `fuzzy_find_files` to quickly locate files when you only remember part of the filename.

### 2. Searching Code
Use `fuzzy_search_content` to find where specific functions, classes, or patterns appear in your code.

### 3. Filtering Log Files
Use `fuzzy_select_lines` to extract relevant lines from large log files.

### 4. Git Workflow
Use `fuzzy_git_files` to find modified or staged files in your repository.

### 5. Exploring Projects
Use `fuzzy_directory_tree` to understand project structure and navigate directories.

### 6. AI Context Management
All tools return structured results that can be used to update AI model context with relevant file information.

## Error Handling

All tools return JSON responses with error information when issues occur:

```json
{
  "error": "Error message describing what went wrong",
  "selected": [],
  "count": 0
}
```

Common errors:
- `fzf is not installed`: fzf binary not found in PATH
- `Path does not exist`: Invalid directory or file path
- `Not a file`: Attempted to read a directory as a file
- `Git command failed`: Repository not found or invalid git operation

## Limitations

- The server runs fzf in filter mode (non-interactive) for programmatic access
- Preview windows and interactive features of fzf are not available via MCP
- File operations are limited to read-only access
- Maximum results are limited to prevent memory issues with large result sets

## Development

### Project Structure
```
fzf-mcp-server/
├── src/
│   └── fzf_mcp_server/
│       ├── __init__.py
│       └── server.py
├── tests/
│   └── test_server.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [fzf](https://github.com/junegunn/fzf) by Junegunn Choi - The amazing fuzzy finder this server is built upon
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that enables AI integration

## Support

For issues and questions:
- fzf issues: https://github.com/junegunn/fzf/issues
- MCP Server issues: Create an issue in this repository

## Version

Current version: 0.1.0
