# Host Monitoring with ig v0.43.0

## Overview
This guide shows how to monitor your Linux host using Inspektor Gadget v0.43.0.

## Key Discovery
In ig v0.43.0, gadgets must be run with:
1. Full gadget image URL with version tag (`:v0.43.0`)
2. Using `sudo ig run` command
3. Timeout specified with `-t` flag

## Working Commands for Host Monitoring

### 1. Process Monitoring

```bash
# Monitor top processes on host
sudo ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 10 --max-entries 20

# Trace process execution on host
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 30

# Trace processes by specific user
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 30 --uid 1000

# Snapshot all processes
sudo ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0 -t 5
```

### 2. Network Monitoring

```bash
# Trace TCP connections
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 30

# Trace only TCP connect events
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 30 --connect-only

# Trace only TCP accept events
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 30 --accept-only

# Show only failed connections
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 30 --failure-only

# Trace DNS queries
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_dns:v0.43.0 -t 30

# Monitor top TCP connections
sudo ig run ghcr.io/inspektor-gadget/gadget/top_tcp:v0.43.0 -t 10

# Snapshot all sockets
sudo ig run ghcr.io/inspektor-gadget/gadget/snapshot_socket:v0.43.0 -t 5
```

### 3. File System Monitoring

```bash
# Trace file opens
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_open:v0.43.0 -t 30

# Trace mount operations
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_mount:v0.43.0 -t 30

# Monitor top file activity
sudo ig run ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0 -t 10

# Trace slow filesystem operations
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_fsslower:v0.43.0 -t 30
```

### 4. Performance Profiling

```bash
# Profile CPU usage
sudo ig run ghcr.io/inspektor-gadget/gadget/profile_cpu:v0.43.0 -t 60

# Profile block I/O
sudo ig run ghcr.io/inspektor-gadget/gadget/profile_blockio:v0.43.0 -t 60

# Profile TCP round-trip time
sudo ig run ghcr.io/inspektor-gadget/gadget/profile_tcprtt:v0.43.0 -t 60

# Monitor top block I/O
sudo ig run ghcr.io/inspektor-gadget/gadget/top_blockio:v0.43.0 -t 10
```

### 5. Container Management

```bash
# List all containers (direct command, not a gadget)
sudo ig list-containers

# List only Docker containers
sudo ig list-containers --runtimes docker

# List specific container
sudo ig list-containers --containername my-container
```

### 6. Security Monitoring

```bash
# Trace capability usage
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_capabilities:v0.43.0 -t 30

# Trace signals
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_signal:v0.43.0 -t 30

# Monitor OOM kills
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_oomkill:v0.43.0 -t 60

# Audit seccomp violations
sudo ig run ghcr.io/inspektor-gadget/gadget/audit_seccomp:v0.43.0 -t 30
```

## Container-Specific Monitoring

To monitor a specific container, add `--containername`:

```bash
# Monitor processes in a specific container
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 30 --containername my-container

# Monitor network in a container
sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 30 --containername my-container
```

## Important Notes

1. **Root Required**: All commands need `sudo` or root access
2. **Version Tags**: Always use `:v0.43.0` tag for gadgets
3. **Timeout**: Use `-t` flag for timeout (in seconds)
4. **No Daemon Needed**: These commands work directly without starting a daemon

## Continuous Monitoring Script

Create a monitoring script for continuous observation:

```bash
#!/bin/bash
# continuous_monitor.sh

while true; do
    echo "=== Process Activity ==="
    sudo ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 5 --max-entries 5
    
    echo "=== Network Activity ==="
    sudo ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 5 --connect-only
    
    echo "=== File Activity ==="
    sudo ig run ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0 -t 5
    
    sleep 2
done
```

## Troubleshooting

If you get errors:

1. **"Error: fetching gadget information"** - Make sure you're using the correct image URL with version tag
2. **"permission denied"** - Run with sudo
3. **"failed to initialize"** - Check kernel version (needs 4.18+, preferably 5.4+)
4. **Long pull times** - First run downloads the gadget image, subsequent runs are faster

## Testing

Run the test script to verify everything works:

```bash
sudo ./test_gadgets.sh
```

This will test the main gadgets and show their output.