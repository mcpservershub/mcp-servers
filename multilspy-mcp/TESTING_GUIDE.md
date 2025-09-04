# Testing Guide for MultilsPy MCP Server

This guide provides step-by-step instructions for testing the MultilsPy MCP Server both as a Python application and in a Docker container using MCP Inspector.

## Prerequisites

- Python 3.10+ (preferably 3.12)
- Docker and Docker Compose (for container testing)
- Node.js 18+ (for MCP Inspector)
- Git

## Part 1: Testing as a Python Application

### Step 1: Setup Python Environment

```bash
# Navigate to the project directory
cd /home/santosh/lsp-server/multilspy-mcp-server

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install the package with all dependencies
pip install -e .

# Verify installation
python -c "from multilspy_mcp import server, lsp_manager, models; print('✓ Modules imported successfully')"
```

### Step 2: Install MCP Inspector

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Verify installation
mcp-inspector --version
```

### Step 3: Create Test Configuration

Create a file `test_config.json`:

```json
{
  "mcpServers": {
    "multilspy-local": {
      "command": "python",
      "args": ["-m", "mcp", "run", "multilspy_mcp.server:mcp"],
      "cwd": "/home/santosh/lsp-server/multilspy-mcp-server",
      "env": {
        "WORKSPACE_ROOT": "/home/santosh/lsp-server/multilspy-mcp-server/workspace",
        "MCP_LSP_CACHE_DIR": "/tmp/mcp-lsp-cache",
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "/home/santosh/lsp-server/multilspy-mcp-server"
      }
    }
  }
}
```

### Step 4: Run MCP Inspector with Python App

```bash
# Make sure you're in the project directory with activated venv
cd /home/santosh/lsp-server/multilspy-mcp-server
source .venv/bin/activate

# Start MCP Inspector
mcp-inspector test_config.json

# The inspector will open in your browser (usually http://localhost:5173)
```

### Step 5: Test MCP Tools in Inspector

In the MCP Inspector web interface:

1. **Connect to Server**
   - Select "multilspy-local" from the dropdown
   - Click "Connect"
   - You should see "Connected" status

2. **Initialize Workspace**
   ```json
   Tool: lsp_initialize
   Arguments:
   {
     "workspace_root": "/home/santosh/lsp-server/multilspy-mcp-server/workspace",
     "cache_dir": "/tmp/mcp-lsp-cache"
   }
   ```

3. **Test Language Detection**
   ```json
   Tool: lsp_detect_language
   Arguments:
   {
     "file_path": "examples/example.py"
   }
   ```

4. **Test Code Navigation**
   ```json
   Tool: code_navigate_definition
   Arguments:
   {
     "file_path": "examples/example.py",
     "line": 50,
     "column": 10,
     "language": "python"
   }
   ```

5. **Test Code Completion**
   ```json
   Tool: code_complete
   Arguments:
   {
     "file_path": "examples/example.py",
     "line": 16,
     "column": 14,
     "language": "python"
   }
   ```

6. **Test Document Symbols**
   ```json
   Tool: code_document_symbols
   Arguments:
   {
     "file_path": "examples/example.py",
     "language": "python"
   }
   ```

7. **Test Workspace Search**
   ```json
   Tool: code_search_workspace
   Arguments:
   {
     "query": "Calculator",
     "language": "python",
     "limit": 10
   }
   ```

## Part 2: Testing with Docker Container

### Step 1: Build Docker Image

```bash
cd /home/santosh/lsp-server/multilspy-mcp-server

# Build the Docker image
docker build -t multilspy-mcp-server:latest .

# Verify the image was created
docker images | grep multilspy-mcp-server
```

### Step 2: Create Docker Test Configuration

Create `docker_test_config.json`:

```json
{
  "mcpServers": {
    "multilspy-docker": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/home/santosh/lsp-server/multilspy-mcp-server/workspace:/workspace:ro",
        "-v", "/tmp/mcp-lsp-cache:/cache",
        "-e", "WORKSPACE_ROOT=/workspace",
        "-e", "MCP_LSP_CACHE_DIR=/cache",
        "-e", "LOG_LEVEL=DEBUG",
        "multilspy-mcp-server:latest",
        "python", "-m", "mcp", "run", "multilspy_mcp.server:mcp"
      ]
    }
  }
}
```

### Step 3: Test with Docker Compose (Alternative)

```bash
# Start the service with docker-compose
docker-compose up -d

# Check if container is running
docker-compose ps

# View logs
docker-compose logs -f multilspy-mcp-server
```

Create `docker_compose_config.json` for MCP Inspector:

```json
{
  "mcpServers": {
    "multilspy-compose": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "multilspy-mcp",
        "python", "-m", "mcp", "run", "multilspy_mcp.server:mcp"
      ]
    }
  }
}
```

### Step 4: Run MCP Inspector with Docker

```bash
# For standalone Docker container
mcp-inspector docker_test_config.json

# For Docker Compose
mcp-inspector docker_compose_config.json
```

## Part 3: Advanced Testing Scenarios

### Test Multiple Languages

Create test files in the workspace for different languages:

```bash
# Create test files
mkdir -p workspace/tests

