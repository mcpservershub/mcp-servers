# MultilsPy MCP Server

A Model Context Protocol (MCP) server that wraps [MultilsPy](https://github.com/microsoft/multilspy) to provide Language Server Protocol (LSP) capabilities through MCP tools. This enables AI assistants to interact with code using the same intelligence features available in modern IDEs.

## Features

### Supported LSP Operations
- **Navigation**: Jump to definitions and find references
- **Code Completion**: Context-aware code suggestions
- **Hover Information**: Type signatures and documentation
- **Document Symbols**: List all symbols in a file
- **Workspace Search**: Find symbols across the entire workspace
- **Session Management**: Save and restore LSP sessions

### Supported Languages
Currently supports all languages provided by MultilsPy plus COBOL via SuperBOL:

**MultilsPy Languages:**
- Python
- Java
- Rust
- C# (CSharp)
- TypeScript / JavaScript
- Go
- Ruby
- Dart
- Kotlin
- C/C++

**COBOL Support:**
- COBOL (.cbl, .cob, .cobol)
- COBOL Copybooks (.cpy)
- Pro*COBOL (.pco)
- Powered by [SuperBOL](https://github.com/OCamlPro/superbol-studio-oss) Language Server

## Installation

### Using pip and pyproject.toml

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multilspy-mcp-server.git
cd multilspy-mcp-server
```

2. Create a Python 3.12 virtual environment:
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

For development with all dependencies:
```bash
pip install -e ".[dev,test]"
```

### Using Docker

The Docker image includes basic COBOL support via GnuCOBOL. For full COBOL language server features, SuperBOL must be installed separately.

Build and run using Docker:
```bash
# Build the image
docker build -t multilspy-mcp-server .

# Run with workspace mounted
docker run -v $(pwd)/workspace:/workspace multilspy-mcp-server python -m multilspy_mcp.server

# For COBOL development, mount your COBOL files
docker run -v /path/to/cobol/code:/workspace/cobol multilspy-mcp-server python -m multilspy_mcp.server
```

## Usage

### Starting the Server

#### Local Installation
```bash
# Set workspace root (optional, defaults to current directory)
export WORKSPACE_ROOT=/path/to/your/project

# Run the MCP server
python -m mcp run multilspy_mcp.server:mcp
```

#### Using Docker
```bash
# Edit docker-compose.yml to mount your project directory
# Then start the service
docker-compose up
```

### MCP Tools Available

The server provides the following MCP tools:

#### Code Navigation
- `code_navigate_definition`: Jump to symbol definition
- `code_find_references`: Find all references to a symbol

#### Code Intelligence
- `code_complete`: Get code completion suggestions
- `code_get_hover`: Get hover information (type signatures, docs)
- `code_document_symbols`: List all symbols in a document
- `code_search_workspace`: Search symbols across workspace

#### Session Management
- `lsp_initialize`: Initialize LSP manager for a workspace
- `lsp_detect_language`: Detect programming language of a file
- `lsp_save_session`: Save current session state
- `lsp_load_session`: Load a previous session

### Example Usage with MCP Client

```python
# Example of using the MCP tools from a client

# Initialize workspace
response = await mcp_client.call_tool(
    "lsp_initialize",
    workspace_root="/path/to/project",
    cache_dir="~/.mcp-lsp/cache"
)

# Navigate to definition
response = await mcp_client.call_tool(
    "code_navigate_definition",
    file_path="src/main.py",
    line=42,
    column=15,
    language="python"
)

# Get completions
response = await mcp_client.call_tool(
    "code_complete",
    file_path="src/utils.py",
    line=10,
    column=20,
    language="python"
)

# Search workspace
response = await mcp_client.call_tool(
    "code_search_workspace",
    query="MyClass",
    language="python",
    limit=50
)
```

## COBOL Support

### Overview

This MCP server provides comprehensive COBOL language support through integration with SuperBOL, a modern COBOL Language Server Protocol implementation. All standard MCP tools work seamlessly with COBOL files.

### Supported COBOL Features

**File Extensions Supported:**
- `.cbl` - COBOL source files
- `.cob` - COBOL source files
- `.cobol` - COBOL source files
- `.cpy` - COBOL copybook files
- `.pco` - Pro*COBOL files

**LSP Features Available:**
- Document symbols (programs, paragraphs, data items)
- Hover information (data types, program structure)
- Go to definition (navigate to paragraph/data definitions)
- Find references (locate paragraph calls, data usage)
- Code completion (COBOL keywords, data names)
- Workspace symbol search

### SuperBOL Installation

For full COBOL language server functionality, install SuperBOL:

**Option 1: VS Code Extension (Recommended)**
```bash
# SuperBOL is primarily distributed as a VS Code extension
# The language server binary is included with the extension
```

**Option 2: Build from Source**
```bash
# Clone SuperBOL repository
git clone https://github.com/OCamlPro/superbol-studio-oss.git
cd superbol-studio-oss

# Follow build instructions in the repository
# Ensure superbol binary is in PATH
```

**Option 3: Docker with External SuperBOL**
```bash
# Mount SuperBOL binary into the container
docker run -v /path/to/superbol:/usr/local/bin/superbol \
           -v /path/to/cobol/code:/workspace/cobol \
           multilspy-mcp-server python -m multilspy_mcp.server
```

### COBOL Usage Examples

```python
# Initialize for COBOL workspace
await mcp_client.call_tool(
    "lsp_initialize",
    workspace_root="/path/to/cobol/project"
)

# Get symbols from COBOL program
await mcp_client.call_tool(
    "code_document_symbols",
    file_path="src/CUSTOMER-MGMT.COB"
)

# Navigate to paragraph definition
await mcp_client.call_tool(
    "code_navigate_definition",
    file_path="src/CUSTOMER-MGMT.COB",
    line=85,
    column=18  # On PERFORM CUSTOMER-LOOKUP
)

# Find all references to a data item
await mcp_client.call_tool(
    "code_find_references",
    file_path="src/CUSTOMER-MGMT.COB",
    line=27,
    column=12  # On CUSTOMER-RECORD
)

# Get hover info for COBOL data structure
await mcp_client.call_tool(
    "code_get_hover",
    file_path="copybooks/CUSTOMER-RECORD.CPY",
    line=5,
    column=10  # On data field definition
)
```

### COBOL Testing

The repository includes comprehensive COBOL test files:

```
test-cobol/
├── CUSTOMER.COB          # Customer management program
├── INVENTORY.COB         # Inventory management system
├── UTILITIES.COB         # Common utility subroutines
├── copybooks/
│   ├── CUSTOMER-RECORD.CPY  # Customer data layout
│   └── ERROR-CODES.CPY      # Error handling definitions
└── README-COBOL-TEST.md     # Testing documentation
```

**Run COBOL Tests:**
```bash
# Test with Docker container
docker run -v $(pwd)/test-cobol:/workspace/cobol \
           multilspy-mcp-server \
           python -c "
from multilspy_mcp.lsp_manager import LSPManager
lsp = LSPManager('/workspace')
print('COBOL files detected:')
import glob
for f in glob.glob('/workspace/cobol/*.COB'):
    lang = lsp.detect_language(f)
    print(f'  {f}: {lang}')
"
```

### COBOL Troubleshooting

**SuperBOL Not Found:**
- Ensure SuperBOL binary is installed and in PATH
- Check SuperBOL installation with: `superbol --version`
- The system gracefully handles SuperBOL unavailability

**File Detection Issues:**
- Verify COBOL files use supported extensions (.cbl, .cob, .cobol, .cpy, .pco)
- Check file permissions and accessibility
- Ensure workspace root is correctly set

**Performance Considerations:**
- COBOL files with many copybook includes may take longer to process
- Consider caching for large COBOL codebases
- SuperBOL supports various COBOL dialects (GnuCOBOL, IBM, Micro Focus)

## Configuration

### Environment Variables

- `WORKSPACE_ROOT`: Root directory of the workspace (default: current directory)
- `MCP_LSP_CACHE_DIR`: Directory for caching LSP data (default: `~/.mcp-lsp/cache`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Docker Configuration

Edit `docker-compose.yml` to customize:
- Workspace mount points
- Resource limits
- Port mappings
- Environment variables

## Architecture

The server is built with extensibility in mind:

```
┌─────────────────┐
│   MCP Client    │
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│   MCP Server    │ (FastMCP)
│  (server.py)    │
└────────┬────────┘
         │
┌────────▼────────┐
│  LSP Manager    │ (Wrapper)
│(lsp_manager.py) │
└────────┬────────┘
         │
┌────────▼────────┐
│   MultilsPy     │ (LSP Client)
└────────┬────────┘
         │ LSP Protocol
┌────────▼────────┐
│  LSP Servers    │
│(pylsp, gopls...)│
└─────────────────┘
```

### Key Components

1. **src/multilspy_mcp/models.py**: Pydantic models for type validation
2. **src/multilspy_mcp/lsp_manager.py**: Wrapper around MultilsPy with caching and state management
3. **src/multilspy_mcp/server.py**: MCP server implementation using FastMCP

## Development

### Running Tests
```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=html tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Adding New Features

To add new LSP features not currently supported:

1. Add the request/response models in `src/multilspy_mcp/models.py`
2. Implement the LSP wrapper method in `src/multilspy_mcp/lsp_manager.py`
3. Create the MCP tool in `src/multilspy_mcp/server.py`
4. Add tests in `tests/`

## Future Enhancements

The current implementation wraps MultilsPy's limited feature set. Future enhancements planned:

### Additional LSP Features
- [ ] Diagnostics (textDocument/publishDiagnostics)
- [ ] Code Actions (textDocument/codeAction)
- [ ] Refactoring (textDocument/rename)
- [ ] Formatting (textDocument/formatting)
- [ ] Semantic Tokens (textDocument/semanticTokens)
- [ ] Call Hierarchy (textDocument/callHierarchy)

### Infrastructure Improvements
- [ ] Connection pooling for multiple language servers
- [ ] Request batching and caching
- [ ] Better session persistence and restoration
- [ ] Multi-workspace support
- [ ] Remote LSP server connections

### Language Support
- [x] COBOL support via SuperBOL integration
- [ ] Add support for more niche languages
- [ ] Custom language server configurations
- [ ] Language-specific optimizations
- [ ] Better COBOL dialect detection and handling

## Troubleshooting

### Common Issues

1. **Language server not starting**: Ensure the required language runtime is installed
2. **Completions not working**: Some language servers need the file to be saved first
3. **Memory issues**: Adjust Docker resource limits in docker-compose.yml

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m mcp run multilspy_mcp.server:mcp
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [MultilsPy](https://github.com/microsoft/multilspy) by Microsoft Research
- [MCP](https://github.com/modelcontextprotocol) for the Model Context Protocol
- All the LSP server implementations that make this possible

## Support

For issues, questions, or suggestions, please open an issue on GitHub.