# ast-grep MCP Server

An MCP (Model Context Protocol) server that integrates the ast-grep CLI tool for powerful code search and transformation capabilities.

## Overview

This MCP server provides two main tools:
- **search**: Search for code patterns using AST-based pattern matching
- **search_replace**: Search and replace code patterns across your project

ast-grep is a CLI tool for structural code search and manipulation that works across multiple programming languages using abstract syntax tree (AST) patterns.

## Prerequisites

- Python 3.10 or higher
- Docker (for containerized deployment)
- ast-grep CLI tool (automatically installed in Docker image)

## Installation


### Local Installation

1. Install the package:
```bash
pip install -e .
```

2. Install ast-grep CLI:
```bash
pip install ast-grep-cli
```

## MCP Server Configuration

Add the following configuration to your MCP client settings:

```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--volume=/path/to/your/code:/workspace",
        "ast-grep-mcp"
      ]
    }
  }
}
```

For local installation, use:

```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "python",
      "args": ["-m", "ast_grep_mcp.server"]
    }
  }
}
```

## Available Tools

### search

Search for code patterns using AST-based pattern matching.

**Parameters:**
- `project_path` (string): Path to the project directory to search in
- `pattern` (string): AST pattern to search for
- `language` (string): Programming language (e.g., python, javascript, rust, java, go, etc.)

**Example:**
```
Search for all function definitions in Python:
- project_path: "/workspace/my-project"
- pattern: "def $FUNC($$$ARGS): $$$BODY"
- language: "python"
```

### search_replace

Search and replace code patterns across your project.

**Parameters:**
- `project_path` (string): Path to the project directory to modify
- `pattern` (string): AST pattern to search for and replace
- `language` (string): Programming language
- `new_pattern` (string): New pattern to replace the matched pattern with

**Example:**
```
Replace print statements with logging:
- project_path: "/workspace/my-project"
- pattern: "print($ARG)"
- language: "python"
- new_pattern: "logger.info($ARG)"
```

## Pattern Syntax

ast-grep uses a pattern syntax that matches the structure of code rather than text. Some key concepts:

- `$VAR` - Matches any single node and captures it as VAR
- `$$$VAR` - Matches zero or more nodes and captures them as VAR
- Literal code structures are matched exactly

For more pattern examples and documentation, see the [ast-grep documentation](https://ast-grep.github.io/).

## Security Notes

When using Docker, ensure you only mount directories that the MCP server should have access to. The `--volume` flag controls which parts of your filesystem are accessible to the container.

## Troubleshooting

1. **ast-grep command not found**: Ensure ast-grep CLI is installed (`pip install ast-grep-cli`)
2. **Permission denied**: Check that the mounted volume has appropriate read/write permissions
3. **No matches found**: Verify your pattern syntax matches the target language's AST structure

## License

This project is licensed under the same terms as the ast-grep-mcp package.

---
*Last updated: 2025-07-29 16:13:12 UTC*
