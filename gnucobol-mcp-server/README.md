# GnuCOBOL MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with the GnuCOBOL compiler, enabling COBOL developers to compile, validate, and analyze COBOL code through a standardized interface.

## Overview

The GnuCOBOL MCP Server exposes GnuCOBOL compiler functionality through the Model Context Protocol, allowing AI assistants, IDEs, and other tools to interact with COBOL codebases efficiently. This server enables modern development workflows for legacy COBOL systems.

## Quick Start

Get started with the GnuCOBOL MCP Server in Docker:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/gnucobol-mcp-server.git
cd gnucobol-mcp-server

# 2. Build the Docker image
docker build -f Dockerfile.cgr -t gnucobol-mcp:cgr .

# 3. Test with MCP Inspector
npx @modelcontextprotocol/inspector docker run -i -v $(pwd):/workspace gnucobol-mcp:cgr

# 4. Navigate to http://localhost:5173 and try:
# Tool: compile_cobol
# Arguments:
{
  "file_path": "/workspace/tests/sample_cobol/valid/calculator.cob",
  "output_name": "calculator"
}
```

### Key Features

- **COBOL Compilation**: Compile COBOL source files to native executables
- **Syntax Validation**: Fast syntax-only checking without code generation
- **Code Analysis**: Generate detailed listings with symbol tables and cross-references
- **Batch Processing**: Compile multiple COBOL files in a single operation
- **STDIN Support**: Process COBOL code directly from input streams
- **Error Reporting**: Structured, IDE-friendly error diagnostics
- **MCP Protocol**: Standardized interface for tool integration

## Requirements

### System Requirements

- **Python**: 3.12 or higher
- **GnuCOBOL**: 3.x or higher
- **uv**: Package manager for Python projects

### GnuCOBOL Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install gnucobol
```

**macOS (Homebrew):**
```bash
brew install gnucobol
```

