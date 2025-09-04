# Universal CTags MCP Server

A fully-functional Model Context Protocol (MCP) server that integrates Universal CTags for advanced code navigation, search, and analysis capabilities. This server enables AI assistants to understand code structure and navigate codebases efficiently across 100+ programming languages.

## Features

- **Code Indexing**: Generate and update CTags indexes for any codebase
- **Symbol Search**: Find functions, classes, variables with regex support
- **Code Navigation**: Jump to definitions, list file symbols
- **Code Analysis**: Generate file outlines and analyze code structure
- **Multi-Language Support**: Works with 100+ programming languages supported by Universal CTags
- **Incremental Updates**: Efficiently update tags for modified files
- **Flexible Matching**: Exact, partial, and regex pattern matching

## Prerequisites

- Python 3.10 or higher
- Universal CTags installed (`ctags` command available)
  - Ubuntu/Debian: `sudo apt-get install universal-ctags`
  - macOS: `brew install universal-ctags`
  - Windows: Download from [Universal CTags releases](https://github.com/universal-ctags/ctags/releases)
- python-ctags3 library: `pip install python-ctags3`

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-ctags-mcp-server.git
cd universal-ctags-mcp-server

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using pip

```bash
pip install universal-ctags-mcp-server
```

## Configuration

### MCP Configuration (Claude Desktop or other MCP clients)

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "universal-ctags": {
      "command": "python",
      "args": ["-m", "ctags_mcp.server"],
      "env": {
        "CTAGS_BINARY": "/usr/local/bin/ctags"
      }
    }
  }
}
```

### Environment Variables

- `CTAGS_BINARY`: Path to ctags executable (default: `ctags`)

## Available Tools

### Indexing Tools

#### `generate_tags`
Generate a CTags index for your project.

```python
# Example usage
result = await generate_tags(
    path="./src",
    recursive=True,
    languages=["python", "javascript"],
    exclude_patterns=["*.test.js", "__pycache__"],
    output_file="./project.tags"
)
```

**Parameters:**
- `path` (str): Directory or file to index
- `recursive` (bool): Recursively index subdirectories
- `languages` (list): Specific languages to index
- `exclude_patterns` (list): Patterns to exclude
- `output_file` (str): Output tags file path
- `extra_options` (list): Additional ctags options

#### `update_tags`
Incrementally update tags for modified files.

```python
result = await update_tags(
    tags_file="./tags",
    modified_files=["src/main.py", "src/utils.py"]
)
```

### Search Tools

#### `find_symbol`
Search for symbols with flexible matching options.

```python
symbols = await find_symbol(
    symbol_name="handle.*Request",
    tags_file="./tags",
    match_type="regex",
    case_sensitive=False,
    limit=20
)
```

**Parameters:**
- `symbol_name` (str): Symbol name or pattern
- `tags_file` (str): Path to tags file
- `match_type` (str): "exact", "partial", or "regex"
- `case_sensitive` (bool): Case-sensitive matching
- `symbol_kinds` (list): Filter by symbol types
- `limit` (int): Maximum results

#### `find_references`
Find all references to a symbol.

```python
refs = await find_references(
    symbol_name="DatabaseConnection",
    scope_file="./src/db.py",  # Optional
    tags_file="./tags"
)
```

### Navigation Tools

#### `go_to_definition`
Navigate to a symbol's definition.

```python
definition = await go_to_definition(
    symbol_name="MyClass",
    current_file="./src/main.py",
    tags_file="./tags"
)
```

#### `list_symbols_in_file`
List all symbols in a specific file.

```python
symbols = await list_symbols_in_file(
    file_path="./src/main.py",
    tags_file="./tags",
    group_by_kind=True
)
```

### Analysis Tools

#### `get_file_outline`
Generate a structured outline of a file.

```python
outline = await get_file_outline(
    file_path="./src/main.py",
    tags_file="./tags",
    include_private=False,
    max_depth=3
)
```

### Management Tools

#### `list_tags_files`
Find all tags files in workspace.

```python
tags_files = await list_tags_files(
    search_path="./",
    include_stats=True
)
```

#### `get_tags_info`
Get detailed information about a tags file.

```python
info = await get_tags_info(tags_file="./project.tags")
```

#### `validate_tags_file`
Validate tags file integrity.

```python
result = await validate_tags_file(
    tags_file="./tags",
    check_files_exist=True
)
```

## Usage Examples

### Basic Workflow

1. **Generate tags for your project:**
```python
# Index entire project
await generate_tags(path=".", recursive=True, output_file="project.tags")
```

2. **Search for a symbol:**
```python
# Find all functions starting with "test_"
results = await find_symbol(
    symbol_name="test_",
    match_type="partial",
    symbol_kinds=["function"]
)
```

3. **Navigate to definition:**
```python
# Jump to class definition
definition = await go_to_definition(symbol_name="MyClass")
print(f"Found at {definition['definition']['file']}:{definition['definition']['line']}")
```

4. **Get file structure:**
```python
# Analyze file structure
outline = await get_file_outline(file_path="main.py")
print(f"Classes: {len(outline['outline']['classes'])}")
print(f"Functions: {len(outline['outline']['functions'])}")
```

### Advanced Usage

#### Working with Multiple Languages
```python
# Index only Python and JavaScript files
await generate_tags(
    path=".",
    languages=["python", "javascript"],
    exclude_patterns=["node_modules", "*.min.js"]
)
```

#### Regex Symbol Search
```python
# Find all symbols matching a regex pattern
symbols = await find_symbol(
    symbol_name="^handle.*Event$",
    match_type="regex"
)
```

#### Incremental Updates
```python
# Update tags for changed files only
await update_tags(
    tags_file="project.tags",
    modified_files=["src/new_feature.py", "src/updated_module.py"]
)
```

## Testing

### Run Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=ctags_mcp tests/
```

