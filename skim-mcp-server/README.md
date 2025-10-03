# Skim MCP Server

A Model Context Protocol (MCP) server implementation for the [skim](https://github.com/skim-rs/skim) (`sk`) fuzzy finder CLI tool. This server enables AI agents and Large Language Models to perform fuzzy finding operations on files and text content, enriching their context with search results from codebases and file systems.

## Features

- **Fuzzy File Finding**: Search for files in directories with fuzzy matching
- **Content Search**: Search within file contents using ripgrep/ag/grep
- **Git Integration**: Specialized fuzzy finding for Git repositories
- **Line Filtering**: Filter any line-based text input
- **Interactive Search**: Dynamic command execution based on queries
- **Rich Previews**: Optional file and content previews using bat
- **Flexible Options**: Support for regex, exact matching, field selection, and more

## Available Tools

### 1. `fuzzy_find_files`

Fuzzy find files in a directory using fd and sk.

**Arguments:**
- `directory` (string, default: "."): Directory to search in
- `query` (string, default: ""): Initial search query
- `multi` (boolean, default: true): Enable multi-selection
- `preview` (boolean, default: true): Show file preview
- `file_types` (string, optional): Comma-separated file extensions (e.g., "py,js,rs")
- `exclude_patterns` (string, optional): Comma-separated patterns to exclude
- `max_depth` (integer, optional): Maximum directory depth to search
- `follow_symlinks` (boolean, default: false): Follow symbolic links
- `hidden` (boolean, default: false): Include hidden files

**Example:**
```json
{
  "directory": "/home/user/project",
  "query": "config",
  "file_types": "py,yaml,json",
  "preview": true
}
```

### 2. `fuzzy_search_content`

Search within file contents using ripgrep/ag/grep and sk.

**Arguments:**
- `directory` (string, default: "."): Directory to search in
- `query` (string, default: ""): Initial search query
- `multi` (boolean, default: true): Enable multi-selection
- `preview` (boolean, default: true): Show file preview with context
- `file_types` (string, optional): Comma-separated file extensions
- `case_sensitive` (boolean, default: false): Case-sensitive search
- `fixed_strings` (boolean, default: false): Treat query as literal string
- `context_lines` (integer, default: 2): Number of context lines to show

**Example:**
```json
{
  "directory": "/home/user/project",
  "query": "def main",
  "file_types": "py",
  "context_lines": 3
}
```

### 3. `fuzzy_filter_lines`

Fuzzy filter lines from input text.

**Arguments:**
- `input_text` (string, required): Text input to filter (newline-separated)
- `query` (string, default: ""): Initial search query
- `multi` (boolean, default: true): Enable multi-selection
- `exact` (boolean, default: false): Use exact matching
- `regex` (boolean, default: false): Use regex matching mode
- `case_sensitive` (boolean, default: false): Case-sensitive matching
- `delimiter` (string, optional): Field delimiter for structured data
- `nth` (string, optional): Select specific fields to search (e.g., "1,3" or "2..")

**Example:**
```json
{
  "input_text": "line1\nline2\nline3\nline4",
  "query": "line",
  "exact": false
}
```

### 4. `fuzzy_select_git_files`

Fuzzy select Git-tracked files.

**Arguments:**
- `query` (string, default: ""): Initial search query
- `multi` (boolean, default: true): Enable multi-selection
- `preview` (boolean, default: true): Show file preview
- `untracked` (boolean, default: false): Include untracked files
- `ignored` (boolean, default: false): Include ignored files

**Example:**
```json
{
  "query": "test",
  "untracked": true
}
```

### 5. `interactive_search`

Interactive search mode - run command dynamically based on query.

**Arguments:**
- `command` (string, required): Command to execute (use {} as placeholder for query)
- `query` (string, default: ""): Initial search query
- `multi` (boolean, default: true): Enable multi-selection
- `preview` (string, optional): Preview command
- `preview_window` (string, default: "right:50%:wrap"): Preview window configuration
- `ansi` (boolean, default: true): Parse ANSI color codes

**Example:**
```json
{
  "command": "rg --color=always --line-number '{}' .",
  "query": "main",
  "preview": "bat --color=always {}"
}
```

## Installation

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- `sk` (skim) CLI tool (will be installed in Docker)

### Local Installation

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone or create the project**:
```bash
cd skim-mcp-server
```

3. **Install dependencies**:
```bash
uv pip install -e .
```

4. **Install skim** (on your host system):

On Alpine Linux:
```bash
apk add skim
```

On macOS:
```bash
brew install sk
```

On other systems, see the [skim installation guide](https://github.com/skim-rs/skim#installation).

### Docker Installation

Build the Docker image:
```bash
docker build -t skim-mcp-server .
```

The Docker image includes:
- Python 3.12
- skim (sk) built from source
- fd, ripgrep, bat, and git for enhanced functionality

## Usage

### Running Locally

Run the MCP server directly:
```bash
python -m skim_mcp_server.server
```

Or if installed:
```bash
skim-mcp-server
```

### Running with Docker

```bash
docker run -i --rm \
  -v "$(pwd)":/workspace \
  skim-mcp-server
```

### Testing with MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a great tool for testing MCP servers.

1. **Install MCP Inspector**:
```bash
npx @modelcontextprotocol/inspector
```

2. **Run the inspector** with your server:

For local testing:
```bash
npx @modelcontextprotocol/inspector python -m skim_mcp_server.server
```

For Docker testing:
```bash
npx @modelcontextprotocol/inspector docker run -i --rm -v "$(pwd)":/workspace skim-mcp-server
```

3. **Test the tools** in the Inspector UI:

Example test for `fuzzy_find_files`:
```json
{
  "directory": ".",
  "query": "test",
  "file_types": "py"
}
```

Example test for `fuzzy_search_content`:
```json
{
  "directory": ".",
  "query": "def",
  "file_types": "py"
}
```

Example test for `fuzzy_filter_lines`:
```json
{
  "input_text": "apple\nbanana\ncherry\napricot",
  "query": "ap"
}
```

## MCP Configuration

### Standalone Application Configuration

Add to your MCP client configuration file (e.g., `mcp.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "skim": {
      "command": "python",
      "args": ["-m", "skim_mcp_server.server"],
      "env": {}
    }
  }
}
```

### Docker Container Configuration

```json
{
  "mcpServers": {
    "skim": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "${workspaceFolder}:/workspace",
        "skim-mcp-server"
      ],
      "env": {}
    }
  }
}
```

### Claude Desktop Configuration

For Claude Desktop on macOS:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

For Claude Desktop on Linux:
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

Add the configuration:
```json
{
  "mcpServers": {
    "skim-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/your/workspace:/workspace",
        "skim-mcp-server"
      ]
    }
  }
}
```

## Development

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/skim_mcp_server --cov-report=html
```

### Project Structure

```
skim-mcp-server/
├── src/
│   └── skim_mcp_server/
│       ├── __init__.py
│       └── server.py          # Main MCP server implementation
├── tests/
│   └── test_server.py         # Test suite
├── Dockerfile                 # Multi-stage Docker build
├── .dockerignore
├── .gitignore
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## Dependencies

### Python Dependencies
- `mcp[cli]>=1.0.0` - Model Context Protocol with CLI support (includes FastMCP)

### Optional System Dependencies (Recommended)
- `fd` - Fast file finder (fallback to `find`)
- `ripgrep` (rg) - Fast content search (fallback to `ag` or `grep`)
- `bat` - Enhanced file preview (fallback to `cat`)
- `git` - For Git repository operations

## Troubleshooting

### sk not found

If you get "sk is not installed" error:

1. **Check if sk is in PATH**:
```bash
which sk
sk --version
```

2. **Install skim**:
   - See [skim installation guide](https://github.com/skim-rs/skim#installation)
   - Or use the Docker image which includes sk

### Docker build fails

If the Docker build fails at the skim build stage:

1. **Check Docker resources**: Ensure Docker has enough memory (at least 2GB)
2. **Check network**: The build needs to download Rust crates
3. **Try building with more verbose output**:
```bash
docker build --progress=plain -t skim-mcp-server .
```

### Skim interactive mode issues

The server uses `--no-mouse` flag by default as skim runs in non-interactive subprocess mode. The tools provide selections via return values rather than interactive UI.

## License

This project is provided as-is for use with the skim fuzzy finder tool. Please refer to the [skim project license](https://github.com/skim-rs/skim/blob/master/LICENSE) for skim-specific licensing.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Links

- [Skim (sk) Repository](https://github.com/skim-rs/skim)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)

## Acknowledgments

- The skim team for creating an excellent fuzzy finder in Rust
- The MCP team at Anthropic for the Model Context Protocol
- Tools like fd, ripgrep, and bat that enhance the fuzzy finding experience