**Verify Installation:**
```bash
cobc --version
```

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/gnucobol-mcp-server.git
cd gnucobol-mcp-server

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
uv pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
uv pip install -e ".[dev]"
```

## MCP Tools

The GnuCOBOL MCP Server provides the following file-based tools:

**Supported COBOL File Extensions:**
The server recognizes and processes files with the following extensions:
- `.cob`, `.cbl`, `.COB`, `.CBL` - Standard COBOL files
- `.c74`, `.C74` - COBOL 74 files
- `.c85`, `.C85` - COBOL 85 files
- `.cpy`, `.CPY` - Copybook files (sometimes used as source)
- `.pco`, `.PCO` - Pro*COBOL files
- `.sqb`, `.SQB` - SQL embedded COBOL files

### 1. compile_cobol

Compiles a COBOL source file from the filesystem to a native executable.

**Arguments:**
- `file_path` (string, required): Path to the COBOL source file (absolute or relative)
- `output_name` (string, optional): Name for the output executable (default: derived from filename)
- `options` (array, optional): Additional compiler options (e.g., `["-Wall", "-O2"]`)

**Example:**
```json
{
  "name": "compile_cobol",
  "arguments": {
    "file_path": "/workspace/programs/hello.cob",
    "output_name": "hello",
    "options": ["-Wall"]
  }
}
```

**Returns:**
```json
{
  "success": true,
  "file_path": "/workspace/programs/hello.cob",
  "output_name": "hello",
  "stdout": "",
  "stderr": "",
  "return_code": 0,
  "command": "cobc -x -o /tmp/.../hello /tmp/.../source.cob",
  "message": "Successfully compiled to executable: hello"
}
```

### 2. syntax_check

Performs syntax-only validation of a COBOL source file without generating executable code.

**Arguments:**
- `file_path` (string, required): Path to the COBOL source file (absolute or relative)
- `options` (array, optional): Additional compiler options (e.g., `["-Wall", "-std=cobol2014"]`)

**Example:**
```json
{
  "name": "syntax_check",
  "arguments": {
    "file_path": "/workspace/programs/calculator.cob"
  }
}
```

**Returns:**
```json
{
  "valid": true,
  "file_path": "/workspace/programs/calculator.cob",
  "stdout": "",
  "stderr": "",
  "return_code": 0,
  "command": "cobc -fsyntax-only /tmp/.../source.cob",
  "warnings": [],
  "errors": [],
  "warning_count": 0,
  "error_count": 0,
  "message": "Syntax is valid"
}
```

### 3. analyze_cobol

Generates detailed code analysis including symbol table and cross-reference listing from a COBOL source file.

**Arguments:**
- `file_path` (string, required): Path to the COBOL source file (absolute or relative)
- `include_symbols` (boolean, optional): Include symbol table in listing (default: true)
- `include_xref` (boolean, optional): Include cross-reference in listing (default: true)
- `copybook_paths` (array, optional): List of directories to search for COPY files (adds `-I` flags)
- `options` (array, optional): Additional compiler options

**Example:**
```json
{
  "name": "analyze_cobol",
  "arguments": {
    "file_path": "/workspace/programs/calculator.cob",
    "include_symbols": true,
    "include_xref": true,
    "copybook_paths": ["/workspace/copybooks"]
  }
}
```

**Returns:**
```json
{
  "success": true,
  "file_path": "/workspace/programs/calculator.cob",
  "listing": "GnuCOBOL 3.2.0  ... [full listing with symbols and cross-references]",
  "stdout": "",
  "stderr": "",
  "return_code": 0,
  "command": "cobc -X -ftsymbols -t /tmp/.../listing.lst -fsyntax-only /tmp/.../source.cob",
  "analysis": {
    "lines_in_listing": 85,
    "has_symbols": true,
    "has_xref": true
  },
  "message": "Analysis completed successfully"
}
```

### 4. batch_compile

Compiles multiple COBOL source files in a single batch operation.

**Arguments:**
- `file_paths` (array, required): Array of paths to COBOL source files
- `options` (array, optional): Compiler options to apply to all programs
- `stop_on_error` (boolean, optional): Stop batch if any compilation fails (default: false)

**Example:**
```json
{
  "name": "batch_compile",
  "arguments": {
    "file_paths": [
      "/workspace/programs/main.cob",
      "/workspace/programs/utils.cob",
      "/workspace/programs/reports.cob"
    ],
    "options": ["-Wall"],
    "stop_on_error": false
  }
}
```

**Returns:**
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "success_rate": "100.0%",
  "results": [
    {
      "index": 0,
      "file_path": "/workspace/programs/main.cob",
      "output_name": "main",
      "success": true,
      "return_code": 0,
      "message": "Successfully compiled main"
    },
    {
      "index": 1,
      "file_path": "/workspace/programs/utils.cob",
      "output_name": "utils",
      "success": true,
      "return_code": 0,
      "message": "Successfully compiled utils"
    },
    {
      "index": 2,
      "file_path": "/workspace/programs/reports.cob",
      "output_name": "reports",
      "success": true,
      "return_code": 0,
      "message": "Successfully compiled reports"
    }
  ],
  "message": "Batch compilation complete: 3 successful, 0 failed"
}
```

### 5. compile_project

Compiles an entire COBOL project from a directory into a single output file (executable or shared library). This tool discovers all COBOL files in a directory and compiles them together using GnuCOBOL's project compilation features, which is more efficient than compiling files individually and properly handles inter-file dependencies.

**Arguments:**
- `directory` (string, required): Directory path containing COBOL source files
- `output_name` (string, required): Name for the output file (executable or module)
- `output_type` (string, optional): Type of output - "executable" or "module" (default: "executable")
- `copybook_paths` (array, optional): List of directories to search for COPY files (adds `-I` flags)
- `library_paths` (array, optional): List of directories to search for libraries (adds `-L` flags)
- `recursive` (boolean, optional): Search subdirectories recursively for COBOL files (default: true)
- `options` (array, optional): Additional compiler options (e.g., `["-Wall", "-O2"]`)