### Test with MCP Inspector
```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Start the server
python -m ctags_mcp.server

# In another terminal, run inspector
mcp-inspector --url http://localhost:3000
```

## Docker Support

### Build Image
```bash
# Recommended: Use the simpler Dockerfile for quick testing
docker build -f Dockerfile.simple -t ctags-mcp-server .

# Alternative: Build from source (compiles Universal CTags from source)
docker build -t ctags-mcp-server .
```

### Run Container
```bash
docker run -v $(pwd):/workspace ctags-mcp-server
```

### Docker Compose
```yaml
version: '3.8'
services:
  ctags-mcp:
    image: ctags-mcp-server
    volumes:
      - ./:/workspace
    environment:
      - CTAGS_BINARY=/usr/local/bin/ctags
```

## Testing MCP Server with Docker and MCP Inspector

### Step-by-Step Container Testing

1. **Build the Docker image:**
```bash
docker build -f Dockerfile.simple -t ctags-mcp-server .
```

2. **Run the container with port mapping:**
```bash
docker run -it --rm \
  -p 3000:3000 \
  -v $(pwd):/workspace \
  --name ctags-mcp \
  ctags-mcp-server
```

3. **In another terminal, run MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector test \
  --url http://localhost:3000
```

### Complete Testing Examples for All Tools

Below are ready-to-use examples with actual values that you can copy and paste into MCP Inspector to test each tool:

#### 1. **generate_tags** - Generate CTags Index
```json
{
  "tool": "generate_tags",
  "arguments": {
    "path": "/workspace/tests/fixtures/sample_code",
    "recursive": true,
    "languages": ["python", "javascript"],
    "exclude_patterns": ["*.min.js", "__pycache__"],
    "output_file": "/workspace/test.tags",
    "extra_options": ["--sort=yes"]
  }
}
```

**Expected Result:** Creates a tags file at `/workspace/test.tags` with indexed symbols from sample code.

#### 2. **update_tags** - Update Tags Incrementally
```json
{
  "tool": "update_tags",
  "arguments": {
    "tags_file": "/workspace/test.tags",
    "modified_files": [
      "/workspace/tests/fixtures/sample_code/example.py",
      "/workspace/tests/fixtures/sample_code/example.js"
    ]
  }
}
```

**Expected Result:** Updates the existing tags file with changes from specified files.

#### 3. **find_symbol** - Search for Symbols
```json
{
  "tool": "find_symbol",
  "arguments": {
    "symbol_name": "DatabaseConnection",
    "tags_file": "/workspace/test.tags",
    "match_type": "exact",
    "case_sensitive": true,
    "symbol_kinds": ["class"],
    "limit": 10
  }
}
```

**Alternative Examples:**
```json
// Partial match example
{
  "tool": "find_symbol",
  "arguments": {
    "symbol_name": "get",
    "tags_file": "/workspace/test.tags",
    "match_type": "partial",
    "case_sensitive": false,
    "limit": 20
  }
}

