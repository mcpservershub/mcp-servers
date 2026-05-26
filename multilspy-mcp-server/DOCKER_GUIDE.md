# Docker Guide for MultilsPy MCP Server

## Understanding Language Server Requirements

### Key Points:
1. **MultilsPy is a client library** - It connects to language servers but doesn't require them to be pre-installed
2. **Language servers are only needed when processing files of that specific language**
3. **For testing the MCP server itself, no language servers are required**

## Docker Options

### 1. Default Dockerfile (C# / OmniSharp Support)
```dockerfile
docker build -t multilspy-mcp-server .
```

**Use this when:**
- Working with C# / .NET code bases
- Need C# code intelligence via OmniSharp
- Container size: about 1GB (includes .NET SDK 8.0)

### 2. Minimal Dockerfile (No Language Servers)
```dockerfile
docker build -f Dockerfile-genreric -t multilspy-mcp-minimal .
```

**Use this when:**
- Testing MCP server functionality
- Running in environments where language servers are installed separately
- Minimizing container size (about 200MB)

### 3. Full Language Server Support (Custom)
If you need additional language servers beyond C#, create a custom Dockerfile:

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

CMD ["python", "-m", "multilspy_mcp"]
```

## Building and Running

### Build the Docker Image
```bash
# Default (with C# / OmniSharp support)
docker build -t multilspy-mcp-server .

# Minimal version (no language servers)
docker build -f Dockerfile-genreric -t multilspy-mcp-minimal .
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
  python -m multilspy_mcp
```

## Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  multilspy-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: multilspy-mcp
    volumes:
      - ./workspace:/workspace:ro
      - mcp-cache:/cache
    environment:
      - WORKSPACE_ROOT=/workspace
      - MCP_LSP_CACHE_DIR=/cache
      - LOG_LEVEL=INFO
    command: python -m multilspy_mcp
    restart: unless-stopped

volumes:
  mcp-cache:
```

Run with:
```bash
docker compose up -d
docker compose logs -f
```

## Language Server Installation Notes

### Language Servers Included:
- **C# / .NET**: OmniSharp (pre-installed via .NET SDK 8.0)

### Language Servers NOT Included (install separately):
- **Python**: Install `python-lsp-server` or `jedi-language-server`
- **TypeScript/JavaScript**: Install `typescript-language-server` (requires Node.js)
- **Java**: Install Java runtime and `jdtls`
- **Go**: Install Go and `gopls`
- **Rust**: Install Rust and `rust-analyzer`

### When Language Servers Are NOT Needed:
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
Options:
1. Install the language server in the container (rebuild with custom Dockerfile)
2. Mount a volume with the language server binary
3. Note: OmniSharp (C#) is pre-installed in the default image; other language servers are not

## Performance Considerations

1. **Default Image (C# support)**: ~1GB, includes .NET SDK 8.0 for OmniSharp
2. **Minimal Image**: ~200MB, fastest startup, no language servers
3. **Full Custom Image**: 500MB+, includes multiple language servers

Choose based on your needs. For production, consider:
- Using multi-stage builds
- Installing only required language servers
- Using Alpine Linux for smaller size (with compatibility testing)

## Security Notes

- Run container as non-root user in production
- Use read-only mounts for workspace files
- Limit resource usage with Docker constraints
- Regularly update base images and dependencies
