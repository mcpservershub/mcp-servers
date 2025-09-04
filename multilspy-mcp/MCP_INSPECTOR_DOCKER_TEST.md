# Testing MCP Server Docker Container with MCP Inspector

## Prerequisites

1. **Docker installed and running**
   ```bash
   docker --version
   docker ps  # Should not error
   ```

2. **Node.js 18+ and MCP Inspector installed**
   ```bash
   # Install MCP Inspector if not already installed
   npm install -g @modelcontextprotocol/inspector
   
   # Verify installation
   mcp-inspector --version
   ```

3. **Docker image built**
   ```bash
   cd /home/santosh/lsp-server/multilspy-mcp-server
   
   # Build the Docker image
   docker build -t multilspy-mcp-server:latest .
   
   # Verify image exists
   docker images | grep multilspy-mcp-server
   ```

## Step 1: Prepare Test Workspace

```bash
# Create test workspace with sample files
mkdir -p workspace/examples

# Create a Python test file
cat > workspace/examples/test.py << 'EOF'
"""Sample Python file for testing LSP features."""

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

def main():
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"5 + 3 = {result}")
    
    product = calc.multiply(4, 7)
    print(f"4 * 7 = {product}")

if __name__ == "__main__":
    main()
EOF

# Create a TypeScript test file
cat > workspace/examples/test.ts << 'EOF'
interface Person {
    name: string;
    age: number;
    email?: string;
}

class User implements Person {
    name: string;
    age: number;
    email?: string;
    
    constructor(name: string, age: number) {
        this.name = name;
        this.age = age;
    }
    
    greet(): string {
        return `Hello, my name is ${this.name}`;
    }
}

function createUser(name: string, age: number): User {
    return new User(name, age);
}

const user = createUser("Alice", 30);
console.log(user.greet());
EOF
```

## Step 2: Start MCP Inspector

```bash
# Navigate to project directory
cd /home/santosh/lsp-server/multilspy-mcp-server

# Launch MCP Inspector with Docker configuration
mcp-inspector docker_inspector_config.json
```

The inspector will open in your browser at `http://localhost:5173`

## Step 3: Connect to the Docker Container

1. **In the MCP Inspector web interface:**
   - You should see "multilspy-docker" in the server dropdown
   - Click "Connect"
   - Wait for "Connected" status (green indicator)

2. **Check connection logs:**
   - Look for initialization messages in the console
   - You should see: "Initialized LSP manager for workspace: /workspace"

## Step 4: Test MCP Tools

### Test 1: Initialize Workspace
```json
Tool: lsp_initialize
Arguments:
{
  "workspace_root": "/workspace",
  "cache_dir": "/cache"
}
```

**Expected Response:**
```json
{
  "success": true,
  "workspace": "/workspace",
  "cache_dir": "/cache",
  "languages_available": ["python", "typescript", "javascript", ...]
}
```

### Test 2: Detect Language
```json
Tool: lsp_detect_language
Arguments:
{
  "file_path": "examples/test.py"
}
```

**Expected Response:**
```json
{
  "success": true,
  "language": "python",
  "confidence": 1.0
}
```

### Test 3: Get Document Symbols
```json
Tool: code_document_symbols
Arguments:
{
  "file_path": "examples/test.py",
  "language": "python"
}
```

**Expected Response:**
```json
{
  "success": true,
  "symbols": [
    {
      "name": "Calculator",
      "kind": "Class",
      "range": {...}
    },
    {
      "name": "add",
      "kind": "Method",
      "range": {...}
    },
    ...
  ]
}
```

### Test 4: Navigate to Definition
```json
Tool: code_navigate_definition
Arguments:
{
  "file_path": "examples/test.py",
  "line": 23,
  "column": 10,
  "language": "python"
}
```
*Note: Line 24 in editor = line 23 (0-indexed), clicking on `Calculator` in `calc = Calculator()`*

**Expected Response:**
```json
{
  "success": true,
  "locations": [
    {
      "file": "examples/test.py",
      "line": 2,
      "column": 6
    }
  ]
}
```