# Python test
cat > workspace/tests/test.py << 'EOF'
def hello_world():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
EOF

# TypeScript test
cat > workspace/tests/test.ts << 'EOF'
interface Person {
    name: string;
    age: number;
}

function greet(person: Person): string {
    return `Hello, ${person.name}!`;
}
EOF

# Go test (if Go is installed)
cat > workspace/tests/test.go << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
EOF
```

### Performance Testing

Test with larger files and measure response times:

```python
# Create a performance test script
cat > test_performance.py << 'EOF'
import time
import json
import asyncio
from multilspy_mcp.server import (
    get_document_symbols,
    get_completions,
    search_workspace_symbols
)

async def test_performance():
    # Test document symbols
    start = time.time()
    result = get_document_symbols(
        file_path="examples/example.py",
        language="python"
    )
    print(f"Document symbols: {time.time() - start:.3f}s")
    
    # Test completions
    start = time.time()
    result = get_completions(
        file_path="examples/example.py",
        line=20,
        column=10,
        language="python"
    )
    print(f"Completions: {time.time() - start:.3f}s")
    
    # Test workspace search
    start = time.time()
    result = search_workspace_symbols(
        query="def",
        language="python"
    )
    print(f"Workspace search: {time.time() - start:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_performance())
EOF

# Run performance test
python test_performance.py
```

### Session Persistence Testing

Test session save and restore:

```bash
# In MCP Inspector, test session persistence:

# 1. Save current session
Tool: lsp_save_session
Arguments: {}

# Note the session_file path in the response

# 2. Restart the server (disconnect and reconnect in Inspector)

# 3. Load the saved session
Tool: lsp_load_session
Arguments: {
  "session_file": "/path/to/saved/session.json"
}
```

## Part 4: Debugging and Troubleshooting

### Enable Debug Logging

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG
export PYTHONUNBUFFERED=1

# Run with verbose output
python -m mcp run multilspy_mcp.server:mcp 2>&1 | tee debug.log
```

### Common Issues and Solutions

1. **MultilsPy not found**
   ```bash
   pip install multilspy>=0.0.15
   ```

2. **Language server not starting**
   - Check if the language runtime is installed
   - For Python: `pip install python-lsp-server[all]`
   - For TypeScript: `npm install -g typescript typescript-language-server`

3. **Connection refused in Docker**
   - Ensure container is running: `docker ps`
   - Check container logs: `docker logs <container-id>`
   - Verify volume mounts are correct

4. **No completions returned**
   - Some language servers need files to be saved
   - Try with a real project with proper structure
   - Check language server capabilities

### Monitoring Container

```bash
# Watch container resource usage
docker stats multilspy-mcp

# Follow container logs
docker logs -f multilspy-mcp

# Execute commands in running container
docker exec -it multilspy-mcp bash

# Check installed language servers
docker exec multilspy-mcp which pylsp
docker exec multilspy-mcp which typescript-language-server
```

## Part 5: Automated Testing Script

Create an automated test script `run_tests.sh`:

```bash
#!/bin/bash

echo "🧪 MultilsPy MCP Server Test Suite"
echo "===================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test function
test_command() {
    if eval "$1"; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

# Python environment tests
echo -e "\n📦 Testing Python Environment..."
test_command "python --version | grep -E 'Python 3.(1[0-2]|11|12)'" "Python version check"
test_command "python -c 'import mcp'" "MCP package installed"
test_command "python -c 'import multilspy'" "MultilsPy installed"
test_command "python -c 'import pydantic'" "Pydantic installed"

# Module import tests
echo -e "\n📚 Testing Module Imports..."
test_command "python -c 'from multilspy_mcp import server'" "Server module"
test_command "python -c 'from multilspy_mcp import lsp_manager'" "LSP Manager module"
test_command "python -c 'from multilspy_mcp import models'" "Models module"

# Basic functionality tests
echo -e "\n⚡ Testing Basic Functionality..."
test_command "python tests/test_server.py" "Test suite"

# Docker tests (if Docker is available)
if command -v docker &> /dev/null; then
    echo -e "\n🐳 Testing Docker..."
    test_command "docker build -t multilspy-mcp-test ." "Docker build"
    test_command "docker run --rm multilspy-mcp-test python -c 'from multilspy_mcp import server'" "Docker run"
fi

echo -e "\n===================================="
echo "Test suite complete!"
```

Make it executable:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Expected Results

When everything is working correctly, you should see:

1. **MCP Inspector Connection**: Green "Connected" status
2. **Tool Responses**: JSON responses with `"success": true`
3. **Language Detection**: Correctly identifies file languages
4. **Code Navigation**: Returns location arrays with file paths and positions
5. **Completions**: Returns arrays of completion items
6. **Symbol Search**: Returns matching symbols across workspace

## Next Steps

After successful testing:

1. Test with your actual project codebase
2. Try different programming languages
3. Measure performance with larger codebases
4. Test session persistence across restarts
5. Deploy to production environment

## Support

If you encounter issues:

1. Check the debug logs (`LOG_LEVEL=DEBUG`)
2. Verify all dependencies are installed
3. Ensure language servers are properly configured
4. Check file permissions for workspace and cache directories
5. Review the error messages in MCP Inspector console