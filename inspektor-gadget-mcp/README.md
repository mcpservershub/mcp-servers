# Inspektor-Gadget MCP Server

An MCP (Model Context Protocol) Server that provides AI agents and developers with powerful eBPF-based observability tools through Inspektor-Gadget.

## Features

This MCP Server exposes 10 high-impact tools for system and container observability:

### 🔍 **Container Management**
- `list_containers` - List running containers across Docker, containerd, CRI-O, and Podman

### 📊 **Tracing Tools** 
- `trace_exec` - Monitor process execution in containers and host
- `trace_network` - Comprehensive network tracing (DNS, TCP, connections)
- `trace_filesystem` - Monitor file operations (open, mount, slow I/O)

### 🎯 **Profiling Tools**
- `profile_cpu` - CPU profiling with flame graph generation
- `profile_io` - Block I/O and TCP RTT profiling

### 📸 **Snapshot Tools**
- `snapshot_system` - Capture system state (processes and sockets)

### 📈 **Monitoring Tools**
- `top_resources` - Real-time resource consumption monitoring

### 🛡️ **Security Tools**
- `advise_security` - Generate network policies and seccomp profiles
- `analyze_deadlock` - Detect potential deadlocks in applications

## Prerequisites

- Linux host (kernel 4.18+ recommended)
- Docker or Podman installed
- Root access or appropriate capabilities for eBPF operations

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/inspektor-gadget-mcp.git
cd inspektor-gadget-mcp

# Build the Docker image
docker build -t inspektor-gadget-mcp:latest .

# Or use docker-compose
docker-compose build
```

### Option 2: Local Installation

```bash
# Install Inspektor-Gadget
curl -sL https://github.com/inspektor-gadget/inspektor-gadget/releases/latest/download/ig-linux-amd64-latest.tar.gz | \
  sudo tar -C /usr/local/bin -xzf - ig

# Install the MCP Server
pip install -e .
```

## Running the MCP Server

### ⚠️ Important: Privileged Access Required

The container **MUST** run with privileged access for eBPF operations to work:

```bash
# Using Docker directly (PRIVILEGED MODE REQUIRED)
docker run --rm \
  --privileged \                              # Required for eBPF syscalls
  --pid=host \                                # See all host processes
  --network=host \                            # See all network interfaces
  -v /sys/kernel/debug:/sys/kernel/debug:ro \ # Kernel debug info (READ-ONLY)
  -v /sys/fs/bpf:/sys/fs/bpf:rw \             # BPF filesystem (READ-WRITE for pinning)
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \       # Cgroup info (READ-ONLY)
  -v /proc:/host/proc:ro \                    # Host process info (READ-ONLY)
  -v /var/run/docker.sock:/var/run/docker.sock:ro \ # Docker API (READ-ONLY)
  inspektor-gadget-mcp:latest

# Using docker-compose (already configured with privileged mode)
docker-compose up
```

### Local Execution

```bash
# Requires root/sudo for eBPF operations
sudo python -m mcp.server.stdio inspektor_mcp.server:mcp
```

## MCP Configuration

### For Claude Desktop or other MCP clients

Add to your MCP configuration file:

#### Docker Configuration (Recommended)
```json
{
  "mcpServers": {
    "inspektor-gadget": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--privileged",
        "--pid=host",
        "--network=host",
        "-v", "/sys/kernel/debug:/sys/kernel/debug:ro",
        "-v", "/sys/fs/bpf:/sys/fs/bpf:rw",
        "-v", "/sys/fs/cgroup:/sys/fs/cgroup:ro",
        "-v", "/proc:/host/proc:ro",
        "-v", "/var/run/docker.sock:/var/run/docker.sock:ro",
        "inspektor-gadget-mcp:latest"
      ]
    }
  }
}
```

#### Local Configuration
```json
{
  "mcpServers": {
    "inspektor-gadget": {
      "command": "sudo",
      "args": ["python", "-m", "mcp.server.stdio", "inspektor_mcp.server:mcp"],
      "env": {
        "PYTHONPATH": "/path/to/inspektor-gadget-mcp/src"
      }
    }
  }
}
```

## Testing with MCP Inspector

### 1. Install MCP Inspector
```bash
npm install -g @modelcontextprotocol/inspector
```

### 2. Run the test script
```bash
# Start the MCP Server in privileged container
docker-compose up -d

# Run the test script
npx @modelcontextprotocol/inspector \
  "docker run --rm -i --privileged --pid=host --network=host \
  -v /sys/kernel/debug:/sys/kernel/debug:ro \
  -v /sys/fs/bpf:/sys/fs/bpf:rw \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  -v /proc:/host/proc:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  inspektor-gadget-mcp:latest"
