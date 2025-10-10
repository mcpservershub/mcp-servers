# Tree-sitter Graph MCP Server

An MCP (Model Context Protocol) server that provides access to the `tree-sitter-graph` CLI tool for generating graphs from tree-sitter queries.

## Overview

This MCP server wraps the `tree-sitter-graph` command-line utility, allowing AI assistants to generate graph representations of code structure based on tree-sitter queries defined in `.tsg` files.

## Prerequisites

Before using this MCP server, you need to have `tree-sitter-graph` installed on your system.

### Installing tree-sitter-graph

You can install `tree-sitter-graph` using either npm or cargo:

```bash
# Using npm
npm install -g @tree-sitter/graph

# Or using cargo
cargo install tree-sitter-graph
```

## Installation

### Install from source

```bash
# Clone or navigate to the project directory
cd tree-sitter-graph-mcp

# Install the package
pip install -e .
```

## Usage

### Running the server

```bash
tree-sitter-graph-mcp
```

### Using with Claude Desktop

Add the following to your Claude Desktop configuration file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tree-sitter-graph": {
      "command": "python",
      "args": ["-m", "tree_sitter_graph_mcp.server"]
    }
  }
}
```

Or if you installed it globally:

```json
{
  "mcpServers": {
    "tree-sitter-graph": {
      "command": "tree-sitter-graph-mcp"
    }
  }
}
```

## Available Tools

### tree_sitter_graph

Generate a graph using the tree-sitter-graph CLI tool.

**Parameters:**
- `tsg_file` (str): Path to the .tsg file containing tree-sitter queries for graph generation, OR the TSG content itself if `create_temp_files` is True
- `source_file` (str): Path to the source code file to analyze, OR the source code content if `create_temp_files` is True  
- `output_file` (str): Path where the JSON graph output will be saved
- `create_temp_files` (bool, optional): If True, `tsg_file` and `source_file` are treated as content strings and temporary files will be created

**Example with file paths:**
```python
result = await tree_sitter_graph(
    tsg_file="./queries.tsg",
    source_file="./code.js",
    output_file="./graph.json"
)
```

**Example with content strings:**
```python
result = await tree_sitter_graph(
    tsg_file="(program) @root",
    source_file="console.log('hello');",
    output_file="./graph.json",
    create_temp_files=True
)
```

## TSG File Format

TSG (Tree-sitter Graph) files define how to create graphs from tree-sitter parse trees. They use tree-sitter query syntax with special graph construction directives.

Example `.tsg` file:

```tsg
; Define nodes for functions
(function_declaration
  name: (identifier) @func_name) @func_node
{
  node @func_node
  attribute @func_node.label = @func_name
}

; Define edges for function calls
(call_expression
  function: (identifier) @callee) @call_site
{
  edge @call_site -> @callee
}
```

## Development

### Setting up development environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Code formatting

```bash
# Format code
black src/

# Check linting
ruff check src/
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) - The parsing library
- [tree-sitter-graph](https://github.com/tree-sitter/tree-sitter-graph) - The graph generation CLI tool
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol specification