### Test 5: Get Completions
```json
Tool: code_complete
Arguments:
{
  "file_path": "examples/test.py",
  "line": 24,
  "column": 17,
  "language": "python",
  "allow_incomplete": false,
  "trigger_character": "."
}
```
*Note: Line 25 in editor = line 24 (0-indexed), position after `calc.`*

**Expected Response:**
```json
{
  "success": true,
  "completions": [
    {
      "label": "add",
      "kind": "Method",
      "detail": "(a: int, b: int) -> int"
    },
    {
      "label": "multiply",
      "kind": "Method",
      "detail": "(a: int, b: int) -> int"
    },
    {
      "label": "divide",
      "kind": "Method",
      "detail": "(a: float, b: float) -> float"
    },
    {
      "label": "result",
      "kind": "Property"
    }
  ]
}
```

### Test 6: Get Hover Information
```json
Tool: code_get_hover
Arguments:
{
  "file_path": "examples/test.py",
  "line": 9,
  "column": 8,
  "language": "python"
}
```
*Note: Line 10 in editor = line 9 (0-indexed), hovering over the `add` method definition*

**Expected Response:**
```json
{
  "success": true,
  "hover": {
    "contents": "def add(self, a: int, b: int) -> int\n\nAdd two numbers.",
    "range": {...}
  }
}
```

### Test 7: Search Workspace
```json
Tool: code_search_workspace
Arguments:
{
  "query": "Calculator",
  "language": "python",
  "limit": 10
}
```

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "name": "Calculator",
      "kind": "Class",
      "location": {
        "file": "examples/test.py",
        "line": 3
      }
    }
  ]
}
```

### Test 8: Find References
```json
Tool: code_find_references
Arguments:
{
  "file_path": "examples/test.py",
  "line": 2,
  "column": 6,
  "language": "python"
}
```
*Note: Line 3 in editor = line 2 (0-indexed), finding references to the Calculator class definition*

**Expected Response:**
```json
{
  "success": true,
  "locations": [
    {
      "file": "examples/test.py",
      "line": 23,
      "column": 10
    }
  ]
}
```

## Step 5: Monitor Docker Container

While testing, you can monitor the Docker container in another terminal:

```bash
# View running containers
docker ps | grep multilspy-mcp

# Follow container logs (if using docker-compose)
docker-compose logs -f

# Or watch Docker logs directly
docker logs -f $(docker ps -q -f ancestor=multilspy-mcp-server:latest)
```

## Step 6: Test Session Persistence

### Save Session
```json
Tool: lsp_save_session
Arguments: {}
```

**Expected Response:**
```json
{
  "success": true,
  "session_file": "/cache/session_20240828_123456.json",
  "message": "Session saved successfully"
}
```

### Load Session
```json
Tool: lsp_load_session
Arguments: {
  "session_file": "/cache/session_20240828_123456.json"
}
```

## Troubleshooting

### Container doesn't start
```bash
# Check if image exists
docker images | grep multilspy-mcp-server

# Rebuild if needed
docker build -t multilspy-mcp-server:latest .

# Test container directly
docker run --rm multilspy-mcp-server:latest python -c "from multilspy_mcp import server; print('OK')"
```

### Connection fails in MCP Inspector
```bash
# Test the container can run the MCP server
docker run --rm -it \
  -v $(pwd)/workspace:/workspace \
  multilspy-mcp-server:latest \
  python -m mcp run multilspy_mcp.server:mcp
```

### No completions or symbols
This is expected with the minimal Dockerfile since no language servers are installed. To get full functionality:

```bash
# Build with Python language server support
docker build -f Dockerfile.with-python-lsp -t multilspy-mcp-server:latest .
```

### Permission issues
```bash
# Ensure workspace directory has correct permissions
chmod -R 755 workspace/

# If using Docker Desktop on Mac/Windows, check file sharing settings
```

## Expected Behavior Summary

With **minimal Dockerfile** (no language servers):
- ✅ Connection succeeds
- ✅ Initialization works
- ✅ File language detection works
- ⚠️ Code intelligence features return empty results (expected)

With **Python LSP Dockerfile**:
- ✅ All above features work
- ✅ Python code intelligence fully functional
- ⚠️ Other languages return empty results (expected)

## Clean Up

After testing:

```bash
# Stop any running containers
docker stop $(docker ps -q -f ancestor=multilspy-mcp-server:latest)

