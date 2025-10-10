# Repomix MCP Server Documentation

## Overview

Repomix can operate as a Model Context Protocol (MCP) server, providing AI assistants with powerful tools to analyze codebases directly without manual file preparation. The MCP server mode enables seamless integration with AI development environments like Claude Desktop, VS Code, Cursor, and Cline.

## Quick Start

### Running as MCP Server

```bash
# Using npm/npx
npx repomix --mcp

# Using Docker (single-stage build)
docker run --rm ghcr.io/yamadashy/repomix --mcp

# Using Docker (multi-stage build for smaller image)
docker run --rm ghcr.io/yamadashy/repomix:multistage --mcp
```

### Docker Images

Two Docker images are available using Chainguard's secure `wolfi-base`:

1. **Single-stage** (`Dockerfile.cgr`): ~320MB
2. **Multi-stage** (`Dockerfile.cgr-multistage`): ~300MB (recommended for production)

Both images use:
- `ENTRYPOINT ["repomix"]`
- `CMD ["--mcp"]`

This allows flexible usage:
```bash
# Run as MCP server (default)
docker run --rm image-name

# Override for other commands
docker run --rm image-name --version
docker run --rm image-name --help
```

## Integration with AI Assistants

### VS Code / VS Code Insiders

Install using the badge or command line:

```bash
# VS Code
code --add-mcp '{"name":"repomix","command":"npx","args":["-y","repomix","--mcp"]}'

# VS Code Insiders
code-insiders --add-mcp '{"name":"repomix","command":"npx","args":["-y","repomix","--mcp"]}'
```

### Cline (VS Code Extension)

Add to `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    }
  }
}
```

### Claude Desktop

Configure in Claude Desktop settings with appropriate command for your platform.

### Claude Code

```bash
claude mcp add repomix -- npx -y repomix --mcp
```

### Docker Alternative

For any MCP client, you can use Docker instead of npx:

```json
{
  "mcpServers": {
    "repomix-docker": {
      "command": "docker",
      "args": ["run", "--rm", "ghcr.io/yamadashy/repomix", "--mcp"]
    }
  }
}
```

## Available MCP Tools

### 1. `pack_codebase`

Package a local code directory into a consolidated XML file for AI analysis.

**Parameters:**
- `directory` (required, string): Absolute path to the directory to pack
- `compress` (optional, boolean): Enable Tree-sitter compression to reduce tokens by ~70% (default: false)
- `includePatterns` (optional, string): Comma-separated glob patterns to include (e.g., "**/*.{js,ts}")
- `ignorePatterns` (optional, string): Additional comma-separated glob patterns to exclude
- `topFilesLength` (optional, number): Number of largest files to display in metrics (default: 10)

**Returns:**
- `description`: Human-readable packing results
- `result`: JSON string with detailed metrics
- `directoryStructure`: Tree structure of the directory
- `outputId`: Unique ID for accessing packed content
- `outputFilePath`: Path to generated output file
- `totalFiles`: Number of files processed
- `totalTokens`: Total token count

**Example Usage:**
```javascript
{
  "directory": "/Users/dev/my-project",
  "compress": true,
  "includePatterns": "src/**,lib/**",
  "ignorePatterns": "**/*.test.js",
  "topFilesLength": 5
}
```

### 2. `pack_remote_repository`

Fetch and package a GitHub repository into a consolidated XML file.

**Parameters:**
- `remote` (required, string): GitHub repository URL or `user/repo` format
  - Examples: "yamadashy/repomix", "https://github.com/user/repo", "https://github.com/user/repo/tree/branch"
- `compress` (optional, boolean): Enable compression (default: false)
- `includePatterns` (optional, string): Glob patterns to include
- `ignorePatterns` (optional, string): Glob patterns to exclude
- `topFilesLength` (optional, number): Number of largest files (default: 10)

**Returns:** Same as `pack_codebase`

**Example Usage:**
```javascript
{
  "remote": "microsoft/vscode",
  "compress": true,
  "includePatterns": "src/**/*.ts",
  "ignorePatterns": "**/*.test.ts"
}
```

### 3. `attach_packed_output`

