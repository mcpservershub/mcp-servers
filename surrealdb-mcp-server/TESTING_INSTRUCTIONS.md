# SurrealMCP Testing Instructions

This document provides comprehensive testing instructions for SurrealMCP, covering both standalone Rust application and Docker container deployments using MCP Inspector.

## Prerequisites

### For All Testing
- **SurrealDB**: Running instance or use the embedded memory mode
- **MCP Inspector**: Install from [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
  ```bash
  npm install -g @modelcontextprotocol/inspector
  ```

### For Rust Testing
- **Rust**: Version 1.89.0 or later
- **Cargo**: Latest version

### For Docker Testing  
- **Docker**: Version 20.10 or later
- **Docker Compose**: Optional, for multi-container setups

## Part 1: Testing as Standalone Rust Application

### 1.1 Build and Install

```bash
# Clone the repository (if not already done)
git clone https://github.com/surrealdb/surrealmcp.git
cd surrealmcp

# Build the project
cargo build --release

# Install locally (optional)
cargo install --path .

# Verify installation
surrealmcp --version
```

### 1.2 Start SurrealDB Instance (Optional)

If testing with an external SurrealDB instance:

```bash
# Start SurrealDB with default settings
surreal start --user root --pass root --bind 0.0.0.0:8000

# Or use Docker
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root
```

### 1.3 Test Different Transport Modes

#### A. STDIO Mode (Default)

```bash
# Test with memory database (no external SurrealDB needed)
surrealmcp start

# Test with external SurrealDB
surrealmcp start \
  --endpoint ws://localhost:8000/rpc \
  --ns test \
  --db test \
  --user root \
  --pass root
```

#### B. HTTP Mode

```bash
# Start HTTP server
surrealmcp start \
  --bind-address 127.0.0.1:8080 \
  --server-url http://localhost:8080 \
  --auth-disabled

# With authentication enabled
surrealmcp start \
  --bind-address 127.0.0.1:8080 \
  --server-url http://localhost:8080 \
  --rate-limit-rps 100 \
  --rate-limit-burst 200
```

#### C. Unix Socket Mode

```bash
# Start Unix socket server
surrealmcp start \
  --socket-path /tmp/surrealmcp.sock \
  --ns test \
  --db test
```

### 1.4 Test with MCP Inspector

#### STDIO Mode Testing

```bash
# Create MCP Inspector configuration
cat > mcp-inspector-stdio.json << EOF
{
  "mcpServers": {
    "surrealmcp": {
      "command": "surrealmcp",
      "args": ["start"],
      "env": {
        "SURREALDB_URL": "memory",
        "SURREALDB_NS": "test",
        "SURREALDB_DB": "test"
      }
    }
  }
}
EOF

# Run MCP Inspector
npx @modelcontextprotocol/inspector mcp-inspector-stdio.json

# Open browser at http://localhost:3000
```

#### HTTP Mode Testing

```bash
# Start the HTTP server first
surrealmcp start \
  --bind-address 127.0.0.1:8080 \
  --auth-disabled &

# Create MCP Inspector configuration for HTTP
cat > mcp-inspector-http.json << EOF
{
  "mcpServers": {
    "surrealmcp": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
EOF

# Run MCP Inspector
npx @modelcontextprotocol/inspector mcp-inspector-http.json
```

### 1.5 Test Available Tools

Once connected via MCP Inspector, test these tools:

1. **Connection Management**
   - `connect_endpoint`: Connect to memory, file, or remote DB
   - `use_namespace`: Switch namespace
   - `use_database`: Switch database
   - `list_namespaces`: List available namespaces
   - `list_databases`: List available databases

2. **Data Operations**
   - `query`: Execute SurrealQL queries
   - `select`: Query records
   - `insert`: Insert records
   - `create`: Create specific record
   - `update`: Update records
   - `delete`: Delete records
   - `relate`: Create relationships

3. **Cloud Operations** (if configured)
   - `list_cloud_organizations`
   - `list_cloud_instances`
   - `create_cloud_instance`

### 1.6 Environment Variable Testing

```bash
# Test with environment variables
export SURREALDB_URL="ws://localhost:8000/rpc"
export SURREALDB_NS="myapp"
export SURREALDB_DB="production"
export SURREALDB_USER="root"
export SURREALDB_PASS="root"

surrealmcp start
```

## Part 2: Testing with Docker Container

### 2.1 Pull or Build Docker Image

```bash
# Pull official image
docker pull surrealdb/surrealmcp:latest

# Or build locally
docker build -t surrealmcp:local .
```

### 2.2 Test Different Docker Modes

#### A. STDIO Mode with Docker

```bash
# Run in interactive mode
docker run --rm -it surrealdb/surrealmcp:latest start

# With environment variables
docker run --rm -it \
  -e SURREALDB_URL="memory" \
  -e SURREALDB_NS="test" \
  -e SURREALDB_DB="test" \
  surrealdb/surrealmcp:latest start
```

#### B. HTTP Mode with Docker

```bash
# Start HTTP server in Docker
docker run --rm -d \
  --name surrealmcp-http \
  -p 8080:8080 \
  surrealdb/surrealmcp:latest start \
  --bind-address 0.0.0.0:8080 \
  --server-url http://localhost:8080 \
  --auth-disabled

# Check logs
docker logs surrealmcp-http

# Test health endpoint
curl http://localhost:8080/health
```

#### C. Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  surrealdb:
    image: surrealdb/surrealdb:latest
    command: start --user root --pass root
    ports:
      - "8000:8000"

  surrealmcp:
    image: surrealdb/surrealmcp:latest
    command: start --bind-address 0.0.0.0:8080 --auth-disabled
    environment:
      SURREALDB_URL: ws://surrealdb:8000/rpc
      SURREALDB_NS: test
      SURREALDB_DB: test
      SURREALDB_USER: root
      SURREALDB_PASS: root
    ports:
      - "8080:8080"
    depends_on:
      - surrealdb
```

Run with:
```bash
docker-compose up
```

### 2.3 Test with MCP Inspector (Docker)

#### STDIO Mode

```bash
# Create MCP Inspector configuration
cat > mcp-inspector-docker-stdio.json << EOF
{
  "mcpServers": {
    "surrealmcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "surrealdb/surrealmcp:latest",
        "start"
      ]
    }
  }
}
EOF

