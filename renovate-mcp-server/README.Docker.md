# Docker Usage for Renovate MCP Server

This guide explains how to build and run the Renovate MCP Server using Docker.

## Quick Start

### 1. Build the Image

```bash
# Standard Debian-based image
docker build -t renovate-mcp-server:latest .

# Or use Alpine Linux for smaller size
docker build -f Dockerfile.alpine -t renovate-mcp-server:alpine .
```

### 2. Run the Container

#### Basic Usage
```bash
docker run -it \
  -e RENOVATE_TOKEN=your-token-here \
  renovate-mcp-server:latest
```

#### With Local Directory Access
```bash
docker run -it \
  -e RENOVATE_TOKEN=your-token-here \
  -v $(pwd):/home/mcp/workspace:ro \
  renovate-mcp-server:latest
```

## Docker Compose

### 1. Setup Environment
```bash
cp .env.example .env
# Edit .env with your tokens
```

### 2. Run with Docker Compose
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Using with MCP Inspector

### 1. Create a Docker wrapper script
```bash
cat > mcp-docker.sh << 'EOF'
#!/bin/bash
docker run -i --rm \
  -e RENOVATE_TOKEN=${RENOVATE_TOKEN} \
  renovate-mcp-server:latest
EOF
chmod +x mcp-docker.sh
```

### 2. Use in MCP Inspector
Point the Inspector to the wrapper script:
```
/path/to/mcp-docker.sh
```

## Advanced Usage

### Custom Configuration
```bash
docker run -it \
  -e RENOVATE_TOKEN=your-token-here \
  -v $(pwd)/renovate.json:/home/mcp/configs/renovate.json:ro \
  -v $(pwd)/my-project:/home/mcp/workspace/my-project:ro \
  renovate-mcp-server:latest
```

### Multiple Platform Tokens
```bash
docker run -it \
  -e GITHUB_TOKEN=github-token \
  -e GITLAB_TOKEN=gitlab-token \
  -e RENOVATE_TOKEN=default-token \
  renovate-mcp-server:latest
```

### Debug Mode
```bash
docker run -it \
  -e RENOVATE_TOKEN=your-token-here \
  -e LOG_LEVEL=debug \
  renovate-mcp-server:latest
```

## Security Considerations

The Docker images implement several security best practices:

1. **Non-root user**: Runs as user `mcp` (UID 1000)
2. **Read-only filesystem**: Uses read-only root filesystem with tmpfs for writable areas
3. **No new privileges**: Prevents privilege escalation
4. **Minimal base image**: Alpine variant available for reduced attack surface
5. **Health checks**: Built-in health monitoring

## Volume Mounts

### Workspace Directory
Mount local directories for analysis:
```bash
-v /path/to/project:/home/mcp/workspace/project:ro
```

### Config Directory
Mount Renovate configuration files:
```bash
-v /path/to/configs:/home/mcp/configs:ro
```

## Troubleshooting

### Permission Issues
If you encounter permission issues with mounted volumes:
```bash
# Run with your user ID
docker run -it --user $(id -u):$(id -g) ...
```

### Network Issues
For GitHub Enterprise or self-hosted platforms:
```bash
docker run -it \
  --add-host gitlab.company.com:192.168.1.100 \
  -e RENOVATE_TOKEN=your-token \
  renovate-mcp-server:latest
```

### Debugging
Enable debug logging:
```bash
docker run -it \
  -e LOG_LEVEL=debug \
  -e NODE_ENV=development \
  renovate-mcp-server:latest
```

## Image Details

### Debian-based Image
- Base: `python:3.12-slim`
- Size: ~400MB
- Includes: Python 3.12, Node.js 20.x, Renovate CLI

### Alpine-based Image
- Base: `python:3.12-alpine`
- Size: ~250MB
- Includes: Python 3.12, Node.js (latest), Renovate CLI

## Building for Production

### Multi-platform Build
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-registry/renovate-mcp-server:latest \
  --push .
```

### Scanning for Vulnerabilities
```bash
# Using Docker Scout
docker scout quickview renovate-mcp-server:latest

# Using Trivy
trivy image renovate-mcp-server:latest
```