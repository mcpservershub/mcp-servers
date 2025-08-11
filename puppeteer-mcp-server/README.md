# Puppeteer MCP Server

A Model Context Protocol (MCP) server that provides browser automation capabilities through Puppeteer. This server enables LLMs to interact with web pages, take screenshots, fill forms, and execute JavaScript in a real browser environment.

## Features

- 🌐 **Web Navigation**: Navigate to URLs with configurable wait strategies
- 📸 **Screenshots**: Capture full page or element-specific screenshots
- 🖱️ **Interactions**: Click elements, type text, fill forms
- 📊 **Content Extraction**: Get page content, extract links, evaluate JavaScript
- 📄 **PDF Generation**: Convert web pages to PDF documents
- 🎯 **Element Selection**: Wait for elements, query selectors
- 📱 **Viewport Control**: Set custom viewport sizes and device emulation
- ✅ **Input Validation**: Robust validation using Zod schemas
- 🔒 **Error Handling**: Comprehensive error handling with detailed messages

## Available Tools

### 1. `puppeteer_navigate`
Navigate to a URL with customizable wait conditions.
- **Parameters:**
  - `url` (string, required): The URL to navigate to
  - `waitUntil` (string, optional): When to consider navigation complete
    - Options: `load`, `domcontentloaded`, `networkidle0`, `networkidle2`
    - Default: `networkidle2`

### 2. `puppeteer_screenshot`
Capture screenshots of the page or specific elements.
- **Parameters:**
  - `selector` (string, optional): CSS selector for element screenshot
  - `fullPage` (boolean, optional): Capture full scrollable page
  - `format` (string, optional): Image format (`png`, `jpeg`, `webp`)
  - `quality` (number, optional): Quality for jpeg/webp (0-100)

### 3. `puppeteer_click`
Click on page elements.
- **Parameters:**
  - `selector` (string, required): CSS selector of element to click
  - `clickCount` (number, optional): Number of clicks
  - `delay` (number, optional): Delay between clicks in ms

### 4. `puppeteer_type`
Type text into input fields.
- **Parameters:**
  - `selector` (string, required): CSS selector of input element
  - `text` (string, required): Text to type
  - `delay` (number, optional): Delay between keystrokes in ms
  - `clear` (boolean, optional): Clear field before typing

### 5. `puppeteer_wait_for_selector`
Wait for elements to appear or disappear.
- **Parameters:**
  - `selector` (string, required): CSS selector to wait for
  - `timeout` (number, optional): Maximum wait time in ms (default: 30000)
  - `visible` (boolean, optional): Wait for element to be visible
  - `hidden` (boolean, optional): Wait for element to be hidden

### 6. `puppeteer_evaluate`
Execute JavaScript in the browser context.
- **Parameters:**
  - `script` (string, required): JavaScript code to execute
  - `args` (array, optional): Arguments to pass to the script

### 7. `puppeteer_get_content`
Extract text or HTML content from the page.
- **Parameters:**
  - `selector` (string, optional): CSS selector for specific element
  - `type` (string, optional): Content type (`text`, `html`, `value`)

### 8. `puppeteer_scroll`
Scroll the page to specific coordinates.
- **Parameters:**
  - `x` (number, optional): Horizontal scroll position
  - `y` (number, optional): Vertical scroll position
  - `smooth` (boolean, optional): Use smooth scrolling

### 9. `puppeteer_set_viewport`
Set viewport size and device characteristics.
- **Parameters:**
  - `width` (number, required): Viewport width in pixels
  - `height` (number, required): Viewport height in pixels
  - `deviceScaleFactor` (number, optional): Device scale factor
  - `isMobile` (boolean, optional): Mobile viewport behavior
  - `hasTouch` (boolean, optional): Enable touch events

### 10. `puppeteer_pdf`
Generate PDF from the current page.
- **Parameters:**
  - `path` (string, optional): File path to save PDF
  - `format` (string, optional): Paper format (A4, Letter, etc.)
  - `landscape` (boolean, optional): Landscape orientation
  - `printBackground` (boolean, optional): Include background graphics
  - `scale` (number, optional): Scale of page rendering (0.1-2)

### 11. `puppeteer_fill_form`
Fill multiple form fields at once.
- **Parameters:**
  - `fields` (object, required): Object mapping CSS selectors to values

### 12. `puppeteer_extract_links`
Extract all links from the page.
- **Parameters:**
  - `selector` (string, optional): CSS selector for links (default: `a`)
  - `includeText` (boolean, optional): Include link text

