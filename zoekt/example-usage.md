# Docker Usage Examples

This document provides examples of how to use the Zoekt MCP Server Docker image.

## Building the Image

### Standard Version
```bash
# Build the standard image
./build-docker.sh

# Or manually with docker
docker build -t zoekt-mcp-server:latest .
```

### Version with Universal Ctags
```bash
# Build the image with Universal Ctags support
./build-docker-ctags.sh

# Or manually with docker
docker build -f Dockerfile.ctags -t zoekt-mcp-server:ctags .
```

## Running the Container

### Basic Usage
```bash
# Start the MCP server (stdin/stdout communication)
docker run -it --rm zoekt-mcp-server:latest
```

### With Persistent Storage
```bash
# Create data directories
mkdir -p data repos

# Run with volume mounts
docker run -it --rm \
  -v $(pwd)/data:/app/.zoekt \
  -v $(pwd)/repos:/app/repos \
  zoekt-mcp-server:latest
```

### Using Docker Compose
```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Testing the Container

### Standard Version
```bash
# Run the test script
./test-docker.sh

# Or manually test tools
docker run --rm zoekt-mcp-server:latest /usr/local/bin/zoekt --help
```

### Version with Universal Ctags
```bash
# Run the ctags test script
./test-docker-ctags.sh

# Test ctags functionality
docker run --rm zoekt-mcp-server:ctags /usr/local/bin/ctags --version
docker run --rm zoekt-mcp-server:ctags /usr/local/bin/ctags --list-languages
```

## Interactive Shell (for debugging)
```bash
# Start a shell in the container
docker run -it --rm --entrypoint=/bin/sh zoekt-mcp-server:latest

# Check available tools
ls -la /usr/local/bin/zoekt*
```

## MCP Protocol Testing

```bash
# Test tools/list method
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | \
  docker run -i --rm zoekt-mcp-server:latest

# Test a search (requires indexed data)
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "zoekt-search", "arguments": {"query": "test", "output_file": "/tmp/results.txt"}}}' | \
  docker run -i --rm -v $(pwd)/data:/app/.zoekt zoekt-mcp-server:latest
```

## Production Deployment

```bash
# Run as a service with restart policy
docker run -d \
  --name zoekt-mcp-server \
  --restart=unless-stopped \
  -v zoekt-data:/app/.zoekt \
  -v zoekt-repos:/app/repos \
  zoekt-mcp-server:latest
```

## Image Details

- **Base Image**: Chainguard static (minimal attack surface)
- **Size**: Optimized for minimal footprint
- **Security**: Distroless runtime with only necessary binaries
- **Tools Included**: All Zoekt CLI tools + MCP server
- **Default User**: Non-root (security best practice)