# Remove test image (optional)
docker rmi multilspy-mcp-server:latest

# Clean up cache
rm -rf /tmp/mcp-lsp-cache
```

## Complete MCP Tools Reference

### Important Notes About Arguments

#### Line and Column Indexing
**All line and column numbers are 0-indexed!**
- Line 1 in your editor = line 0 in the API
- Column 1 in your editor = column 0 in the API

#### File Paths
- Use **relative paths** from the workspace root
- ✅ Correct: `"examples/test.py"`
- ❌ Wrong: `"/workspace/examples/test.py"`

### Complete List of Tools with All Arguments

#### 1. `lsp_initialize`
Initialize the LSP manager for a workspace.

**Required:**
- `workspace_root` (string): Path to workspace root

**Optional:**
- `cache_dir` (string): Directory for caching

```json
{
  "workspace_root": "/workspace",
  "cache_dir": "/cache"
}
```

#### 2. `lsp_detect_language`
Detect the programming language of a file.

**Required:**
- `file_path` (string): Relative path to the file

```json
{
  "file_path": "examples/test.py"
}
```

#### 3. `code_navigate_definition`
Navigate to where a symbol is defined.

**Required:**
- `file_path` (string): Relative path to the file
- `line` (integer): Line number (0-indexed)
- `column` (integer): Column number (0-indexed)

**Optional:**
- `language` (string): Programming language hint

```json
{
  "file_path": "examples/test.py",
  "line": 23,
  "column": 10,
  "language": "python"
}
```

#### 4. `code_find_references`
Find all places where a symbol is referenced.

**Required:**
- `file_path` (string): Relative path to the file
- `line` (integer): Line number (0-indexed)
- `column` (integer): Column number (0-indexed)

**Optional:**
- `language` (string): Programming language hint

```json
{
  "file_path": "examples/test.py",
  "line": 2,
  "column": 6,
  "language": "python"
}
```

#### 5. `code_complete`
Get code completion suggestions.

**Required:**
- `file_path` (string): Relative path to the file
- `line` (integer): Line number (0-indexed)
- `column` (integer): Column number (0-indexed)

**Optional:**
- `language` (string): Programming language hint
- `allow_incomplete` (boolean): Allow incomplete results (default: false)
- `trigger_character` (string): Character that triggered completion (e.g., ".")

```json
{
  "file_path": "examples/test.py",
  "line": 24,
  "column": 17,
  "language": "python",
  "allow_incomplete": false,
  "trigger_character": "."
}
```

#### 6. `code_get_hover`
Get hover information for a symbol.

**Required:**
- `file_path` (string): Relative path to the file
- `line` (integer): Line number (0-indexed)
- `column` (integer): Column number (0-indexed)

**Optional:**
- `language` (string): Programming language hint

```json
{
  "file_path": "examples/test.py",
  "line": 9,
  "column": 8,
  "language": "python"
}
```

#### 7. `code_document_symbols`
Get all symbols in a document.

**Required:**
- `file_path` (string): Relative path to the file

**Optional:**
- `language` (string): Programming language hint

```json
{
  "file_path": "examples/test.py",
  "language": "python"
}
```

#### 8. `code_search_workspace`
Search for symbols across the workspace.

**Required:**
- `query` (string): Search query string

**Optional:**
- `language` (string): Limit to specific language
- `limit` (integer): Max results (default: 100)

```json
{
  "query": "Calculator",
  "language": "python",
  "limit": 50
}
```

#### 9. `lsp_save_session`
Save the current session state.

**No arguments required:**
```json
{}
```

#### 10. `lsp_load_session`
Load a previously saved session.

**Required:**
- `session_file` (string): Path to session file

```json
{
  "session_file": "/cache/session_20240828_123456.json"
}
```

### Symbol Kind Reference
When symbols are returned, the `kind` field uses these numeric values:
- 5: Class
- 6: Method
- 7: Property
- 12: Function
- 13: Variable
- (See server documentation for complete list)

### Supported Languages
- `"python"`, `"java"`, `"rust"`, `"csharp"`, `"cpp"`
- `"typescript"`, `"javascript"`, `"go"`, `"ruby"`
- `"dart"`, `"kotlin"`