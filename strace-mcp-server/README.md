# strace MCP Server

A Model Context Protocol (MCP) server that provides programmatic access to the Linux `strace` system call tracer. This server enables AI assistants and other applications to trace and analyze system calls for debugging, performance analysis, and security auditing.

## Features

- **System Call Tracing**: Trace system calls made by new or existing processes
- **Process Attachment**: Attach to running processes by PID
- **Statistical Analysis**: Generate summary statistics of system call usage
- **Specialized Filters**: Focus on specific syscall categories (file, network, process, memory, etc.)
- **File Operations Tracking**: Monitor file system interactions
- **Network Activity Monitoring**: Trace network-related system calls

## Installation

### Prerequisites

- Python 3.11+
- Linux operating system with `strace` installed
- `uv` package manager

### Install strace (if not already installed)

```bash
# Ubuntu/Debian
sudo apt-get install strace

# Fedora/RHEL
sudo dnf install strace

# Arch Linux
sudo pacman -S strace
```

### Install the MCP Server

```bash
# Clone the repository
git clone <repository-url>
cd strace-mcp-server

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

## Available Tools

### 1. `trace_command`
Trace system calls of a new command.

**Parameters:**
- `command` (str): Command to execute and trace
- `args` (list): Command arguments
- `trace_filter` (str): Filter type (all, file, network, process, memory, signal, ipc, desc)
- `follow_forks` (bool): Follow child processes
- `max_string_size` (int): Maximum string size to capture
- `timeout` (int): Timeout in seconds
- `show_timestamps` (bool): Include timestamps

**Example:**
```json
{
  "command": "ls",
  "args": ["-la", "/tmp"],
  "trace_filter": "file",
  "timeout": 10
}
```

### 2. `trace_process`
Attach to and trace an existing process.

**Parameters:**
- `pid` (int): Process ID to attach to
- `duration` (int): Duration to trace in seconds
- `trace_filter` (str): Filter type
- `follow_children` (bool): Follow child processes
- `show_timestamps` (bool): Include timestamps

**Example:**
```json
{
  "pid": 1234,
  "duration": 5,
  "trace_filter": "network"
}
```

### 3. `analyze_syscalls`
Generate statistical analysis of system calls.

**Parameters:**
- `command` (str): Command to analyze
- `args` (list): Command arguments
- `sort_by` (str): Sort by (time, calls, errors, syscall)
- `show_errors_only` (bool): Only show failed syscalls
- `timeout` (int): Timeout in seconds

**Example:**
```json
{
  "command": "find",
  "args": ["/", "-name", "*.txt"],
  "sort_by": "calls",
  "timeout": 30
}
```

### 4. `trace_file_operations`
Specialized tool for tracing file system operations.

**Parameters:**
- `command` (str): Command to trace
- `args` (list): Command arguments
- `path_filter` (str): Optional path to filter
- `show_reads` (bool): Include read operations
- `show_writes` (bool): Include write operations
- `timeout` (int): Timeout in seconds

**Example:**
```json
{
  "command": "cat",
  "args": ["/etc/passwd"],
  "show_reads": true,
  "show_writes": false
}
```

### 5. `trace_network_activity`
Monitor network-related system calls.

**Parameters:**
- `command` (str): Command to trace
- `args` (list): Command arguments
- `show_data` (bool): Show data transferred
- `timeout` (int): Timeout in seconds

**Example:**
```json
{
  "command": "curl",
  "args": ["https://example.com"],
  "show_data": true
}
```

### 6. `list_available_filters`
List all available trace filters and their descriptions.

**Example:**
```json
{}
```

## Usage

### Running the Server

```bash
# Using uv
uv run mcp start

# Or directly
python -m strace_mcp.server
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run the inspector
npx @modelcontextprotocol/inspector uv run mcp start
```

### MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "strace": {
      "command": "uv",
      "args": ["run", "mcp", "start"],
      "cwd": "/path/to/strace-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/strace-mcp-server/src"
      }
    }
  }
}
```

### Docker Usage

Build and run with Docker:

```dockerfile
FROM python:3.11-slim

# Install strace
RUN apt-get update && apt-get install -y strace && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync

# Run the server
CMD ["uv", "run", "mcp", "start"]
```

Build and run:
```bash
docker build -t strace-mcp .
docker run --cap-add SYS_PTRACE --pid=host strace-mcp
```

**Note:** The `--cap-add SYS_PTRACE` flag is required for strace to work in Docker.

## Use Cases

### Debugging File Access Issues
```python
# Trace all file operations of a command
result = await trace_file_operations(
    command="myapp",
    path_filter="/etc/config",
    show_reads=True,
    show_writes=True
)
```

### Performance Analysis
```python
# Analyze syscall statistics
stats = await analyze_syscalls(
    command="python",
    args=["script.py"],
    sort_by="time"
)
```

### Network Debugging
```python
# Monitor network activity
trace = await trace_network_activity(
    command="wget",
    args=["https://example.com/file.zip"],
    show_data=True
)
```

### Security Auditing
```python
# Trace a suspicious process
result = await trace_process(
    pid=suspect_pid,
    duration=60,
    trace_filter="all"
)
```

## Security Considerations

- **Permissions**: Tracing processes requires appropriate permissions (usually root or CAP_SYS_PTRACE)
- **Input Validation**: All inputs are validated to prevent command injection
- **Timeouts**: All operations have configurable timeouts to prevent resource exhaustion
- **Output Limits**: Output is limited to prevent memory issues

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=strace_mcp --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/
```

## Troubleshooting

### Permission Denied
If you get permission errors when tracing processes:
- Run with sudo: `sudo uv run mcp start`
- Or add CAP_SYS_PTRACE capability to the Python executable

### strace Not Found
Install strace for your distribution (see Installation section)

### Process Not Found
Ensure the PID exists: `ps -p <pid>`

### Timeout Issues
Increase the timeout parameter or use a more specific filter to reduce output

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

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Powered by the Linux `strace` utility
- Follows Model Context Protocol specifications