### 13. `puppeteer_close_page`
Close the current browser page.

## Installation

### Using NPM

```bash
npm install
npm run build
npm start
```

### Using Docker

Build the Docker image:
```bash
docker build -t puppeteer-mcp-server .
```

Run the container:
```bash
docker run -it puppeteer-mcp-server
```

## Testing

### Run Tests Locally

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Testing with MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a tool for testing and debugging MCP servers.

1. Install MCP Inspector:
```bash
npm install -g @modelcontextprotocol/inspector
```

2. Run the server with Inspector:
```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

3. Open your browser to the URL shown (typically http://localhost:5173)

4. Test the tools interactively:
   - Use the Inspector UI to call tools
   - View request/response payloads
   - Debug tool implementations

Example test flow in Inspector:
```javascript
// 1. Navigate to a website
{
  "tool": "puppeteer_navigate",
  "arguments": {
    "url": "https://example.com"
  }
}

// 2. Take a screenshot
{
  "tool": "puppeteer_screenshot",
  "arguments": {
    "fullPage": true,
    "format": "png"
  }
}

// 3. Extract all links
{
  "tool": "puppeteer_extract_links",
  "arguments": {
    "includeText": true
  }
}
```

## Configuration

### Environment Variables

- `PUPPETEER_HEADLESS`: Set to `false` to run browser in headful mode (default: `true`)
- `PUPPETEER_EXECUTABLE_PATH`: Path to Chrome/Chromium executable
- `NODE_ENV`: Set to `production` for production deployments

### MCP Configuration

#### Standalone Application

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "node",
      "args": ["/path/to/puppeteer-mcp-server/dist/index.js"],
      "env": {
        "PUPPETEER_HEADLESS": "true"
      }
    }
  }
}
```

#### Using NPX

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@mcp/puppeteer-server"],
      "env": {
        "PUPPETEER_HEADLESS": "true"
      }
    }
  }
}
```

#### Using Docker

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "puppeteer-mcp-server"
      ]
    }
  }
}
```

#### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "node",
      "args": ["/absolute/path/to/dist/index.js"]
    }
  }
}
```

## Docker Usage

### Building the Image

```bash
# Build with default settings
docker build -t puppeteer-mcp-server .

# Build with custom tag
docker build -t myregistry/puppeteer-mcp:latest .
```

### Running the Container

```bash
# Run interactively
docker run -it puppeteer-mcp-server

# Run with environment variables
docker run -it \
  -e PUPPETEER_HEADLESS=true \
  puppeteer-mcp-server

# Run with volume mount for persistent data
docker run -it \
  -v $(pwd)/data:/app/data \
  puppeteer-mcp-server
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  puppeteer-mcp:
    build: .
    environment:
      - PUPPETEER_HEADLESS=true
      - NODE_ENV=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## Development

### Project Structure

```
puppeteer-mcp-server/
├── src/
│   ├── index.ts          # Main server entry point
│   ├── browser-manager.ts # Browser lifecycle management
│   ├── tools.ts          # Tool implementations
│   ├── schemas.ts        # Zod validation schemas
│   └── index.test.ts     # Test suite
├── dist/                 # Compiled JavaScript
├── package.json
├── tsconfig.json
├── Dockerfile
└── README.md
```

### Adding New Tools

1. Define the schema in `src/schemas.ts`
2. Implement the tool in `src/tools.ts`
3. Register the tool in `src/index.ts`
4. Add tests in `src/index.test.ts`
5. Update this README

## Security Considerations

- The server runs Puppeteer in a sandboxed environment
- Input validation is enforced on all tool parameters
- The Docker image runs as a non-root user
- Chromium runs with additional security flags
- No arbitrary code execution is allowed outside the `evaluate` tool

## Troubleshooting

### Common Issues

1. **Browser fails to launch**
   - Ensure Chrome/Chromium is installed
   - Check `PUPPETEER_EXECUTABLE_PATH` environment variable
   - For Docker, ensure the image has all required dependencies

2. **Timeout errors**
   - Increase timeout values in tool parameters
   - Check network connectivity
   - Verify the target website is accessible

3. **Memory issues**
   - Close unused pages with `puppeteer_close_page`
   - Restart the server periodically for long-running sessions
   - Monitor Docker container memory limits

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
- All tests pass (`npm test`)
- Code passes linting (`npm run lint`)
- TypeScript compiles without errors (`npm run build`)
- New features include tests
- Documentation is updated