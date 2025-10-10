# Zoekt MCP Server

An MCP (Model Context Protocol) server that provides access to Zoekt code search functionality through structured tools.

## Overview

This server exposes Zoekt's powerful code search capabilities as MCP tools, allowing AI assistants to index and search code repositories efficiently.

## Available Tools

### 1. zoekt-index
Index a local directory for code search.

**Parameters:**
- `directory` (required): Directory path to index
- `index_dir` (optional): Directory to store index files (default: ~/.zoekt)
- `output_file` (required): File to write the indexing output
- `language_map` (optional): Language mapping (format: lang1:processor1,lang2:processor2)
- `incremental` (optional): Enable incremental indexing

### 2. zoekt-git-index
Index a git repository for code search.

**Parameters:**
- `repository` (required): Git repository path or URL
- `index_dir` (optional): Directory to store index files (default: ~/.zoekt)
- `output_file` (required): File to write the indexing output
- `branches` (optional): Git branches to index (default: HEAD)
- `branch_prefix` (optional): Prefix for branch names (default: refs/heads/)
- `submodules` (optional): Recurse into submodules
- `incremental` (optional): Enable incremental indexing

### 3. zoekt-search
Search indexed repositories using Zoekt query syntax with advanced options.

**Parameters:**
- `query` (required): Search query (supports repo:, file:, lang:, content: filters)
- `index_dir` (optional): Directory containing index files (default: ~/.zoekt)
- `output_file` (required): File to write the search results
- `shard` (optional): Search in a specific shard file
- `max_results` (optional): Maximum number of results to return
- `list_files` (optional): List matching files only (-l flag)
- `show_repo` (optional): Show repository name before file name (-r flag)
- `symbol_search` (optional): Enable experimental symbol search (-sym flag)
- `debug_score` (optional): Show debug score output (-debug flag)
- `verbose` (optional): Print verbose background data (-v flag)

## Query Syntax

Zoekt supports powerful query syntax including:

- **Field filters**: `repo:myrepo`, `file:*.go`, `lang:python`, `content:function`
- **Logical operators**: `AND`, `OR`, parentheses for grouping
- **Negation**: `-repo:unwanted`
- **Regular expressions**: Full regex support
- **Boolean fields**: `public:yes`, `archived:no`

## Examples

### Index a repository
```json
{
  "directory": "/path/to/repo",
  "output_file": "/tmp/index_output.txt",
  "incremental": true
}
```

### Search for functions in Go files
```json
{
  "query": "lang:go content:func",
  "output_file": "/tmp/search_results.txt",
  "max_results": 50,
  "show_repo": true
}
```

### Search for symbols in code
```json
{
  "query": "handleRequest",
  "output_file": "/tmp/symbol_search.txt",
  "symbol_search": true,
  "verbose": true
}
```

### Search specific repository with file listing
```json
{
  "query": "repo:myproject file:*.py import",
  "output_file": "/tmp/python_imports.txt",
  "list_files": true
}
```

## Installation

### Option 1: Native Build
1. Ensure Zoekt tools are installed and available in PATH
2. Build the MCP server:
   ```bash
   go build -o zoekt-mcp-server main.go
   ```

### Option 2: Docker Build
1. Build the standard Docker image:
   ```bash
   ./build-docker.sh
   ```

2. Build the Docker image with Universal Ctags support (recommended):
   ```bash
   ./build-docker-ctags.sh
   ```
   
   **Why use the ctags version?**
   - Enhanced symbol information for better search results
   - Improved function and class detection across languages
   - Better code navigation and indexing quality
   - As recommended in the [Zoekt documentation](https://github.com/sourcegraph/zoekt#ctags)

## Usage

### Native Usage
The server communicates via stdio as per MCP protocol:
```bash
./zoekt-mcp-server
```

### Docker Usage
Run the containerized MCP server:
```bash
# Basic usage
docker run -it --rm zoekt-mcp-server:latest

# With persistent data volumes
docker run -it --rm \
  -v $(pwd)/data:/app/.zoekt \
  -v $(pwd)/repos:/app/repos \
  zoekt-mcp-server:latest
```

### Docker Image Details
The Docker image uses a multi-stage build:
- **Build stage**: Chainguard Wolfi base image with Go toolchain
- **Runtime stage**: Chainguard static image for minimal attack surface
- **Includes**: All Zoekt CLI tools in `/usr/local/bin/`
- **Size**: Optimized for minimal footprint

All tool executions write detailed output to the specified output file, with a JSON summary returned to the client.
---
*Last updated: 2025-07-29 16:13:12 UTC*
