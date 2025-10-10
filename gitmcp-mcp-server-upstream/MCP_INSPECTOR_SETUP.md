# Using GitMCP Docker Container with MCP Inspector

This guide explains how to test your Dockerized GitMCP server with MCP Inspector.

## Important: GitMCP runs as an HTTP/SSE Server

GitMCP is **NOT** a stdio-based MCP server. It runs as an **HTTP server** using Server-Sent Events (SSE) for MCP communication.

This means:
- ❌ You **cannot** run it as a command-line tool
- ✅ You **must** connect to it via HTTP/SSE URL

## Step-by-Step Setup

### 1. Start the Docker Container

```bash
# Build the image (if not already built)
docker build -t git-mcp:latest .

# Run the container
docker run -d --name git-mcp -p 8787:8787 git-mcp:latest

# Verify it's running
docker logs git-mcp
```

You should see wrangler starting up and listening on port 8787.

### 2. Configure MCP Inspector

1. Open MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. In the MCP Inspector interface:
   - **Transport Type**: Select `SSE`
   - **SSE URL**: Enter one of these URLs:
     - For generic/docs endpoint: `http://localhost:8787/docs`
     - For specific repo: `http://localhost:8787/{owner}/{repo}`
   - Click **Connect**

### 3. URL Format Examples

**Generic endpoint** (can access any repo):
```
http://localhost:8787/docs
```

**Specific repository**:
```
http://localhost:8787/microsoft/typescript
http://localhost:8787/facebook/react
```

## Troubleshooting

### Error: "Command not found, transports removed"

This error occurs when MCP Inspector tries to execute GitMCP as a command-line tool.

**Solution**: GitMCP is an HTTP/SSE server, not a stdio server. Use the SSE transport type with a URL, not a command.

### Error: Connection refused

**Check if container is running:**
```bash
docker ps | grep git-mcp
```

**Check container logs:**
```bash
docker logs git-mcp
```

**Verify wrangler is listening:**
```bash
curl http://localhost:8787/docs
```

You should get an HTML response (the GitMCP web interface).

### Error: "Accept header must include text/event-stream"

This means you're accessing the root URL instead of a specific endpoint.

**Wrong**: `http://localhost:8787/`
**Correct**: `http://localhost:8787/docs`

### Port Issues

If port 8787 is already in use, you can map to a different port:

```bash
docker run -d --name git-mcp -p 9000:8787 git-mcp:latest
```

Then connect to: `http://localhost:9000/docs`

## How It Works

1. **Wrangler** runs the Cloudflare Worker locally on port 8787
2. **GitMCP** detects SSE requests by checking:
   - Request has `Accept: text/event-stream` header
   - URL path is not `/` (e.g., `/docs`, `/owner/repo`)
3. **MCP Inspector** connects via SSE and communicates using the MCP protocol
4. **Tools** are exposed for fetching documentation, searching code, etc.

## Testing the Connection

Once connected in MCP Inspector, you should see:

- **Server Info**: GitMCP v1.1.0
- **Available Tools**:
  - `fetch_generic_documentation` (for `/docs` endpoint)
  - `search_generic_documentation`
  - `search_generic_code`
  - `fetch_url_content`

Or for specific repos (`/owner/repo`):
  - `fetch_{repo}_documentation`
  - `search_{repo}_documentation`
  - `search_{repo}_code`
  - `fetch_url_content`

## Example: Testing with a Specific Repository

1. Start container:
   ```bash
   docker run -d --name git-mcp -p 8787:8787 git-mcp:latest
   ```

2. Open MCP Inspector and connect to:
   ```
   http://localhost:8787/microsoft/typescript
   ```

3. Try the `fetch_microsoft-typescript_documentation` tool

4. You should receive the TypeScript documentation

## Clean Up

```bash
# Stop and remove container
docker stop git-mcp
docker rm git-mcp

# Remove image (optional)
docker rmi git-mcp:latest
```

## For Production Use

For production deployment on Cloudflare Workers:

```bash
# Deploy to Cloudflare
pnpm run deploy
```

Then connect MCP clients to: `https://gitmcp.io/docs` or `https://gitmcp.io/{owner}/{repo}`