**Example - Compile project to executable:**
```json
{
  "name": "compile_project",
  "arguments": {
    "directory": "/workspace/cobol-app",
    "output_name": "myapp",
    "output_type": "executable",
    "copybook_paths": ["/workspace/cobol-app/copybooks"],
    "recursive": true,
    "options": ["-Wall", "-O2"]
  }
}
```

**Example - Compile project to shared library:**
```json
{
  "name": "compile_project",
  "arguments": {
    "directory": "/workspace/cobol-lib",
    "output_name": "libcobol.so",
    "output_type": "module",
    "copybook_paths": ["/workspace/cobol-lib/copy"],
    "library_paths": ["/usr/local/lib"]
  }
}
```

**Returns:**
```json
{
  "success": true,
  "directory": "/workspace/cobol-app",
  "output_name": "myapp",
  "output_type": "executable",
  "files_compiled": 15,
  "file_list": [
    "/workspace/cobol-app/main.cob",
    "/workspace/cobol-app/src/customer.cob",
    "/workspace/cobol-app/src/invoice.cob",
    "..."
  ],
  "stdout": "",
  "stderr": "",
  "return_code": 0,
  "command": "cobc -x -o /tmp/.../myapp -I /workspace/cobol-app/copybooks /workspace/cobol-app/main.cob ...",
  "message": "Successfully compiled 15 files into executable: myapp"
}
```

**Key Features:**
- **Automatic File Discovery**: Finds all COBOL files with common extensions (.cob, .cbl, .c74, .c85, .cpy, .pco, .sqb and uppercase variants) in directory tree
- **Single Compilation**: Compiles all files together (more efficient than batch_compile)
- **Dependency Handling**: GnuCOBOL automatically resolves CALL dependencies between files
- **Copybook Support**: Specify directories for COPY statement resolution with `-I` flags
- **Library Linking**: Link external libraries with `-L` and `-l` flags
- **Flexible Output**: Create executables (`-x`) or shared libraries (`-b`)

**Use Cases:**
1. **Multi-file Projects**: Compile entire COBOL application with multiple source files
2. **Library Creation**: Build shared libraries from multiple COBOL modules
3. **Build Automation**: Integrate into CI/CD pipelines for automated builds
4. **Dependency Management**: Let GnuCOBOL handle inter-file CALL statements

### 6. get_compiler_info

Returns information about the GnuCOBOL compiler installation.

**Arguments:** None

**Example:**
```json
{
  "name": "get_compiler_info"
}
```

**Returns:**
```json
{
  "version": "GnuCOBOL 3.2.0",
  "build_date": "Oct 01 2024",
  "configuration": {
    "default_source_format": "fixed",
    "max_source_line_length": 255
  }
}
```

### 7. health_check

Checks the health status of the MCP server and GnuCOBOL installation.

**Arguments:** None

**Example:**
```json
{
  "name": "health_check"
}
```

**Returns:**
```json
{
  "status": "healthy",
  "server": "online",
  "compiler_available": true,
  "message": "MCP server is running"
}
```

### 8. batch_analyze

Analyzes multiple COBOL source files and extracts project-level semantic relationships, including inter-file dependencies, CALL statements, and COPY/INCLUDE references. This tool provides comprehensive insights into how COBOL programs interact within a project.

You can provide either specific file paths OR a directory containing COBOL files. When using directory mode, the tool automatically discovers all COBOL files with common extensions (.cob, .cbl, .c74, .c85, .cpy, .pco, .sqb and uppercase variants) recursively and filters out non-COBOL files like README, Makefiles, etc.

**Arguments:**
- `file_paths` (array, optional): Array of paths to COBOL source files (required if `directory` not provided)
- `directory` (string, optional): Directory path to scan for COBOL files (required if `file_paths` not provided)
- `recursive` (boolean, optional): When using `directory`, search subdirectories recursively (default: true)
- `copybook_paths` (array, optional): List of directories to search for COPY files (adds `-I` flags)
- `include_symbols` (boolean, optional): Include symbol table analysis (default: true)
- `include_xref` (boolean, optional): Include cross-reference analysis (default: true)

