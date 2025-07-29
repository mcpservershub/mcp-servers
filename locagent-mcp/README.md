# LocAgent MCP Server

Model Context Protocol (MCP) Server for LocAgent code localization tools.

## Overview

This MCP server exposes LocAgent's code localization capabilities through the Model Context Protocol, allowing LLM clients to search and analyze codebases.

## Features

- **Repository Setup**: Initialize local or GitHub repositories for analysis
- **Code Search**: Search for code snippets using keywords, function names, or line numbers
- **Dependency Analysis**: Explore code dependencies and relationships in tree or graph format
- **Multiple Retrieval Methods**: BM25, fuzzy matching, and semantic search capabilities

## Tools

1. `setup_repository` - Initialize repository for analysis
2. `reset_repository` - Reset repository context
3. `search_code_snippets` - Search codebase for relevant code snippets
4. `explore_tree_structure` - Analyze code dependencies in tree format
5. `explore_graph_structure` - Analyze code dependencies in graph format

## Usage

```bash
# Install dependencies
pip install -e .

# Run the server
locagent-mcp-server --log-level INFO

# Run with custom log file
locagent-mcp-server --log-file /tmp/mcp-server.log
```

## Docker

```bash
# Build optimized image
docker build -f Dockerfile.optimized -t locagent-mcp-server .

# Run container
docker run -p 8080:8080 locagent-mcp-server
```

## License

Apache-2.0

---
*Last updated: 2025-07-29 16:13:12 UTC*