Attach an existing Repomix packed output file for analysis.

**Parameters:**
- `path` (required, string): Path to directory containing `repomix-output.xml` or direct path to XML file
- `topFilesLength` (optional, number): Number of largest files (default: 10)

**Returns:** Same as `pack_codebase`

**Special Behaviors:**
- Accepts both directory paths and direct XML file paths
- Refreshes content if file has been updated
- Returns new output ID for updated content

**Example Usage:**
```javascript
{
  "path": "/Users/dev/my-project/repomix-output.xml",
  "topFilesLength": 20
}
```

### 4. `read_repomix_output`

Read contents of a Repomix-generated output file with support for partial reading.

**Parameters:**
- `outputId` (required, string): ID of the Repomix output file
- `startLine` (optional, number): Starting line number (1-based, inclusive)
- `endLine` (optional, number): Ending line number (1-based, inclusive)

**Returns:**
- `content`: File content or specified line range
- `totalLines`: Total number of lines
- `linesRead`: Number of lines read
- `startLine`: Starting line used (if specified)
- `endLine`: Ending line used (if specified)

**Example Usage:**
```javascript
{
  "outputId": "a1b2c3d4",
  "startLine": 100,
  "endLine": 200
}
```

### 5. `grep_repomix_output`

Search for patterns in a Repomix output file using JavaScript RegExp syntax.

**Parameters:**
- `outputId` (required, string): ID of the Repomix output file
- `pattern` (required, string): JavaScript RegExp pattern
- `contextLines` (optional, number): Context lines before and after matches (default: 0)
- `beforeLines` (optional, number): Lines before each match (overrides contextLines)
- `afterLines` (optional, number): Lines after each match (overrides contextLines)
- `ignoreCase` (optional, boolean): Case-insensitive matching (default: false)

**Returns:**
- `description`: Human-readable search results
- `matches`: Array of matches with lineNumber, line, and matchedText
- `formattedOutput`: Grep-style formatted output
- `totalMatches`: Total matches found
- `pattern`: The search pattern used

**Example Usage:**
```javascript
{
  "outputId": "a1b2c3d4",
  "pattern": "function\\s+\\w+",
  "contextLines": 2,
  "ignoreCase": true
}
```

### 6. `file_system_read_file`

Read a file from the local file system with security validation.

**Parameters:**
- `path` (required, string): Absolute path to the file

**Returns:**
- `path`: File path that was read
- `content`: File content
- `size`: File size in bytes
- `encoding`: Text encoding (always 'utf8')
- `lines`: Number of lines

**Security Features:**
- Uses SecretLint to detect and block sensitive information
- Requires absolute paths
- Blocks access if security check fails

**Example Usage:**
```javascript
{
  "path": "/Users/dev/project/src/index.js"
}
```

### 7. `file_system_read_directory`

List contents of a directory.

**Parameters:**
- `path` (required, string): Absolute path to the directory

**Returns:**
- `path`: Directory path listed
- `contents`: Array with [FILE]/[DIR] indicators
- `totalItems`: Total items in directory
- `fileCount`: Number of files
- `directoryCount`: Number of subdirectories

**Example Usage:**
```javascript
{
  "path": "/Users/dev/project/src"
}
```

## MCP Prompts

### `pack_remote_repository`

Interactive prompt for analyzing GitHub repositories.

**Parameters:**
- `repository` (required, string): GitHub URL or owner/repo format
- `includePatterns` (optional, string): Comma-separated glob patterns to include
- `ignorePatterns` (optional, string): Comma-separated glob patterns to exclude

**Generated Workflow:**
1. Uses `pack_remote_repository` tool with specified parameters
2. Reads the packed code using the outputId
3. Provides high-level project overview
4. Explains architecture and main components
5. Identifies key technologies and dependencies
6. Highlights interesting patterns or design decisions

## Features and Capabilities

### Tree-sitter Compression
- Reduces token usage by ~70%
- Extracts essential code signatures and structure
- Removes implementation details while preserving semantic meaning
- Optional feature (disabled by default)

### Security Scanning
- Integrated SecretLint for all file operations
- Automatically detects and blocks sensitive information
- Applied to both individual files and packed outputs

