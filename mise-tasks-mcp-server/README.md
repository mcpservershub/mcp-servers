# mise-tasks-mcp

MCP (Model Context Protocol) server for mise tasks and configuration management.

## Overview

This MCP server provides a focused set of tools for managing mise environments, tasks, and configuration through a standardized API interface.

## Tools

### Environment Management
- `set_env` - Set environment variables in mise
- `get_env` - Get environment variable values
- `unset_env` - Remove environment variables

### Task Management
- `task_run` - Execute mise tasks with optional arguments
- `task_ls` - List available tasks
- `task_info` - Get detailed information about a specific task
- `task_edit` - Open a task for editing
- `task_deps` - List task dependencies

### Configuration
- `get_config` - Retrieve mise configuration values
- `current_config` - Show current configuration sources

### Utilities
- `self_update` - Update mise to the latest or specified version
- `fmt_config` - Format mise configuration files

## Installation

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

### Using Docker

```bash
# Build standard image
docker build -t mise-tasks-mcp .

# Or build with Chainguard base (more secure, smaller)
docker build -f Dockerfile.cgr -t mise-tasks-mcp:cgr .

# Run container
docker run -it mise-tasks-mcp
```

## Development

### Setup

```bash
# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mise_tasks_mcp

# Run specific test file
pytest tests/test_server.py
pytest tests/test_edge_cases.py
```

### Project Structure

```
mise-tasks-mcp/
├── src/
│   └── mise_tasks_mcp/
│       ├── __init__.py
│       ├── server.py          # Main MCP server implementation
│       └── utils/
│           ├── __init__.py
│           ├── command.py     # Command execution utilities
│           └── validator.py   # Input validation utilities
├── tests/
│   ├── test_server.py        # Main server tests
│   └── test_edge_cases.py    # Edge case and security tests
├── Dockerfile                 # Standard Docker image
├── Dockerfile.cgr            # Chainguard-based Docker image
├── pyproject.toml            # Package configuration
└── README.md
```

## Security

This implementation includes several security features:

- **Input Validation**: All user inputs are validated to prevent injection attacks
- **Command Injection Prevention**: Special characters are properly escaped
- **Non-root Execution**: Docker containers run as non-root user
- **Minimal Docker Images**: Chainguard base image option for reduced attack surface

## Requirements

- Python 3.12+
- mise CLI installed and available in PATH
- FastMCP library (mcp[cli])

## License

MIT License - See LICENSE file for details.

Copyright (c) 2024 Capten.ai and Contributors