**Example with file_paths:**
```json
{
  "name": "batch_analyze",
  "arguments": {
    "file_paths": [
      "/workspace/programs/MAIN.cob",
      "/workspace/programs/CUSTOMER.cob",
      "/workspace/programs/INVENTORY.cob"
    ],
    "include_symbols": true,
    "include_xref": true
  }
}
```

**Example with directory (recommended for projects):**
```json
{
  "name": "batch_analyze",
  "arguments": {
    "directory": "/workspace/cobol-project",
    "recursive": true
  }
}
```

This will automatically discover all COBOL files in the directory tree:
- `/workspace/cobol-project/MAIN.cob`
- `/workspace/cobol-project/src/CUSTOMER.cob`
- `/workspace/cobol-project/src/utils/LOGGER.cob`
- `/workspace/cobol-project/lib/FILEIO.CBL`

**Example with non-recursive directory scan:**
```json
{
  "name": "batch_analyze",
  "arguments": {
    "directory": "/workspace/programs",
    "recursive": false
  }
}
```

This only analyzes COBOL files in the immediate directory, skipping subdirectories.

**Returns:**
```json
{
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "programs": ["MAIN", "CUSTOMER", "INVENTORY"],
  "program_calls": {
    "MAIN": ["CUSTOMER", "INVENTORY"],
    "CUSTOMER": [],
    "INVENTORY": []
  },
  "copybook_usage": {
    "MAIN": ["SQLCA", "CUSTCOPY"],
    "CUSTOMER": ["SQLCA", "CUSTCOPY"],
    "INVENTORY": ["SQLCA", "INVCOPY"]
  },
  "call_summary": {
    "total_calls": 2,
    "unique_programs": ["CUSTOMER", "INVENTORY"],
    "call_graph": [
      {"caller": "MAIN", "callee": "CUSTOMER", "type": "external_call"},
      {"caller": "MAIN", "callee": "INVENTORY", "type": "external_call"}
    ]
  },
  "copybook_summary": {
    "total_includes": 5,
    "unique_copybooks": ["SQLCA", "CUSTCOPY", "INVCOPY"],
    "dependencies": [
      {"program": "MAIN", "copybook": "SQLCA", "type": "include"},
      {"program": "MAIN", "copybook": "CUSTCOPY", "type": "include"},
      {"program": "CUSTOMER", "copybook": "SQLCA", "type": "include"},
      {"program": "CUSTOMER", "copybook": "CUSTCOPY", "type": "include"},
      {"program": "INVENTORY", "copybook": "SQLCA", "type": "include"},
      {"program": "INVENTORY", "copybook": "INVCOPY", "type": "include"}
    ]
  },
  "per_file_analysis": [
    {
      "file_path": "/workspace/programs/MAIN.cob",
      "program_id": "MAIN",
      "success": true,
      "listing": "... detailed listing ...",
      "calls": [
        {"program": "CUSTOMER", "type": "external_call"},
        {"program": "INVENTORY", "type": "external_call"}
      ],
      "copybooks": [
        {"copybook": "SQLCA", "type": "include"},
        {"copybook": "CUSTCOPY", "type": "include"}
      ]
    }
  ],
  "message": "Batch analysis complete: 3 successful, 0 failed"
}
```

**Use Cases:**

1. **Dependency Mapping**: Understand which programs call other programs in your COBOL project
2. **Impact Analysis**: Identify which programs are affected when modifying a copybook or called program
3. **Architecture Visualization**: Generate call graphs and dependency diagrams for legacy systems
4. **Code Migration**: Map inter-file dependencies before modernization or refactoring
5. **Documentation**: Auto-generate project structure documentation with semantic relationships

**Key Features:**

