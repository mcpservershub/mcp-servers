# Docker Deployment Guide

This guide explains how to run `chrome-devtools-mcp` in a Docker container using Chainguard base images.

## Overview

The MCP server has been containerized using a multi-stage Dockerfile with Chainguard images for minimal attack surface and enhanced security. The container includes:

- **Base Images**: Chainguard's hardened, minimal images
- **Node.js**: Required for running the MCP server
- **Chromium**: Open-source browser for DevTools functionality
- **Multi-stage Build**: Optimized for size and security

## Prerequisites

- Docker 20.10+ or Docker Desktop
- Docker Compose 2.0+ (optional)
- At least 4GB RAM available
- Linux, macOS, or Windows with WSL2

## Quick Start

### Build the Image

```bash
docker build -t chrome-devtools-mcp:latest .
```

### Run with Docker

```bash
docker run --rm -i \
  --cap-add=SYS_ADMIN \
  --shm-size=2g \
  chrome-devtools-mcp:latest
```

### Run with Docker Compose

```bash
docker compose up -d
```

## Important Considerations

### 1. Chrome Sandbox Requirements

Chrome requires either:
- **Option A**: `CAP_SYS_ADMIN` capability (recommended)
- **Option B**: Running Chrome with `--no-sandbox` (less secure)

The Dockerfile uses Option A by default via `cap_add` in docker-compose.yml.

### 2. Shared Memory

Chrome needs more shared memory than Docker's default 64MB:

```bash
docker run --shm-size=2g ...
```

### 3. Headless Mode

For containerized environments, always use headless mode:

```bash
docker run chrome-devtools-mcp:latest --headless --isolated
```

### 4. MCP Communication

MCP servers communicate via stdin/stdout. To use with MCP clients:

```bash
docker run -i chrome-devtools-mcp:latest
```

The `-i` (interactive) flag is **required** for proper stdio communication.

## Configuration

### Environment Variables

```bash
docker run -i \
  -e DEBUG="*" \
  -e NODE_ENV=production \
  chrome-devtools-mcp:latest
```

### Command-line Arguments

Pass arguments after the image name:

```bash
docker run -i chrome-devtools-mcp:latest \
  --headless \
  --isolated \
  --viewport=1920x1080 \
  --logFile=/tmp/debug.log
```

### Available Arguments

- `--headless`: Run Chrome without UI (required for containers)
- `--isolated`: Use temporary profile (recommended for containers)
- `--executablePath`: Path to Chrome (pre-set to `/usr/bin/chromium-browser`)
- `--viewport`: Initial viewport size (e.g., `1920x1080`)
- `--logFile`: Path to log file
- `--channel`: Chrome channel (not applicable with Chromium)

## MCP Client Integration

### Claude Desktop / Cline / Cursor

Update your MCP configuration to use Docker:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--cap-add=SYS_ADMIN",
        "--shm-size=2g",
        "chrome-devtools-mcp:latest",
        "--headless",
        "--isolated"
      ]
    }
  }
}
```

### Using Docker Compose

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "/path/to/docker-compose.yml",
        "run",
        "--rm",
        "chrome-devtools-mcp"
      ]
    }
  }
}
```

## Security Considerations

### Chainguard Images

This Dockerfile uses Chainguard's hardened base images:
- Minimal attack surface (no shell by default in runtime)
- Regular security updates
- Non-root user execution
- SBOM (Software Bill of Materials) included

### Non-Root Execution

The container runs as user `nonroot` (UID 65532) for enhanced security:

```dockerfile
USER nonroot
```

### Network Isolation

For added security, run without network access when possible:

```bash
docker run -i --network=none chrome-devtools-mcp:latest
```

**Note**: This only works if connecting to a pre-existing Chrome instance.

## Troubleshooting

### Chrome Won't Start

**Symptom**: "Failed to launch Chrome" errors

**Solutions**:
1. Ensure `--shm-size=2g` is set
2. Add `CAP_SYS_ADMIN` capability
3. Try with `--cap-add=SYS_ADMIN --security-opt seccomp=unconfined`

### Performance Issues

**Symptom**: Slow page loads or timeouts

**Solutions**:
1. Increase container resources:
   ```bash
   docker run --cpus=2 --memory=4g ...
   ```
2. Use SSD storage for Docker volumes
3. Enable hardware acceleration (host-dependent)

### MCP Client Can't Connect

**Symptom**: MCP client reports connection timeout

**Solutions**:
1. Ensure `-i` flag is used for interactive mode
2. Check that container starts successfully: `docker logs <container-id>`
3. Verify Chrome can launch: `docker run chrome-devtools-mcp:latest --version`

### Font Rendering Issues

**Symptom**: Missing or broken fonts in screenshots

**Solution**: The Dockerfile includes common fonts, but you can mount additional fonts:

```bash
docker run -i \
  -v /usr/share/fonts:/usr/share/fonts:ro \
  chrome-devtools-mcp:latest
```

## Advanced Usage

### Persistent Cache

Use a volume for Chrome cache to improve performance:

```bash
docker run -i \
  -v chrome-cache:/home/nonroot/.cache/chrome-devtools-mcp \
  chrome-devtools-mcp:latest
```

### Custom Chrome Binary

Mount a custom Chrome installation:

```bash
docker run -i \
  -v /path/to/chrome:/chrome:ro \
  chrome-devtools-mcp:latest \
  --executablePath=/chrome/chrome
```

### Debugging

Enable verbose logging:

```bash
docker run -i \
  -e DEBUG="*" \
  chrome-devtools-mcp:latest \
  --logFile=/tmp/debug.log
```

## Building from Source

### Standard Build

```bash
docker build -t chrome-devtools-mcp:latest .
```

### Build with Custom Arguments

```bash
docker build \
  --build-arg NODE_VERSION=22 \
  -t chrome-devtools-mcp:node22 \
  .
```

### Multi-platform Build

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t chrome-devtools-mcp:latest \
  .
```

**Note**: ARM64 support depends on Chromium availability for ARM.

## Resource Requirements

### Minimum

- **CPU**: 1 core
- **Memory**: 2GB
- **Disk**: 1GB
- **Shared Memory**: 512MB

### Recommended

- **CPU**: 2+ cores
- **Memory**: 4GB
- **Disk**: 2GB SSD
- **Shared Memory**: 2GB

## Limitations

1. **No GPU Acceleration**: Software rendering only in containers
2. **No Audio**: Audio devices not available
3. **Limited Display**: Headless mode required
4. **Sandbox Restrictions**: Requires elevated capabilities or --no-sandbox

## Production Deployment

### Kubernetes

Example pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: chrome-devtools-mcp
spec:
  containers:
  - name: mcp-server
    image: chrome-devtools-mcp:latest
    args: ["--headless", "--isolated"]
    securityContext:
      capabilities:
        add: ["SYS_ADMIN"]
    resources:
      limits:
        memory: "4Gi"
        cpu: "2"
      requests:
        memory: "2Gi"
        cpu: "1"
    volumeMounts:
    - name: dshm
      mountPath: /dev/shm
  volumes:
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 2Gi
```

### Health Checks

The Dockerfile includes a basic health check. For production, consider:

```bash
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1
```

## License

This Docker configuration is part of the chrome-devtools-mcp project and uses the same Apache-2.0 license.

## Support

For issues related to:
- **Docker setup**: Check this guide and Docker logs
- **MCP server**: See main [README.md](./README.md) and [troubleshooting guide](./docs/troubleshooting.md)
- **Chainguard images**: Visit [Chainguard documentation](https://edu.chainguard.dev/)
