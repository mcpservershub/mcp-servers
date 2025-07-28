# markdownlint MCP Server

An MCP (Model Context Protocol) server that provides tools for linting and fixing Markdown files using markdownlint-cli.

## Features

- **Lint Markdown files** - Check multiple files, directories, or globs for Markdown style issues
- **Automatic fixing** - Automatically fix basic Markdown errors (always enabled)
- **Lint content** - Lint Markdown content provided as a string
- **Configurable rules** - Support for custom configuration files and rule sets
- **Flexible output** - Option to write results to a file
- **Version checking** - Check installed markdownlint-cli version
- **Exit code handling** - Proper interpretation of markdownlint exit codes:
  - 0: Program ran successfully
  - 1: Linting errors found (and fixed when `--fix` is enabled)
  - 2: Unable to write output file
  - 3: Unable to load custom rules
  - 4: Unexpected error (e.g., malformed config)

## Prerequisites

- Python 3.12 or higher
- Node.js and npm (for markdownlint-cli)
- markdownlint-cli installed globally:
  ```bash
  npm install -g markdownlint-cli
  ```

## Installation

### Using pip

```bash
pip install markdownlint-mcp-server
```

### From source

```bash
git clone <repository-url>
cd markdownlint-mcp-server
pip install -e .
```

### Using Docker

```bash
# Build the image
docker build -f Dockerfile.cgr -t markdownlint-mcp-server .

# Run with mounted volume
docker run -i -v /path/to/your/files:/app/workdir markdownlint-mcp-server

# Example with MCP Inspector
npx @modelcontextprotocol/inspector docker run -i -v /home/user/markdown-files:/app/workdir markdownlint-mcp-server
```

**Note on permissions**: The container runs as user `mcpuser` (UID 1001). Ensure mounted files have appropriate permissions for reading/writing.

## Usage

### Starting the Server

```bash
markdownlint-mcp
```

### Configuration for MCP Clients

Add the following to your MCP client configuration:

```json
{
  "mcpServers": {
    "markdownlint": {
      "command": "markdownlint-mcp"
    }
  }
}
```

### Available Tools

#### 1. `lint_files`
Lint markdown files with automatic fixing enabled.

**Parameters:**
- `files` (required): List of files, directories, or globs to lint
- `config` (optional): Path to configuration file (JSON, JSONC, JS, YAML, or TOML)
- `ignore` (optional): List of files/directories/globs to ignore
- `rules` (optional): List of custom rule files to include
- `disable` (optional): List of rules to disable (e.g., ["MD013", "MD041"])
- `output_file` (optional): Write lint results to this file

**Example:**
```json
{
  "tool": "lint_files",
  "arguments": {
    "files": ["README.md", "docs/*.md"],
    "config": ".markdownlint.json",
    "disable": ["MD013", "MD033"],
    "output_file": "lint-results.txt"
  }
}
```

#### 2. `lint_content`
Lint markdown content from a string.

**Parameters:**
- `content` (required): Markdown content to lint
- `config` (optional): Path to configuration file
- `rules` (optional): List of custom rule files to include
- `disable` (optional): List of rules to disable
- `output_file` (optional): Write lint results to this file

**Returns:**
- Linting results including the fixed content

**Example:**
```json
{
  "tool": "lint_content",
  "arguments": {
    "content": "# Header\\n\\nSome content with  issues",
    "disable": ["MD009"]
  }
}
```

#### 3. `check_version`
Check the installed version of markdownlint-cli.

**Example:**
```json
{
  "tool": "check_version",
  "arguments": {}
}
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO

### markdownlint Configuration

You can use any markdownlint configuration file format:
- `.markdownlint.json`
- `.markdownlint.yaml`
- `.markdownlint.yml`
- `.markdownlintrc`

Example `.markdownlint.json`:
```json
{
  "default": true,
  "MD013": false,
  "MD033": {
    "allowed_elements": ["br", "img"]
  }
}
```

## Development

### Setting up the development environment

```bash
# Create a virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

### Running tests

```bash
# Install markdownlint-cli first
npm install -g markdownlint-cli

# Run the server in development mode
LOG_LEVEL=DEBUG markdownlint-mcp
```

## License

MIT License