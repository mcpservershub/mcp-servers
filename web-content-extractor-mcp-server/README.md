# Web Content Extractor MCP Server

A Model Context Protocol (MCP) server that provides web content extraction capabilities using the `@wrtnlabs/web-content-extractor` library.

## Features

- **Single Tool**: `get_content` - Extract HTML content from URLs
- **Content Extraction**: Uses text density analysis to extract meaningful content
- **File Output**: Saves extracted content to specified file paths
- **Comprehensive Data**: Returns title, description, main content, HTML fragments, and links

## Installation

```bash
npm install
npm run build
```

## Usage

### As MCP Server

The server runs on stdio transport and can be integrated with MCP-compatible clients like Claude Desktop.

```bash
npm start
```

### Tool: get_content

Extracts content from a URL and saves it to a file.

**Parameters:**
- `url` (string, required): The URL to extract content from
- `output_file_path` (string, required): File path where extracted content will be saved

**Returns:**
- Extracted content summary
- Full data saved to the specified file path

**Example Usage:**
```json
{
  "tool": "get_content",
  "arguments": {
    "url": "https://example.com/article",
    "output_file_path": "./extracted_content.json"
  }
}
```

## Output Format

The tool saves a JSON file with the following structure:

```json
{
  "url": "https://example.com/article",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "extracted": {
    "title": "Article Title",
    "description": "Article description",
    "content": "Main content text...",
    "contentHtmls": ["<p>HTML fragments...</p>"],
    "links": ["https://link1.com", "https://link2.com"]
  },
  "rawHtml": "<!DOCTYPE html>..."
}
```

## Development

```bash
# Development mode
npm run dev

# Build
npm run build

# Production
npm start
```

## Integration with Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "web-content-extractor": {
      "command": "node",
      "args": ["/path/to/web-content-extractor-mcp-server/dist/index.js"]
    }
  }
}
```

## Dependencies

- `@modelcontextprotocol/sdk` - MCP TypeScript SDK
- `@wrtnlabs/web-content-extractor` - Web content extraction library
- `node-fetch` - HTTP client for fetching web content
- `zod` - Schema validation
---
*Last updated: 2025-07-29 16:13:12 UTC*
