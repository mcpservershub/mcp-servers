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
Currently supports all languages provided by MultilsPy:
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

Build and run using Docker Compose:
```bash
docker-compose up -d
```

Or build manually:
```bash
docker build -t multilspy-mcp-server:latest .
docker run -v $(pwd)/workspace:/workspace multilspy-mcp-server:latest
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
- [ ] Add support for more languages
- [ ] Custom language server configurations
- [ ] Language-specific optimizations

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