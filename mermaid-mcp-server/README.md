# Mermaid MCP Server

A Model Context Protocol (MCP) server that converts Mermaid diagrams to PNG images.

## Overview

This MCP server provides the ability to generate PNG images from Mermaid diagram definitions through the Model Context Protocol, enabling AI assistants to create visual diagrams.

## Features

- Convert Mermaid diagram syntax to PNG images
- Support for all Mermaid diagram types
- Automated rendering using Puppeteer
- MCP-compatible interface

## Installation

```bash
npm install @peng-shawn/mermaid-mcp-server
```

## Usage

Run the server:

```bash
mermaid-mcp-server
```

Or with npm:

```bash
npm start
```

## Docker Support

Build and run with Docker:

```bash
docker build -t mermaid-mcp-server .
docker run mermaid-mcp-server
```

## Requirements

- Node.js >= 18.0.0
- Puppeteer dependencies for headless Chrome

## Configuration

Configure the server using the `config.json` file provided.

## License

MIT License - see LICENSE file for details.

## Author

Shawn Peng

---
*Last updated: 2025-07-29 16:13:12 UTC