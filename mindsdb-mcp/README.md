# MindsDB MCP Server

An MCP (Model Context Protocol) server for MindsDB integration, enabling AI-powered database operations.

## Overview

This MCP server provides integration with MindsDB, allowing you to leverage machine learning capabilities directly within your database operations through the Model Context Protocol.

## Features

- Connect to MindsDB instances
- Execute AI-powered SQL queries
- Machine learning model management
- Predictive analytics capabilities

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the server:

```bash
python server.py
```

## Docker Support

Build and run with Docker:

```bash
docker build -t mindsdb-mcp .
docker run mindsdb-mcp
```

## Configuration

Configure your MindsDB connection settings in `config.py`.

## Requirements

See `requirements.txt` for full dependency list.

## License

See LICENSE file in the project root.

---
*Last updated: 2025-07-29 16:13:12 UTC