```

## Usage Examples

### List all containers
```python
result = await mcp.call_tool("list_containers", {
    "runtime": "docker",
    "output_format": "json"
})
```

### Trace process execution
```python
result = await mcp.call_tool("trace_exec", {
    "target": "container",
    "container_name": "my-app",
    "duration": 30,
    "follow_fork": True
})
```

### Profile CPU usage
```python
result = await mcp.call_tool("profile_cpu", {
    "target": "container",
    "container_name": "my-app",
    "duration": 60,
    "output_format": "flamegraph"
})
```

### Generate security policies
```python
result = await mcp.call_tool("advise_security", {
    "advice_type": "networkpolicy",
    "container_name": "my-app",
    "duration": 120,
    "output_format": "yaml"
})
```

## Tools Reference

Complete documentation of all available tools and their arguments.

### Important Notes

- **Container Name Behavior**: 
  - If `container_name` is provided → monitors the specified container
  - If `container_name` is NOT provided → monitors the Linux host (uses `--host` flag)
  - For tools with `target` parameter, set `target="host"` to monitor the host

- **Required Permissions**: All tools require `sudo`/root privileges

### Tool Arguments Summary

#### 1. list_containers
List all running containers with their metadata

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| runtime | string | No | "all" | Container runtime to query (docker, containerd, crio, podman, all) |
| namespace | string | No | None | [OPTIONAL] Namespace for containerd runtime |
| containername | string | No | None | [OPTIONAL] Filter by specific container name |
| output_format | string | No | "json" | Output format (json, table) |

#### 2. trace_exec
Trace process execution in containers or host system

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| target | string | No | "host" | Trace target (host, container) |
| container_name | string | Conditional | None | Container name (required when target='container') |
| duration | integer | No | 10 | Duration in seconds (1-300) |
| filter_uid | integer | No | None | Filter by user ID |
| filter_comm | string | No | None | Filter by command name |
| follow_fork | boolean | No | true | Follow forked processes |

#### 3. trace_network
Trace network events including DNS, TCP, and connections

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| trace_type | string | No | "tcp" | Network trace type (dns, tcp, bind, ssl, sni, all) |
| container_name | string | No | None | Container name (None = monitor host) |
| duration | integer | No | 10 | Duration in seconds (1-300) |
| filter_port | integer | No | None | Filter by port number (1-65535) |
| filter_protocol | string | No | "tcp" | Protocol to filter (tcp, udp) |
| show_drops | boolean | No | false | Show dropped packets |
| show_retransmissions | boolean | No | false | Show TCP retransmissions |

#### 4. trace_filesystem
Monitor file operations including open, mount, and slow I/O

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| trace_type | string | No | "open" | Filesystem trace type (open, mount, fsslower) |
| container_name | string | No | None | Container name (None = monitor host) |
| duration | integer | No | 10 | Duration in seconds (1-300) |
| filter_path | string | No | None | Filter by file path pattern |
| min_latency_ms | integer | No | None | Min I/O latency in ms (for fsslower) |

#### 5. profile_cpu
Profile CPU usage and generate flame graphs

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| target | string | No | "host" | Profile target (host, container, pid) |
| container_name | string | Conditional | None | Container name (required when target='container') |
| pid | integer | Conditional | None | Process ID (required when target='pid') |
| duration | integer | No | 30 | Duration in seconds (1-300) |
| frequency | integer | No | 99 | Sampling frequency in Hz (1-1000) |
| output_format | string | No | "flamegraph" | Output format (flamegraph, raw, folded) |

#### 6. profile_io
Profile I/O operations including block I/O and TCP RTT

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| profile_type | string | No | "blockio" | I/O profile type (blockio, tcprtt) |
| container_name | string | No | None | Container name (None = profile host) |
| duration | integer | No | 30 | Duration in seconds (1-300) |

#### 7. snapshot_system
Take a snapshot of system state

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| snapshot_type | string | No | "process" | Snapshot type (process, socket, all) |
| container_name | string | No | None | Container name (None = snapshot host) |
| include_threads | boolean | No | false | Include thread information |
| include_tcp | boolean | No | true | Include TCP sockets |
| include_udp | boolean | No | true | Include UDP sockets |
| include_unix | boolean | No | false | Include Unix domain sockets |

#### 8. top_resources
Monitor top resource consumers in real-time

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| resource_type | string | No | "process" | Resource type (process, file, tcp, blockio, all) |
| container_name | string | No | None | Container name (None = monitor host) |
| interval | integer | No | 1 | Update interval in seconds (1-10) |
| max_rows | integer | No | 10 | Maximum rows to display (1-50) |
| sort_by | string | No | "cpu" | Sort by field (cpu, memory, io, pid) |

#### 9. advise_security
Generate security policies and recommendations

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| advice_type | string | No | "all" | Advice type (networkpolicy, seccomp, all) |
| container_name | string | **YES** | - | Container name to analyze (REQUIRED) |
| duration | integer | No | 60 | Observation duration in seconds (10-600) |
| output_format | string | No | "yaml" | Output format (yaml, json) |

#### 10. analyze_deadlock
Detect potential deadlocks in applications

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| container_name | string | No | None | Container name (None = analyze host) |
| pid | integer | No | None | Specific process ID to analyze |
| duration | integer | No | 30 | Analysis duration in seconds (1-300) |
| stack_depth | integer | No | 20 | Stack trace depth (1-127) |

#### 11. run_gadget
Run any Inspektor Gadget with custom parameters - provides maximum flexibility

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| gadget_name | string | Yes | - | Gadget name - short name (e.g., 'trace_open') or full URL |
| container_name | string | No | None | Container name to monitor (None = monitor host) |
| args | list[string] | No | [] | Additional arguments to pass to the gadget |
| timeout_seconds | integer | No | 120 | Timeout for gadget execution in seconds (1-600) |

**Examples:**
```python
# Run a gadget using short name on the host
result = await tool("run_gadget", {
    "gadget_name": "trace_open",  # Automatically expands to full URL
    "args": ["-t", "30", "--filter-failed"]
})

