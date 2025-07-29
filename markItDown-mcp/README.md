# MarkItDown MCP Server

An MCP (Model Context Protocol) server for the MarkItDown library, enabling document conversion capabilities.

## Overview

This MCP server provides access to the MarkItDown library functionality, allowing you to convert various document formats to Markdown through the Model Context Protocol.

## Features

- Convert multiple document formats to Markdown
- Supports all MarkItDown library features
- Easy integration with MCP-compatible applications

## Installation

```bash
pip install markitdown-mcp
```

## Usage

Run the server using:

```bash
markitdown-mcp
```

## Docker Support

This server includes a Dockerfile for containerized deployment:

```bash
docker build -t markitdown-mcp .
docker run markitdown-mcp
```

## Requirements

- Python >= 3.10
- MCP ~= 1.8.0
- MarkItDown >= 0.1.1, < 0.2.0

## License

See LICENSE file in the project root.

---
*Last updated: 2025-07-29 16:13:12 UTC