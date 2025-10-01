# PostgreSQL MCP Server

MCP server for interacting with PostgreSQL databases through the Model Context Protocol.

## Overview

This MCP server enables AI assistants to interact with PostgreSQL databases, providing safe and controlled database access through the Model Context Protocol.

## Features

- Connect to PostgreSQL databases
- Execute SQL queries
- Database schema exploration
- Transaction support
- Secure credential handling

## Installation

```bash
npm install @modelcontextprotocol/server-postgres
```

## Usage

Run the server:

```bash
mcp-server-postgres
```

## Docker Support

Build and run with Docker:

```bash
docker build -t postgres-mcp .
docker run postgres-mcp
```

## Configuration

Set your PostgreSQL connection parameters through environment variables or configuration file.

## Requirements

- Node.js
- PostgreSQL client libraries

## Author

Anthropic, PBC (https://anthropic.com)

## License

MIT License

---
*Last updated: 2025-07-29 16:13:12 UTC