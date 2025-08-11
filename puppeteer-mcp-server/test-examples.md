# Testing Output File Functionality

## How to Test

1. Start the server with MCP Inspector:
```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

2. Open browser at http://localhost:5173

3. Use these test examples in the Inspector interface:

## Test Examples

### 1. Navigate and Save Info
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_navigate",
    "arguments": {
      "url": "https://example.com",
      "output_file": "outputs/navigation-info.json"
    }
  }
}
```
**Expected**: Creates `outputs/navigation-info.json` with URL, title, and status

### 2. Screenshot to File
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_screenshot",
    "arguments": {
      "fullPage": true,
      "format": "png",
      "output_file": "outputs/screenshot.png"
    }
  }
}
```
**Expected**: Creates `outputs/screenshot.png` with the page screenshot

### 3. Extract Content to File
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_get_content",
    "arguments": {
      "type": "text",
      "output_file": "outputs/page-text.txt"
    }
  }
}
```
**Expected**: Creates `outputs/page-text.txt` with page text content

### 4. Save HTML Content
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_get_content",
    "arguments": {
      "type": "html",
      "output_file": "outputs/page.html"
    }
  }
}
```
**Expected**: Creates `outputs/page.html` with full HTML

### 5. Extract Links to JSON
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_extract_links",
    "arguments": {
      "includeText": true,
      "output_file": "outputs/links.json"
    }
  }
}
```
**Expected**: Creates `outputs/links.json` with array of links

### 6. Evaluate Script and Save Result
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_evaluate",
    "arguments": {
      "script": "return { title: document.title, url: window.location.href, timestamp: new Date().toISOString() }",
      "output_file": "outputs/eval-result.json"
    }
  }
}
```
**Expected**: Creates `outputs/eval-result.json` with script result

### 7. Generate PDF
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_pdf",
    "arguments": {
      "format": "A4",
      "printBackground": true,
      "output_file": "outputs/page.pdf"
    }
  }
}
```
**Expected**: Creates `outputs/page.pdf` with page PDF

### 8. Fill Form and Save Data
First navigate to a page with a form, then:
```json
{
  "method": "tools/call",
  "params": {
    "name": "puppeteer_fill_form",
    "arguments": {
      "fields": {
        "input[name='search']": "test query",
        "input[type='email']": "test@example.com"
      },
      "output_file": "outputs/form-data.json"
    }
  }
}
```
**Expected**: Creates `outputs/form-data.json` with filled form data

## Verify Files Created

After running tests, check the `outputs/` directory:
```bash
ls -la outputs/
```

Each file should contain the appropriate content:
- JSON files: Properly formatted JSON data
- PNG files: Valid image data
- PDF files: Valid PDF document
- TXT/HTML files: Text or HTML content

## Response Format

When `output_file` is used, the response includes a `saved_to` field:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{
        \"screenshot\": \"data:image/png;base64,...\",
        \"timestamp\": \"2024-01-01T00:00:00.000Z\",
        \"saved_to\": \"outputs/screenshot.png\"
      }"
    }
  ]
}
```

## Testing with Docker

To test with Docker container:
```bash
# Build image
docker build -t puppeteer-mcp-server .

# Run with volume mount for outputs
docker run -it -v $(pwd)/outputs:/app/outputs puppeteer-mcp-server
```

Then use the same test examples above.