// Regex match example
{
  "tool": "find_symbol",
  "arguments": {
    "symbol_name": "^test_.*",
    "tags_file": "/workspace/test.tags",
    "match_type": "regex",
    "case_sensitive": true,
    "limit": 15
  }
}
```

#### 4. **find_references** - Find All References
```json
{
  "tool": "find_references",
  "arguments": {
    "symbol_name": "UserModel",
    "scope_file": "/workspace/tests/fixtures/sample_code/example.py",
    "tags_file": "/workspace/test.tags"
  }
}
```

#### 5. **go_to_definition** - Navigate to Definition
```json
{
  "tool": "go_to_definition",
  "arguments": {
    "symbol_name": "main",
    "current_file": "/workspace/tests/fixtures/sample_code/example.py",
    "tags_file": "/workspace/test.tags"
  }
}
```

#### 6. **list_symbols_in_file** - List File Symbols
```json
{
  "tool": "list_symbols_in_file",
  "arguments": {
    "file_path": "/workspace/tests/fixtures/sample_code/example.py",
    "tags_file": "/workspace/test.tags",
    "group_by_kind": true
  }
}
```

#### 7. **get_file_outline** - Generate File Outline
```json
{
  "tool": "get_file_outline",
  "arguments": {
    "file_path": "/workspace/tests/fixtures/sample_code/example.py",
    "tags_file": "/workspace/test.tags",
    "include_private": false,
    "max_depth": 3
  }
}
```

#### 8. **list_tags_files** - Find All Tags Files
```json
{
  "tool": "list_tags_files",
  "arguments": {
    "search_path": "/workspace",
    "include_stats": true
  }
}
```

#### 9. **get_tags_info** - Get Tags File Information
```json
{
  "tool": "get_tags_info",
  "arguments": {
    "tags_file": "/workspace/test.tags"
  }
}
```

#### 10. **validate_tags_file** - Validate Tags File
```json
{
  "tool": "validate_tags_file",
  "arguments": {
    "tags_file": "/workspace/test.tags",
    "check_files_exist": true
  }
}
```

### Quick Test Script

Create a file `test_all_tools.sh` to test all tools sequentially:

```bash
#!/bin/bash
# test_all_tools.sh - Test all MCP tools in container

# Start container in background
docker run -d --rm \
  -p 3000:3000 \
  -v $(pwd):/workspace \
  --name ctags-mcp-test \
  ctags-mcp-server

# Wait for server to start
sleep 3

# Generate initial tags
echo "Testing generate_tags..."
curl -X POST http://localhost:3000/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "generate_tags",
    "arguments": {
      "path": "/workspace/tests/fixtures/sample_code",
      "output_file": "/workspace/test.tags"
    }
  }'

# Test other tools...
echo "Testing find_symbol..."
curl -X POST http://localhost:3000/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "find_symbol",
    "arguments": {
      "symbol_name": "DatabaseConnection",
      "tags_file": "/workspace/test.tags"
    }
  }'

