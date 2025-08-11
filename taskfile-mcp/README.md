# Taskfile MCP Server

A lightweight MCP (Model Context Protocol) server for Taskfile development, providing a clean interface to the Task CLI through AI assistants.

## Features

The Taskfile MCP Server provides essential tools for working with Taskfiles by wrapping the `task` CLI:

### Core Tools

1. **`list_tasks`** - List all available tasks in a Taskfile
   - Supports custom taskfile names (not just Taskfile.yml)
   - JSON or text output formats

2. **`run_task`** - Execute tasks with full CLI flag support
   - Dry-run, watch mode, parallel execution
   - Force, silent, and verbose modes

3. **`init_taskfile`** - Initialize a new Taskfile in any directory

4. **`validate_taskfile`** - Validate Taskfile syntax and structure

5. **`get_task_summary`** - Get detailed information about specific tasks

6. **`dry_run`** - Preview task execution without running commands

7. **`watch_task`** - Run tasks in watch mode with file monitoring

## Prerequisites

- Python 3.12 or higher
- Task CLI installed ([Installation Guide](https://taskfile.dev/installation))

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/taskfile-mcp.git
cd taskfile-mcp

# Create virtual environment and install
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Using Docker

```bash
# Build the Docker image
docker build -t taskfile-mcp:latest .

# Run the container
docker run --rm -it -v $(pwd):/workspace taskfile-mcp:latest
```

## Usage

### Running the Server

```bash
# With virtual environment
.venv/bin/python -m src.server

# Or if installed globally
taskfile-mcp
```

### Tool Parameters

#### list_tasks
```python
{
    "working_dir": "/path/to/project",  # Optional: directory containing Taskfile
    "taskfile": "custom.yml",           # Optional: specific taskfile name
    "json_output": True,                # Optional: JSON (True) or text (False)
    "output_file": "tasks.json"         # Optional: save output to file
}
```

#### run_task
```python
{
    "task_name": "build",               # Required: task to execute
    "working_dir": "/path/to/project",  # Optional: directory containing Taskfile
    "taskfile": "custom.yml",           # Optional: specific taskfile name
    "dry_run": False,                   # Optional: preview without executing
    "watch": False,                     # Optional: watch mode
    "parallel": False,                  # Optional: parallel execution
    "force": False,                     # Optional: force execution
    "silent": False,                    # Optional: suppress output
    "verbose": False                    # Optional: verbose output
}
```

#### Other Tools
- **init_taskfile**: `{"working_dir": "/path/to/new/project"}`
- **validate_taskfile**: `{"working_dir": "/path/to/project"}`
- **get_task_summary**: `{"task_name": "test", "working_dir": "/path"}`
- **dry_run**: `{"task_name": "build", "working_dir": "/path"}`
- **watch_task**: `{"task_name": "dev", "working_dir": "/path"}`

## MCP Configuration

### For Claude Desktop

Add to your configuration file:

**Linux/Mac:** `~/.config/claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "taskfile": {
      "command": "/path/to/taskfile-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Docker Configuration

```json
{
  "mcpServers": {
    "taskfile": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/your/project:/workspace",
        "taskfile-mcp:latest"
      ]
    }
  }
}
```

## Testing

### Direct Testing

```bash
# Test all tools
.venv/bin/python test_tools.py

# Simple test
.venv/bin/python test_server.py
```

### With MCP Inspector

1. Install MCP Inspector:
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. Start the inspector:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

3. Connect to the server:
   - Command: `/path/to/.venv/bin/python`
   - Arguments: `-m` and `src.server`

## Examples

### Working with Custom Taskfiles

```python
# List tasks from a custom taskfile
await list_tasks(
    working_dir="/project",
    taskfile="ci-tasks.yml",
    json_output=True
)

# Save task list to a file for documentation
await list_tasks(
    working_dir="/project",
    taskfile="ci-tasks.yml",
    json_output=True,
    output_file="available-tasks.json"
)

# Run a task from a specific taskfile
await run_task(
    task_name="deploy",
    working_dir="/project",
    taskfile="deploy.yml",
    dry_run=True
)
```

### Common Workflows

```python
# Initialize and validate a new project
await init_taskfile(working_dir="/new-project")
await validate_taskfile(working_dir="/new-project")

# Debug a task
await dry_run(task_name="build", working_dir="/project")
await get_task_summary(task_name="build", working_dir="/project")

# Watch for changes
await watch_task(task_name="test", working_dir="/project")
```

## Architecture

This MCP server is intentionally minimal, acting as a thin wrapper around the Task CLI:

```
┌─────────────┐     ┌─────────────┐     ┌──────────┐
│ AI Assistant│────▶│  MCP Server │────▶│ Task CLI │
└─────────────┘     └─────────────┘     └──────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Taskfile   │
                    └─────────────┘
```

## Dependencies

- **mcp[cli]**: MCP protocol implementation
- **Task CLI**: External binary (must be installed separately)

## Troubleshooting

### Task CLI Not Found
Install Task from https://taskfile.dev/installation

### Permission Errors
Ensure the Task binary is executable and in PATH

### Connection Issues
Verify Python path and MCP server startup

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Acknowledgments

- [Task](https://taskfile.dev) - Modern task runner
- [MCP](https://modelcontextprotocol.io) - Model Context Protocol