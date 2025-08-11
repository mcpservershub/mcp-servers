# Testing Puppeteer MCP Server with MCP Inspector

## Prerequisites

Install MCP Inspector globally:
```bash
npm install -g @modelcontextprotocol/inspector
```

## Method 1: Testing as JavaScript Application

### Step 1: Build the Server
```bash
cd puppeteer-mcp-server
npm install
npm run build
```

### Step 2: Start with MCP Inspector
```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

### Step 3: Access Inspector UI
Open your browser and navigate to: `http://localhost:5173`

### Step 4: Test the Tools

In the MCP Inspector interface, you can test each tool by sending requests. Here are example test sequences:

#### Test Sequence 1: Basic Navigation and Screenshot
```json
// 1. Navigate to a website
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "https://example.com",
      "waitUntil": "networkidle2"
    }
  }
}

// 2. Take a screenshot
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_screenshot",
    "arguments": {
      "fullPage": true,
      "format": "png"
    }
  }
}
```

#### Test Sequence 2: Form Interaction
```json
// 1. Navigate to a form page
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "https://www.google.com"
    }
  }
}

// 2. Type in search box
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_type",
    "arguments": {
      "selector": "textarea[name='q']",
      "text": "MCP Protocol"
    }
  }
}

// 3. Take screenshot of result
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_screenshot",
    "arguments": {
      "fullPage": false
    }
  }
}
```

#### Test Sequence 3: Content Extraction
```json
// 1. Navigate to a page
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "https://example.com"
    }
  }
}

// 2. Get page content
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_get_content",
    "arguments": {
      "type": "text"
    }
  }
}

// 3. Extract all links
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_extract_links",
    "arguments": {
      "includeText": true
    }
  }
}
```

## Method 2: Testing with Docker Container

### Step 1: Build Docker Image
```bash
# Build the standard Docker image
docker build -t puppeteer-mcp-server .

# OR build with Chainguard base
docker build -f Dockerfile.cgr -t puppeteer-mcp-server:cgr .
```

### Step 2: Run Container with MCP Inspector

#### Option A: Using Docker Network (Recommended)
```bash
# Create a network for MCP communication
docker network create mcp-network

# Run the Puppeteer MCP server
docker run -d \
  --name puppeteer-mcp \
  --network mcp-network \
  puppeteer-mcp-server

# Run MCP Inspector connected to the container
docker run -it --rm \
  --network mcp-network \
  -p 5173:5173 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  node:20-alpine sh -c "
    npm install -g @modelcontextprotocol/inspector && 
    npx @modelcontextprotocol/inspector docker exec -i puppeteer-mcp node dist/index.js
  "
```

#### Option B: Using Host Networking
```bash
# Run container with host network
docker run -it --rm \
  --network host \
  puppeteer-mcp-server
```

Then in another terminal:
```bash
npx @modelcontextprotocol/inspector localhost:3000
```

#### Option C: Direct Execution with Docker
```bash
# Run with inspector directly
docker run -it --rm \
  -p 5173:5173 \
  puppeteer-mcp-server \
  sh -c "npm install -g @modelcontextprotocol/inspector && npx @modelcontextprotocol/inspector node dist/index.js"
```

### Step 3: Test via Inspector UI
Navigate to `http://localhost:5173` and use the same test sequences as above.

## Method 3: Using Docker Compose for Testing

Create a `docker-compose.test.yml` file:

```yaml
version: '3.8'
services:
  puppeteer-mcp:
    build: 
      context: .
      dockerfile: Dockerfile
    environment:
      - PUPPETEER_HEADLESS=true
      - NODE_ENV=production
    ports:
      - "3000:3000"
    command: node dist/index.js
    
  inspector:
    image: node:20-alpine
    depends_on:
      - puppeteer-mcp
    ports:
      - "5173:5173"
    volumes:
      - ./:/app
    working_dir: /app
    command: sh -c "npm install -g @modelcontextprotocol/inspector && npx @modelcontextprotocol/inspector puppeteer-mcp:3000"
```

Run with:
```bash
docker-compose -f docker-compose.test.yml up
```

## Testing Checklist

### Core Functionality Tests
- [ ] Navigate to URL
- [ ] Take screenshot (full page)
- [ ] Take screenshot (specific element)
- [ ] Click on elements
- [ ] Type text into inputs
- [ ] Wait for elements to appear
- [ ] Execute JavaScript
- [ ] Get page content (text/HTML)
- [ ] Scroll page
- [ ] Set viewport size
- [ ] Generate PDF
- [ ] Fill form fields
- [ ] Extract links
- [ ] Close page

### Error Handling Tests
- [ ] Invalid URL navigation
- [ ] Non-existent selector click
- [ ] Timeout on wait for selector
- [ ] Invalid JavaScript execution
- [ ] Empty form fields validation

### Performance Tests
- [ ] Multiple sequential operations
- [ ] Large page screenshot
- [ ] Complex JavaScript evaluation
- [ ] Multiple page operations

## Debugging Tips

### 1. Check Server Logs
```bash
# For JavaScript app
node dist/index.js 2>&1 | tee server.log

# For Docker
docker logs puppeteer-mcp
```

### 2. Enable Debug Mode
```bash
# Set environment variable
export DEBUG=puppeteer:*
export PUPPETEER_HEADLESS=false  # See browser window

# Run server
node dist/index.js
```

### 3. Test Individual Tools
Use the Inspector to test one tool at a time and verify the response.

### 4. Verify Browser Launch
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "about:blank"
    }
  }
}
```

## Common Issues and Solutions

### Issue: Browser fails to launch in Docker
**Solution**: Ensure Chromium dependencies are installed:
```bash
docker exec puppeteer-mcp chromium --version
```

### Issue: Timeout errors
**Solution**: Increase timeout values:
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_wait_for_selector",
    "arguments": {
      "selector": "#element",
      "timeout": 60000
    }
  }
}
```

### Issue: Screenshot returns empty
**Solution**: Ensure page is loaded:
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "https://example.com",
      "waitUntil": "networkidle0"
    }
  }
}
```

## Automated Testing Script

Create `test-mcp.js`:

```javascript
const { spawn } = require('child_process');
const http = require('http');

// Start the MCP server
const server = spawn('node', ['dist/index.js']);

// Wait for server to start
setTimeout(() => {
  // Test sequence
  const tests = [
    {
      name: 'Navigate',
      tool: 'puppeteer_navigate',
      args: { url: 'https://example.com' }
    },
    {
      name: 'Screenshot',
      tool: 'puppeteer_screenshot',
      args: { fullPage: true }
    },
    {
      name: 'Get Content',
      tool: 'puppeteer_get_content',
      args: { type: 'text' }
    }
  ];

  // Run tests
  tests.forEach(test => {
    console.log(`Running test: ${test.name}`);
    // Send request to MCP server
    // Process response
  });

  // Cleanup
  server.kill();
}, 3000);
```

Run with:
```bash
node test-mcp.js
```