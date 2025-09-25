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

# COBOL test (basic COBOL syntax)
cat > workspace/tests/TEST-PROGRAM.COB << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEST-PROGRAM.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MESSAGE         PIC X(30) VALUE 'Hello from COBOL'.
       01  WS-COUNTER         PIC 9(3) VALUE ZERO.

       PROCEDURE DIVISION.
       MAIN-PARAGRAPH.
           DISPLAY WS-MESSAGE
           PERFORM TEST-LOOP 5 TIMES
           STOP RUN.

       TEST-LOOP.
           ADD 1 TO WS-COUNTER
           DISPLAY 'Counter: ' WS-COUNTER.
EOF
```

### COBOL Testing with SuperBOL

The MCP server includes comprehensive COBOL support via SuperBOL integration. Test COBOL functionality separately:

#### Step 1: COBOL Test Setup

```bash
# Ensure COBOL test files are available
cd /home/santosh/lsp-server/multilspy-mcp-server

# Create COBOL workspace directory
mkdir -p workspace/cobol

# Copy COBOL test files if available
cp /home/santosh/lsp-server/test-colbol/*.COB workspace/cobol/ 2>/dev/null || true
cp /home/santosh/lsp-server/test-colbol/*.CPY workspace/cobol/ 2>/dev/null || true
```

#### Step 2: Test COBOL Language Detection

In MCP Inspector, test COBOL file detection:

```json
Tool: lsp_detect_language
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB"
}
```

Expected response: `"language": "cobol"`

#### Step 3: Test COBOL Document Symbols

```json
Tool: code_document_symbols
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB"
}
```

Expected symbols include:
- Program names (CUSTOMER-MGMT)
- Paragraph names (MAIN-PROGRAM, DISPLAY-MENU, ADD-CUSTOMER)
- Data items (CUSTOMER-RECORD, WS-CUSTOMER-ID)
- File definitions (CUSTOMER-FILE)

#### Step 4: Test COBOL Navigation

Navigate to paragraph definition:

```json
Tool: code_navigate_definition
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB",
  "line": 49,
  "column": 18
}
```

#### Step 5: Test COBOL Hover Information

Get hover info for COBOL data structures:

```json
Tool: code_get_hover
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB",
  "line": 27,
  "column": 12
}
```

#### Step 6: Test COBOL References

Find all references to a COBOL data item:

```json
Tool: code_find_references
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB",
  "line": 19,
  "column": 10
}
```

#### Step 7: Test COBOL Code Completion

Get COBOL keyword and data name completions:

```json
Tool: code_complete
Arguments:
{
  "file_path": "cobol/CUSTOMER.COB",
  "line": 50,
  "column": 20
}
```

#### Step 8: Test COBOL Workspace Search

Search for COBOL symbols across workspace:

```json
Tool: code_search_workspace
Arguments:
{
  "query": "CUSTOMER",
  "language": "cobol",
  "limit": 10
}
```

### COBOL Docker Testing

Test COBOL functionality in Docker environment:

```bash
# Build Docker image with COBOL support
docker build -t multilspy-mcp-server:cobol .

# Run with COBOL test files mounted
docker run -v /home/santosh/lsp-server/test-colbol:/workspace/cobol \
           -v /tmp/mcp-lsp-cache:/cache \
           -e WORKSPACE_ROOT=/workspace \
           -e MCP_LSP_CACHE_DIR=/cache \
           -e LOG_LEVEL=DEBUG \
           multilspy-mcp-server:cobol \
           python -c "
from multilspy_mcp.lsp_manager import LSPManager
import os
os.chdir('/workspace')
lsp = LSPManager('/workspace')
print('COBOL Detection Test:')
for f in ['/workspace/cobol/CUSTOMER.COB', '/workspace/cobol/INVENTORY.COB']:
    if os.path.exists(f):
        lang = lsp.detect_language(f)
        print(f'  {f}: {lang}')
    else:
        print(f'  {f}: File not found')
"
```

### COBOL Test Configuration for MCP Inspector

Create `cobol_test_config.json`:

```json
{
  "mcpServers": {
    "multilspy-cobol": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/home/santosh/lsp-server/test-colbol:/workspace/cobol:ro",
        "-v", "/tmp/mcp-lsp-cache:/cache",
        "-e", "WORKSPACE_ROOT=/workspace",
        "-e", "MCP_LSP_CACHE_DIR=/cache",
        "-e", "LOG_LEVEL=INFO",
        "multilspy-mcp-server",
        "python", "-m", "multilspy_mcp.server"
      ]
    }
  }
}
```

Run COBOL tests with:

```bash
mcp-inspector cobol_test_config.json
```

### COBOL Error Handling Tests

Test graceful handling when SuperBOL is not available:

1. **Expected Behavior**: When SuperBOL is not installed, COBOL tools should:
   - Detect COBOL files correctly (Language.COBOL)
   - Return clear error messages: "SuperBOL not found"
   - Not crash or hang
   - Provide helpful installation guidance

2. **Test Error Response**:
   ```json
   {
     "error": "SuperBOL not found. Please install SuperBOL or ensure it's in PATH",
     "language_detected": "cobol",
     "file_path": "cobol/CUSTOMER.COB"
   }
   ```

### COBOL Performance Considerations

- COBOL files with extensive copybook includes may have longer processing times
- SuperBOL supports multiple COBOL dialects (GnuCOBOL, IBM Enterprise COBOL, Micro Focus)
- Test with both small programs and large enterprise COBOL applications

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
test_command "python -c 'from multilspy_mcp import superbol_client'" "SuperBOL client module"

# COBOL support tests
echo -e "\n🔧 Testing COBOL Support..."
test_command "python -c 'from multilspy_mcp.models import Language; print(Language.COBOL)'" "COBOL language enum"
test_command "python -c 'from multilspy_mcp.lsp_manager import LSPManager; lsp = LSPManager(\"/tmp\"); print(lsp.is_cobol_language(lsp.detect_language(\"test.cob\")))'" "COBOL detection"

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