# Run a gadget with full URL and container monitoring
result = await tool("run_gadget", {
    "gadget_name": "ghcr.io/inspektor-gadget/gadget/trace_signal:v0.43.0",
    "container_name": "my-app",
    "args": ["--filter-signal", "SIGKILL"],
    "timeout_seconds": 60
})

# Run any gadget not in the registry
result = await tool("run_gadget", {
    "gadget_name": "trace_custom",  # Will try ghcr.io/inspektor-gadget/gadget/trace_custom:v0.43.0
    "args": ["--custom-flag", "value"]
})
```

### Common Usage Patterns

#### Host Monitoring (No container_name)
```python
# Monitor the Linux host - just omit container_name
result = await tool("top_resources", {
    "resource_type": "process"
})

result = await tool("trace_network", {
    "trace_type": "tcp"
})
```

#### Container Monitoring (With container_name)
```python
# Monitor specific container - provide container_name
result = await tool("top_resources", {
    "resource_type": "process",
    "container_name": "my-container"
})

result = await tool("trace_network", {
    "trace_type": "tcp",
    "container_name": "my-container"
})
```

## Security Considerations

1. **Privileged Access**: This MCP Server requires privileged container access for eBPF operations
2. **Host Visibility**: The container has visibility into host processes and network
3. **Resource Access**: Mounts sensitive kernel interfaces (/sys, /proc)
4. **Runtime Access**: Requires Docker socket access to inspect containers

### Best Practices

- Run in isolated environments when possible
- Limit access to trusted users only
- Monitor resource usage (eBPF programs can impact performance)
- Use resource limits in production deployments
- Audit all tool executions

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure the container is running with `--privileged` flag
   - For local execution, use `sudo`

2. **Inspektor-Gadget not found**
   - Check if `ig` binary is installed: `which ig`
   - Verify installation: `ig version`

3. **Container runtime not accessible**
   - Ensure Docker socket is mounted: `-v /var/run/docker.sock:/var/run/docker.sock`
   - Check Docker daemon is running: `docker ps`

4. **eBPF programs fail to load**
   - Verify kernel version: `uname -r` (needs 4.18+)
   - Check kernel config: `grep CONFIG_BPF /boot/config-$(uname -r)`

### Debug Mode

Enable debug logging:
```bash
docker run --rm \
  --privileged \
  # ... other flags ...
  -e LOG_LEVEL=DEBUG \
  inspektor-gadget-mcp:latest
```

## Development

### Project Structure
```
inspektor-gadget-mcp/
├── src/inspektor_mcp/
│   ├── server.py       # Main MCP server
│   ├── models.py       # Pydantic models
│   ├── config.py       # Configuration
│   ├── tools/          # Tool implementations
│   └── utils/          # Utilities
├── tests/              # Test suite
├── Dockerfile          # Container image
├── docker-compose.yml  # Compose configuration
└── pyproject.toml      # Python project config
```

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# With coverage
pytest --cov=inspektor_mcp tests/
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

- [Inspektor-Gadget](https://github.com/inspektor-gadget/inspektor-gadget) for the powerful eBPF observability framework
- [Model Context Protocol](https://modelcontextprotocol.io) for the MCP specification
- The eBPF community for advancing Linux observability

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [Inspektor-Gadget documentation](https://inspektor-gadget.io/docs/)
- Review the [MCP documentation](https://modelcontextprotocol.io/docs)