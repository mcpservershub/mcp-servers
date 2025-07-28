# OpenGrep MCP Server

An MCP (Model Context Protocol) server that provides tools for validating and scanning code using OpenGrep (Semgrep) rules. This server enables AI assistants to perform static analysis and security scanning on codebases using OpenGrep's powerful pattern matching capabilities.

## Overview

The OpenGrep MCP server exposes two primary tools:
- **opengrep_validate**: Validate OpenGrep rules files or directories
- **opengrep_scan**: Scan code using OpenGrep rules with SARIF output

## Prerequisites

- Docker installed on your system
- OpenGrep CLI (automatically included in the Docker image)
- MCP-compatible client (e.g., Claude Desktop, Cline)

## Available Tools

### 1. `opengrep_validate`
Validates OpenGrep rules files or directories to ensure they are syntactically correct.

**Parameters:**
- `rules_path` (required): Path to the rules file or directory to validate

### 2. `opengrep_scan`
Scans code using OpenGrep rules and generates SARIF (Static Analysis Results Interchange Format) output.

**Parameters:**
- `rules_path` (required): Path to the OpenGrep rules file or directory
- `code_path` (required): Path to the code directory or file to scan
- `sarif_output` (optional): Path for SARIF output file (default: "results.sarif")
- `config` (optional): OpenGrep configuration preset (e.g., 'p/python')

## Configuration

### Docker Configuration

To use the OpenGrep MCP server with Docker, add the following configuration to your MCP client's settings:

```json
{
  "mcpServers": {
    "opengrep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--volume=/path/to/your/code:/workspace",
        "--volume=/path/to/your/rules:/rules",
        "santoshkal/opengrep-mcp",
        "/workspace"
      ]
    }
  }
}
```

**Important Notes:**
- Replace `/path/to/your/code` with the actual path to your code directory on the host
- Replace `/path/to/your/rules` with the path to your OpenGrep rules directory
- The volume mappings allow the container to access your local files
- The last argument (`/workspace`) is the repository path inside the container

### Multiple Volume Mounts

For more complex setups, you can mount multiple directories:

```json
{
  "mcpServers": {
    "opengrep": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--volume=/home/user/projects:/projects:ro",
        "--volume=/home/user/opengrep-rules:/rules:ro",
        "--volume=/tmp/scan-results:/results",
        "santoshkal/opengrep-mcp",
        "/projects"
      ]
    }
  }
}
```

## Usage Examples

### Validating Rules

To validate OpenGrep rules:
```
Tool: opengrep_validate
Arguments:
{
  "rules_path": "/rules/my-security-rules.yaml"
}
```

### Scanning Code

To scan a codebase with OpenGrep rules:
```
Tool: opengrep_scan
Arguments:
{
  "rules_path": "/rules/security-rules.yaml",
  "code_path": "/workspace/src",
  "sarif_output": "/results/scan-results.sarif"
}
```

### Using Configuration Presets

To scan with a specific language configuration:
```
Tool: opengrep_scan
Arguments:
{
  "rules_path": "/rules/python-rules.yaml",
  "code_path": "/workspace/python-app",
  "sarif_output": "/results/python-scan.sarif",
  "config": "p/python"
}
```

## Security Considerations

- Use read-only mounts (`:ro`) for source code and rules directories when possible
- Be careful with volume permissions - the container runs with specific user permissions
- The SARIF output files contain detailed information about potential security issues

## Building the Docker Image

If you want to build the image yourself:

```bash
cd opengrep-mcp
docker build -t opengrep-mcp .
```

## Troubleshooting

### Common Issues

1. **"opengrep CLI not found" error**
   - The Docker image should include OpenGrep automatically
   - If building locally, ensure the Dockerfile correctly downloads OpenGrep

2. **"Rules path does not exist" error**
   - Verify your volume mounts are correct
   - Check that the paths inside the container match your tool arguments

3. **"Output directory is not writable" error**
   - Ensure the output directory has write permissions
   - Check volume mount permissions

### Path Mapping

Remember that paths in tool arguments refer to paths *inside* the container:
- Host: `/home/user/code` → Container: `/workspace` (via volume mount)
- Tool argument should use: `/workspace/file.py`

## License

This MCP server is a wrapper around OpenGrep. Please refer to the OpenGrep/Semgrep license for usage terms.