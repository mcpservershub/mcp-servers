# Makefile MCP Server

An MCP (Model Context Protocol) server that provides intelligent tools for working with Makefiles using the `make` CLI as its backend.

## Features

This MCP server provides the following high-impact tools for Makefile development:

### Core Tools

- **`list_targets`** - List all available targets in a Makefile with their dependencies and phony status
- **`execute_target`** - Execute specific make targets with support for variables, parallel execution, and dry-run mode
- **`analyze_dependencies`** - Analyze target dependencies, detect circular dependencies, and visualize the dependency tree
- **`dry_run`** - Preview commands that would be executed without actually running them
- **`show_variables`** - Display all variables defined in the Makefile with pattern filtering
- **`validate_makefile`** - Validate Makefile syntax and detect common issues
- **`clean_build`** - Execute the clean target to remove build artifacts

## Installation

### Using pip

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Using Docker

```bash
# Build the Docker image
docker build -t makefile-mcp .

# Run the container
docker run -it --rm -v $(pwd):/workspace makefile-mcp
```

## Testing with MCP Inspector

1. Install MCP Inspector:
```bash
npm install -g @modelcontextprotocol/inspector
```

2. Run the MCP server:
```bash
# From the project directory
mcp-inspector python makefile_mcp.py
```

3. Open your browser to the URL shown by MCP Inspector (typically http://localhost:5173)

4. Test the tools using the Inspector interface

## MCP Configuration

### Standalone Application Configuration

Add to your MCP client configuration file:

```json
{
  "mcpServers": {
    "makefile-mcp": {
      "command": "python",
      "args": ["/path/to/makefile_mcp.py"],
      "transport": "stdio"
    }
  }
}
```

### Docker Configuration

```json
{
  "mcpServers": {
    "makefile-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "${workspaceFolder}:/workspace",
        "makefile-mcp"
      ],
      "transport": "stdio"
    }
  }
}
```

### Claude Desktop Configuration

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "makefile-mcp": {
      "command": "python",
      "args": ["/path/to/makefile_mcp.py"]
    }
  }
}
```

## Usage Examples

### List all targets in a Makefile

```python
result = await list_targets(
    working_dir="/path/to/project",
    output_file="targets.json"  # Optional: save output to file
)
# Returns: List of targets with dependencies and phony status
# If output_file is specified, also saves results to JSON file
```

### Execute a target

```python
result = await execute_target(
    target="build",
    working_dir="/path/to/project",
    variables={"DEBUG": "1"},
    parallel=4
)
```

### Analyze dependencies

```python
result = await analyze_dependencies(
    target="all",
    working_dir="/path/to/project"
)
# Returns: Dependency tree with circular dependency detection
```

### Dry run to preview commands

```python
result = await dry_run(
    target="install",
    working_dir="/path/to/project",
    debug=True
)
```

### Validate Makefile

```python
result = await validate_makefile(
    working_dir="/path/to/project",
    makefile="custom.mk"
)
```

## Tool Parameters

### Common Parameters

- `working_dir` (Optional[str]): Directory containing the Makefile (default: current directory)
- `makefile` (Optional[str]): Name of the Makefile (default: Makefile)
- `output_file` (Optional[str]): File path to save JSON output (available for: list_targets, analyze_dependencies, show_variables, dry_run, validate_makefile)

### execute_target Parameters

- `target` (str): Target name to execute [required]
- `variables` (Optional[Dict[str, str]]): Variables to pass to make
- `dry_run` (bool): Show commands without executing
- `parallel` (Optional[int]): Number of parallel jobs
- `always_make` (bool): Unconditionally make all targets
- `keep_going` (bool): Continue after errors
- `silent` (bool): Don't echo commands

### analyze_dependencies Parameters

- `target` (Optional[str]): Specific target to analyze (default: all targets)
- `show_all` (bool): Include automatic variables and built-in rules

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python test_makefile_mcp.py
```

### Building Docker Image

```bash
# Build image
docker build -t makefile-mcp .

# Test the image
docker run -it --rm makefile-mcp
```

## Requirements

- Python 3.12+
- `make` CLI tool installed on the system
- `mcp[cli]` package

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Architecture

This MCP server follows the principle of being a thin wrapper around the `make` CLI tool. It:

1. **Does not reinvent the wheel** - Leverages make's built-in capabilities
2. **Provides structured output** - Parses make output into JSON for AI consumption
3. **Handles errors gracefully** - Validates inputs and provides clear error messages
4. **Supports all make features** - Pass-through support for make flags and options

The server uses FastMCP for easy tool creation with decorators and runs on the stdio transport for maximum compatibility.