### Output Format
The packed XML output structure:
```xml
<file_summary>
  <!-- Metadata and AI usage instructions -->
</file_summary>

<directory_structure>
  <!-- Directory tree structure -->
</directory_structure>

<files>
  <file path="src/index.js">
    <!-- File contents -->
  </file>
  <!-- Additional files -->
</files>

<instruction>
  <!-- Custom instructions if provided -->
</instruction>
```

### Resource Management
- **Temporary Storage**: Creates temporary directories under `os.tmpdir()/repomix/mcp-outputs/`
- **Output Registry**: In-memory mapping of output IDs to file paths
- **Unique IDs**: 8-byte hex strings for each packing operation
- **File Access**: Tools access files via registered IDs

### Error Handling
- Comprehensive error conversion with structured JSON format
- Includes stack trace, name, cause, code, and timestamp
- Distinguishes between Error objects and unknown error types

## Architecture Notes

### Communication Protocol
- Uses stdio (standard input/output) for MCP communication
- JSON-RPC based message exchange
- Stateless tool invocations

### Tool Annotations
All tools include MCP annotations:
- `readOnlyHint: true` - Tools don't modify the file system
- `destructiveHint: false` - No destructive operations
- `idempotentHint` - Varies by tool (true for read operations)
- `openWorldHint` - True only for `pack_remote_repository` (network access)

### Environment Compatibility
- **Direct File Access**: Provides file paths for environments with file system access
- **Limited Access**: Provides output IDs for web browsers/sandboxed environments
- **Cross-platform**: Uses Node.js built-in modules for compatibility

## Best Practices

### For AI Assistants
1. Start with `pack_codebase` or `pack_remote_repository` to prepare the codebase
2. Use `compress: true` for large codebases to reduce token usage
3. Use `grep_repomix_output` to search for specific patterns
4. Use `read_repomix_output` with line ranges for examining specific sections

### For Developers
1. Use multi-stage Docker images for production deployments
2. Configure appropriate include/ignore patterns for optimal packing
3. Use the `attach_packed_output` tool for pre-generated outputs
4. Monitor temporary directory usage in long-running deployments

## Troubleshooting

### MCP Server Silent Operation
The MCP server runs silently and waits for stdio communication. This is normal behavior - the server is waiting for MCP protocol messages.

### Docker Networking
When using Docker, ensure proper volume mounting for local directory access:
```bash
docker run --rm -v /path/to/code:/app ghcr.io/yamadashy/repomix --mcp
```

### Security Blocks
If files are blocked by security scanning:
1. Review the file for sensitive information
2. Remove or redact sensitive data
3. Use ignore patterns to exclude sensitive files

## Examples

### Analyzing a Local Project
```javascript
// 1. Pack the codebase
{
  "tool": "pack_codebase",
  "parameters": {
    "directory": "/Users/dev/my-project",
    "compress": true,
    "ignorePatterns": "node_modules/**,dist/**"
  }
}

// 2. Search for specific patterns
{
  "tool": "grep_repomix_output",
  "parameters": {
    "outputId": "returned-id",
    "pattern": "TODO|FIXME",
    "contextLines": 2
  }
}
```

### Analyzing a GitHub Repository
```javascript
// 1. Pack remote repository
{
  "tool": "pack_remote_repository",
  "parameters": {
    "remote": "facebook/react",
    "compress": true,
    "includePatterns": "packages/**/*.js"
  }
}

// 2. Read specific sections
{
  "tool": "read_repomix_output",
  "parameters": {
    "outputId": "returned-id",
    "startLine": 1000,
    "endLine": 2000
  }
}
```

## Version Compatibility

- MCP SDK: `@modelcontextprotocol/sdk` version 1.15.0
- Node.js: Compatible with Node.js 18+
- Docker: Chainguard wolfi-base image with Node.js 24

## Support and Resources

- [Repomix GitHub Repository](https://github.com/yamadashy/repomix)
- [MCP Documentation](https://modelcontextprotocol.io)
- [Issue Tracker](https://github.com/yamadashy/repomix/issues)