# Run MCP Inspector
npx @modelcontextprotocol/inspector mcp-inspector-docker-stdio.json
```

#### HTTP Mode

```bash
# First, ensure HTTP server is running (from step 2.2.B)
# Then create MCP Inspector configuration
cat > mcp-inspector-docker-http.json << EOF
{
  "mcpServers": {
    "surrealmcp": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
EOF

# Run MCP Inspector
npx @modelcontextprotocol/inspector mcp-inspector-docker-http.json
```

### 2.4 Volume Mounting for Persistent Data

```bash
# Create local directories
mkdir -p ./data ./logs

# Run with volumes
docker run --rm -it \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/logs \
  -e SURREALDB_URL="file:/data/database.db" \
  surrealdb/surrealmcp:latest start
```

## Part 3: Advanced Testing Scenarios

### 3.1 Authentication Testing

```bash
# Test with authentication enabled (HTTP mode)
surrealmcp start \
  --bind-address 127.0.0.1:8080 \
  --server-url http://localhost:8080 \
  --auth-server https://auth.example.com \
  --auth-audience https://api.example.com/

# Test authentication discovery
curl http://localhost:8080/.well-known/oauth-protected-resource
```

### 3.2 Rate Limiting Testing

```bash
# Start with custom rate limits
surrealmcp start \
  --bind-address 127.0.0.1:8080 \
  --auth-disabled \
  --rate-limit-rps 10 \
  --rate-limit-burst 20

# Test rate limiting with rapid requests
for i in {1..30}; do
  curl -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' &
done
```

### 3.3 Cloud Connection Testing

```bash
# Test SurrealDB Cloud connection (requires cloud credentials)
export SURREAL_MCP_CLOUD_ACCESS_TOKEN="your_token"
export SURREAL_MCP_CLOUD_REFRESH_TOKEN="your_refresh_token"

surrealmcp start
# Then use connect_endpoint('cloud:instance_id', 'namespace', 'database')
```

### 3.4 Performance Testing

```bash
# Start server with metrics enabled
surrealmcp start --bind-address 127.0.0.1:8080 --auth-disabled

# Monitor metrics (if exposed)
# Check logs for performance metrics
```

## Part 4: Validation Checklist

### Basic Functionality
- [ ] Server starts successfully in all modes (STDIO, HTTP, Unix)
- [ ] Can connect to memory database
- [ ] Can connect to file-based database
- [ ] Can connect to remote SurrealDB instance
- [ ] Health endpoint responds (HTTP mode)

### MCP Inspector Integration
- [ ] Inspector connects successfully
- [ ] Tools are listed correctly
- [ ] Can execute queries
- [ ] Can perform CRUD operations
- [ ] Connection switching works

### Docker Deployment
- [ ] Container starts successfully
- [ ] Volumes mount correctly
- [ ] Environment variables are recognized
- [ ] Can connect from host machine

### Advanced Features
- [ ] Authentication works (if configured)
- [ ] Rate limiting functions correctly
- [ ] Cloud connections work (if applicable)
- [ ] Graceful shutdown works (Ctrl+C twice)

## Troubleshooting

### Common Issues and Solutions

1. **Connection Refused**
   - Check if SurrealDB is running
   - Verify endpoint URL and port
   - Check firewall settings

2. **Authentication Failed**
   - Verify credentials
   - Check token configuration
   - Validate audience settings

3. **MCP Inspector Connection Issues**
   - Ensure server is running
   - Check configuration file syntax
   - Verify network connectivity

4. **Docker Permission Errors**
   - Run with appropriate user permissions
   - Check volume mount permissions
   - Verify Docker daemon is running

### Debug Mode

Enable debug logging:
```bash
# Set log level
export RUST_LOG=debug
surrealmcp start

# Or for Docker
docker run --rm -it \
  -e RUST_LOG=debug \
  surrealdb/surrealmcp:latest start
```

### Log Files

Check logs in:
- Standalone: Current directory or `/logs`
- Docker: Use `docker logs <container_name>`
- With volumes: Check mounted log directory

## Example Test Session

```bash
# 1. Start SurrealDB
docker run -d --name surrealdb -p 8000:8000 \
  surrealdb/surrealdb:latest start --user root --pass root

# 2. Start SurrealMCP HTTP server
docker run -d --name surrealmcp \
  -p 8080:8080 \
  --link surrealdb:surrealdb \
  surrealdb/surrealmcp:latest start \
  --bind-address 0.0.0.0:8080 \
  --endpoint ws://surrealdb:8000/rpc \
  --ns test --db test \
  --user root --pass root \
  --auth-disabled

# 3. Start MCP Inspector
npx @modelcontextprotocol/inspector

# 4. Connect to http://localhost:8080/mcp in Inspector
# 5. Test various tools and operations
# 6. Clean up
docker stop surrealmcp surrealdb
docker rm surrealmcp surrealdb
```

## Additional Resources

- [SurrealDB Documentation](https://surrealdb.com/docs)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [MCP Inspector GitHub](https://github.com/modelcontextprotocol/inspector)
- [SurrealMCP GitHub Issues](https://github.com/surrealdb/surrealmcp/issues)