# Stop container
docker stop ctags-mcp-test
```

### Docker Compose Testing Setup

For a complete testing environment with MCP Inspector:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  ctags-mcp:
    build:
      context: .
      dockerfile: Dockerfile.simple
    image: ctags-mcp-server:test
    container_name: ctags-mcp-test
    ports:
      - "3000:3000"
    volumes:
      - ./:/workspace
    environment:
      - CTAGS_BINARY=/usr/bin/ctags
      - PYTHONUNBUFFERED=1
    command: python -m ctags_mcp.server
    
  test-runner:
    image: node:18-slim
    container_name: mcp-inspector
    depends_on:
      - ctags-mcp
    volumes:
      - ./test-scripts:/scripts
    command: |
      sh -c "
        npm install -g @modelcontextprotocol/inspector &&
        sleep 5 &&
        mcp-inspector test --url http://ctags-mcp:3000
      "
    networks:
      - default
```

Run with:
```bash
docker-compose -f docker-compose.test.yml up
```

### Troubleshooting Container Testing

1. **Container can't find sample files:**
   - Ensure volume mount is correct: `-v $(pwd):/workspace`
   - Check file paths start with `/workspace/`

2. **MCP Inspector can't connect:**
   - Verify port mapping: `-p 3000:3000`
   - Check container is running: `docker ps`
   - View logs: `docker logs ctags-mcp`

3. **CTags not found in container:**
   - Use Dockerfile.simple which installs universal-ctags
   - Or set `CTAGS_BINARY=/usr/bin/ctags` environment variable

4. **Permission issues:**
   - Run container with user ID: `--user $(id -u):$(id -g)`
   - Or adjust file permissions in mounted volume

## Development

### Project Structure
```
universal-ctags-mcp-server/
├── src/
│   └── ctags_mcp/
│       ├── server.py          # Main server implementation
│       ├── models/            # Pydantic models
│       └── utils/             # CTags wrapper and validators
├── tests/                     # Test suite
├── pyproject.toml            # Project configuration
└── README.md                 # Documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Important Implementation Notes

### CTags Library Integration
- The server uses `python-ctags3` library for reading tag files
- The library expects **bytes** for filenames and symbol names in Python 3
- All string/bytes conversions are handled automatically by the wrapper

### Tags File Detection
The `list_tags_files` tool searches for files matching these patterns:
- Exact names: `tags`, `TAGS`, `.tags`
- Files ending with `.tags` or `.tag`
- Files starting with `tags` or `.tags`

### Path Handling
- All file paths are normalized for comparison
- Both absolute and relative paths are supported
- Docker containers should use `/workspace` as the base path

## Troubleshooting

### Common Issues

#### CTags not found
```bash
# Check if ctags is installed
which ctags

# Set custom path
export CTAGS_BINARY=/path/to/ctags
```

#### Tags file not generating
- Check file permissions
- Verify path exists
- Check exclude patterns aren't too broad

#### Symbol not found
- Regenerate tags file
- Check if file is indexed
- Verify symbol name and case sensitivity

## Language Support

Universal CTags supports 100+ languages including:
- Python, JavaScript, TypeScript
- C, C++, C#, Java
- Go, Rust, Swift
- Ruby, PHP, Perl
- HTML, CSS, SCSS
- Markdown, YAML, JSON
- And many more...

## Performance Tips

1. **Use exclude patterns** to skip unnecessary files:
```python
exclude_patterns=["*.min.js", "node_modules", "__pycache__", ".git"]
```

2. **Index specific languages** for faster generation:
```python
languages=["python", "javascript"]
```

3. **Use incremental updates** for large projects:
```python
await update_tags(tags_file="tags", modified_files=changed_files)
```

4. **Limit search results** when possible:
```python
await find_symbol(symbol_name="test", limit=10)
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Universal CTags](https://ctags.io/) - The powerful indexing tool
- [python-ctags3](https://github.com/jonashaag/python-ctags3) - Python bindings for CTags
- [Model Context Protocol](https://modelcontextprotocol.io/) - The MCP specification

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/universal-ctags-mcp-server/issues)
- Discussions: [Ask questions or share ideas](https://github.com/yourusername/universal-ctags-mcp-server/discussions)