- **Inter-File Relationships**: Discovers CALL statements to identify program-to-program dependencies
- **Copybook Tracking**: Identifies all COPY/INCLUDE statements to map shared data structures
- **Call Graph Generation**: Provides structured call graph data for visualization
- **Semantic Aggregation**: Combines per-file analysis into project-level insights
- **Hybrid Approach**: Leverages GnuCOBOL's native analysis with minimal Python aggregation

## Usage

### Running the MCP Server (STDIO Mode)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
gnucobol-mcp
```

The server communicates via STDIO and follows the MCP protocol specification.

### Testing with MCP Inspector

The MCP Inspector is an official tool for testing MCP servers.

**Installation:**
```bash
npx @modelcontextprotocol/inspector
```

**Usage:**
```bash
# Start the inspector
npx @modelcontextprotocol/inspector uv --directory /path/to/gnucobol-mcp-server run gnucobol-mcp
```

This will:
1. Launch the MCP Inspector web interface
2. Start the GnuCOBOL MCP Server
3. Allow interactive testing of all tools

**Testing Tools:**

1. Navigate to http://localhost:6789 in your browser
2. Select a tool from the available tools list
3. Enter the required arguments in JSON format
4. Click "Execute" to test the tool
5. View the response and any errors

### Example Test Cases

Before running these examples, ensure you have COBOL files in your workspace. You can use the sample files in `tests/sample_cobol/valid/` directory.

**Test 1: Compile a COBOL Program**

Tool: `compile_cobol`

```json
{
  "file_path": "/workspace/tests/sample_cobol/valid/hello.cob",
  "output_name": "hello"
}
```

Expected result: Successfully compiles the program to an executable named "hello".

---

**Test 2: Syntax Check**

Tool: `syntax_check`

```json
{
  "file_path": "/workspace/tests/sample_cobol/valid/calculator.cob"
}
```

Expected result: Returns `valid: true` with no errors or warnings.

---

**Test 3: Code Analysis with Symbols and Cross-Reference**

Tool: `analyze_cobol`

```json
{
  "file_path": "/workspace/tests/sample_cobol/valid/calculator.cob",
  "include_symbols": true,
  "include_xref": true
}
```

Expected result: Returns a detailed listing showing:
- Program source with line numbers
- Symbol table with data types and sizes
- Cross-reference showing where each variable is defined and used

---

**Test 4: Batch Compilation**

Tool: `batch_compile`

```json
{
  "file_paths": [
    "/workspace/tests/sample_cobol/valid/hello.cob",
    "/workspace/tests/sample_cobol/valid/calculator.cob"
  ],
  "options": ["-Wall"],
  "stop_on_error": false
}
```

Expected result: Compiles both programs and returns detailed results for each.

---

**Test 5: Get Compiler Information**

Tool: `get_compiler_info`

```json
{}
```

Expected result: Returns GnuCOBOL version, configuration, and installation path.

## Configuration

### Standalone Application

Add the following configuration to your MCP client (e.g., Claude Desktop):

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "gnucobol": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gnucobol-mcp-server",
        "run",
        "gnucobol-mcp"
      ],
      "env": {
        "PATH": "/usr/bin:/usr/local/bin"
      }
    }
  }
}
```

### Docker Container

The GnuCOBOL MCP Server is designed to run in a Docker container for isolated and consistent environments.

#### Building the Docker Image

Use the optimized Chainguard-based Dockerfile:

```bash
# Build the Docker image
docker build -f Dockerfile.cgr -t gnucobol-mcp:cgr .
```

**What's included:**
- GnuCOBOL 3.2.0 compiler
- Required dependencies (GMP, NCurses, Berkeley DB)
- Python 3.12 with FastMCP
- Minimal Chainguard Wolfi base for security

#### Running with MCP Inspector

Test your MCP server with MCP Inspector and volume mounting:

```bash
# Run with volume mount to access host files
npx @modelcontextprotocol/inspector docker run -i -v $(pwd):/workspace gnucobol-mcp:cgr
```

This will:
1. Launch the MCP Inspector web interface at http://localhost:5173
2. Mount your current directory to `/workspace` in the container
3. Allow you to test tools with files from your host system

