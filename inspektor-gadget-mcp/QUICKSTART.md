# Inspektor Gadget MCP Server - Quick Start

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from the directory
pip install .
```

## Running the Server

### With MCP Inspector

```bash
# Make sure you have MCP Inspector installed
npm install -g @modelcontextprotocol/inspector

# Run the server (requires sudo for ig commands)
sudo mcp-inspector python -m inspektor_gadget_mcp
```

### Direct Python Execution

```bash
# Run directly
sudo python -m inspektor_gadget_mcp
```

## Usage Examples

The simplified server provides clean, simple tools without complex validation:

### Monitor Host System (No container_name)

```python
# Monitor host processes
result = await top_resources(
    resource_type="process",
    container_name=None,  # or just omit this parameter
    duration=10
)

# Trace host network
result = await trace_network(
    trace_type="tcp",
    container_name=None
)

# Snapshot host processes
result = await snapshot_system(
    snapshot_type="process",
    container_name=None
)
```

### Monitor Specific Container

```python
# Monitor container processes
result = await top_resources(
    resource_type="process",
    container_name="my-container",
    duration=10
)

# Trace container execution
result = await trace_exec(
    container_name="my-container",
    duration=30
)

# Profile container CPU
result = await profile_cpu(
    container_name="my-container",
    duration=60
)
```

## Available Tools

1. **list_containers** - List running containers
2. **top_resources** - Monitor top resource consumers
3. **trace_exec** - Trace process execution
4. **trace_network** - Trace network events
5. **trace_filesystem** - Monitor file operations
6. **profile_cpu** - Profile CPU usage
7. **profile_io** - Profile I/O operations
8. **snapshot_system** - Take system snapshots
9. **advise_security** - Generate security policies (requires container_name)
10. **analyze_deadlock** - Detect deadlocks

## Key Features of Simplified Implementation

✅ **Simple Parameter Handling**
- Uses Python's `Optional[str] = None` for optional parameters
- No complex Pydantic validation
- MCP Inspector friendly

✅ **Automatic Host/Container Detection**
- If `container_name` is `None` → monitors the host (adds `--host` flag)
- If `container_name` is provided → monitors that container

✅ **Clean Project Structure**
```
src/
└── inspektor_gadget_mcp/
    ├── __init__.py
    ├── __main__.py
    └── server.py       # All tools in one simple file
```

✅ **Direct Command Execution**
- Uses subprocess to run `sudo ig` commands
- Returns simple dictionaries with success/error/data
- Automatic JSON parsing when possible

## Testing

Run the test script to verify everything works:

```bash
# Run tests (some may fail without sudo)
python test_simplified.py

# Run with sudo to test actual ig commands
sudo python test_simplified.py
```

## Requirements

- Python 3.8+
- Inspektor Gadget (ig) v0.43.0 installed
- Linux kernel 4.18+ (5.4+ recommended)
- Root/sudo access for eBPF operations

## Troubleshooting

1. **"sudo: a terminal is required"** - Run with actual sudo: `sudo python -m inspektor_gadget_mcp`
2. **"command not found: ig"** - Install Inspektor Gadget first
3. **Container errors** - Make sure Docker/containerd is running
4. **eBPF errors** - Check kernel version and permissions