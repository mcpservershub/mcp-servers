# Docker Guide for MultilsPy MCP Server

## Understanding Language Server Requirements

### Key Points:
1. **MultilsPy is a client library** - It connects to language servers but doesn't require them to be pre-installed
2. **Language servers are only needed when processing files of that specific language**
3. **For testing the MCP server itself, no language servers are required**

## Docker Options

### 1. Minimal Dockerfile (Recommended for Testing)
```dockerfile
# Uses the main Dockerfile - no language servers installed
docker build -t multilspy-mcp-minimal .
```

**Use this when:**
- Testing MCP server functionality
- Running in environments where language servers are installed separately
- Minimizing container size (about 200MB)

### 2. Python Language Server Support
```dockerfile
# Build from Dockerfile.with-python-lsp
docker build -f Dockerfile.with-python-lsp -t multilspy-mcp-python .
```

**Use this when:**
- Working primarily with Python code
- Need Python code intelligence features
- Container size: about 250MB

### 3. Full Language Server Support (Optional)
If you need multiple language servers, create a custom Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for various language servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs npm \           # For TypeScript/JavaScript
    openjdk-17-jre-headless \  # For Java
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

# Install Python package
RUN pip install --no-cache-dir -e .

# Install language servers as needed
RUN pip install python-lsp-server[all] && \
    npm install -g typescript typescript-language-server

ENV WORKSPACE_ROOT=/workspace \
    MCP_LSP_CACHE_DIR=/cache \
    PYTHONUNBUFFERED=1

RUN mkdir -p /workspace /cache

CMD ["python", "-m", "mcp", "run", "multilspy_mcp.server:mcp"]
```

## Building and Running

### Build the Docker Image
```bash
# Minimal version (no language servers)
docker build -t multilspy-mcp-server .

# With Python language server
docker build -f Dockerfile.with-python-lsp -t multilspy-mcp-server .
```

### Run the Container
```bash
# Basic run
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  -v /tmp/mcp-lsp-cache:/cache \
  multilspy-mcp-server

# With environment variables
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  -e LOG_LEVEL=DEBUG \
  multilspy-mcp-server

# Interactive bash session
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  multilspy-mcp-server \
  /bin/bash
```

### Test the Container
```bash
# Test module imports
docker run --rm multilspy-mcp-server \
  python -c "from multilspy_mcp import server; print('OK')"

# Test with MCP Inspector
docker run --rm -i \
  -v $(pwd)/workspace:/workspace \
  multilspy-mcp-server \
  python -m mcp run multilspy_mcp.server:mcp
```

## Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  multilspy-mcp:
    build: .
    container_name: multilspy-mcp
    volumes:
      - ./workspace:/workspace:ro
      - mcp-cache:/cache
    environment:
      - WORKSPACE_ROOT=/workspace
      - MCP_LSP_CACHE_DIR=/cache
      - LOG_LEVEL=INFO
    command: python -m mcp run multilspy_mcp.server:mcp
    restart: unless-stopped

volumes:
  mcp-cache:
```

Run with:
```bash
docker-compose up -d
docker-compose logs -f
```

## Language Server Installation Notes

### When Language Servers Are Needed:
- **Python files**: Install `python-lsp-server` or `jedi-language-server`
- **TypeScript/JavaScript**: Install `typescript-language-server`
- **Java**: Install Java runtime and `jdtls`
- **Go**: Install Go and `gopls`
- **Rust**: Install Rust and `rust-analyzer`

### When They Are NOT Needed:
- Testing MCP server connectivity
- Testing MCP protocol implementation
- Running in environments with external language servers
- Using the server as a pass-through proxy

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs multilspy-mcp-server

# Run interactive debug
docker run --rm -it multilspy-mcp-server /bin/bash
```

### Import errors
```bash
# Verify installation
docker run --rm multilspy-mcp-server pip list | grep multilspy
```

### Language server not found
This is expected if you're using the minimal Dockerfile. Options:
1. Install the language server in the container (rebuild with custom Dockerfile)
2. Mount a volume with the language server binary
3. Use the full-featured Dockerfile

## Performance Considerations

1. **Minimal Image**: ~200MB, fastest startup, no language servers
2. **Python LSP Image**: ~250MB, includes Python language server
3. **Full Image**: 500MB+, includes multiple language servers

Choose based on your needs. For production, consider:
- Using multi-stage builds
- Installing only required language servers
- Using Alpine Linux for smaller size (with compatibility testing)

## Security Notes

- Run container as non-root user in production
- Use read-only mounts for workspace files
- Limit resource usage with Docker constraints
- Regularly update base images and dependencies