**Example test in MCP Inspector:**
```json
{
  "file_path": "/workspace/tests/sample_cobol/valid/calculator.cob",
  "output_name": "calculator"
}
```

#### Running in Production

**Run the container with STDIN/STDOUT:**
```bash
docker run -i --rm -v /path/to/cobol/files:/workspace gnucobol-mcp:cgr
```

**With specific file access:**
```bash
docker run -i --rm \
  -v /path/to/cobol/files:/workspace:ro \
  gnucobol-mcp:cgr
```

#### MCP Client Configuration for Docker

**Claude Desktop (macOS):**

Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gnucobol": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/your/cobol/projects:/workspace",
        "gnucobol-mcp:cgr"
      ]
    }
  }
}
```

**Claude Desktop (Windows):**

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gnucobol": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "C:\\path\\to\\cobol\\projects:/workspace",
        "gnucobol-mcp:cgr"
      ]
    }
  }
}
```

**Claude Desktop (Linux):**

Location: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gnucobol": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/home/user/cobol-projects:/workspace",
        "gnucobol-mcp:cgr"
      ]
    }
  }
}
```

#### Docker Image Details

**Base Image:** `cgr.dev/chainguard/wolfi-base`
- Minimal attack surface
- Regularly updated security patches
- Non-root user for security

**Installed Packages:**
- `gnucobol` - GnuCOBOL 3.2.0 compiler
- `gcc` - C compiler for COBOL compilation
- `gmp-dev`, `libgmp` - GNU Multiple Precision Arithmetic Library
- `ncurses-dev` - NCurses library for COBOL SCREEN/ACCEPT/DISPLAY
- `db-dev` - Berkeley DB for indexed file support
- `python-3.12` - Python runtime
- `py3.12-pip`, `uv` - Python package managers

**Security Features:**
- Runs as non-root user (`mcpuser`)
- Read-only root filesystem compatible
- Minimal dependency footprint
- Health check included

### Environment Variables

- `COBOL_CONFIG_DIR`: Custom GnuCOBOL configuration directory
- `COB_CFLAGS`: Additional C compiler flags
- `COB_LDFLAGS`: Additional linker flags

## Development

### Project Structure

```
gnucobol-mcp-server/
├── gnucobol_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── docs/
│   ├── API.md
│   ├── EXAMPLES.md
│   └── TROUBLESHOOTING.md
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
└── .gitignore
```

### Running Tests

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=gnucobol_mcp tests/
```

### Code Quality

```bash
# Format code
black gnucobol_mcp/ tests/

# Lint code
ruff check gnucobol_mcp/ tests/

# Type checking (optional)
mypy gnucobol_mcp/
```

## Troubleshooting

### Common Issues

**1. GnuCOBOL not found**
```
Error: cobc: command not found
```
**Solution:** Install GnuCOBOL and ensure it's in your PATH:
```bash
which cobc
export PATH=$PATH:/usr/local/bin
```

**2. Permission denied errors**
```
Error: Permission denied: './program'
```
**Solution:** Ensure the output directory has write permissions:
```bash
chmod +w /path/to/output
```

**3. Import errors**
```
ModuleNotFoundError: No module named 'mcp'
```
**Solution:** Reinstall dependencies:
```bash
uv pip install -e .
```

**4. STDIO communication issues**
```
Error: JSON-RPC parse error
```
**Solution:** Ensure proper STDIO mode configuration and check logs for JSON formatting issues.

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export MCP_DEBUG=1
gnucobol-mcp
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black .`
6. Commit changes: `git commit -m "Add your feature"`
7. Push to branch: `git push origin feature/your-feature`
8. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/gnucobol-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/gnucobol-mcp-server/discussions)

## Acknowledgments

- [GnuCOBOL Project](https://gnucobol.sourceforge.io/) - The free COBOL compiler
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [Anthropic](https://www.anthropic.com/) - MCP creators

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**Built with MCP by the GnuCOBOL MCP Team**
