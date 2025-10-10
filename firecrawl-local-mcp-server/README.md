# Firecrawl Local MCP Server

A Model Context Protocol (MCP) server implementation that integrates with locally hosted [Firecrawl](https://github.com/mendableai/firecrawl) for web scraping capabilities.

## Features

- Web scraping, crawling, and discovery
- Search and content extraction
- Deep research and batch scraping
- Automatic retries and rate limiting
- Local Firecrawl instance support
- SSE support for streaming operations

## Prerequisites

- Node.js 18+ installed
- Docker and Docker Compose installed
- Local Firecrawl instance (included via docker-compose.yaml)

## Quick Start

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/mendableai/firecrawl-mcp-server.git
cd firecrawl-mcp-server

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env
```

### Step 2: Start Local Firecrawl

```bash
# Start Firecrawl services (API, Redis, Playwright, Workers)
docker-compose up -d

# Verify services are running
docker-compose ps
```

The Firecrawl API will be available at `http://localhost:3002`

### Step 3: Configure Environment

Edit the `.env` file (already configured for local use):

```env
# Local Firecrawl API Configuration
FIRECRAWL_API_URL=http://localhost:3002

# Set to 'local' for local development mode
FIRECRAWL_MODE=local

# Optional: Logging level
LOGGING_LEVEL=info
```

### Step 4: Build and Run MCP Server

```bash
# Build the TypeScript code
npm run build

# Run the MCP server
npm run start
```

## Installation in Claude Desktop

### Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "firecrawl-local": {
      "command": "node",
      "args": ["/path/to/firecrawl-local-mcp/dist/index.js"],
      "env": {
        "FIRECRAWL_API_URL": "http://localhost:3002",
        "FIRECRAWL_MODE": "local"
      }
    }
  }
}
```

Replace `/path/to/firecrawl-local-mcp` with the actual path to your installation.

## Installation in Cursor

Add this to your Cursor configuration:

1. Open Cursor Settings
2. Go to Features > MCP Servers  
3. Click "+ Add new global MCP server"
4. Enter the following:

```json
{
  "mcpServers": {
    "firecrawl-local": {
      "command": "node",
      "args": ["/path/to/firecrawl-local-mcp/dist/index.js"],
      "env": {
        "FIRECRAWL_API_URL": "http://localhost:3002",
        "FIRECRAWL_MODE": "local"
      }
    }
  }
}
```

## Installation in VS Code

Add to your User Settings (JSON) or `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "firecrawl-local": {
        "command": "node",
        "args": ["/path/to/firecrawl-local-mcp/dist/index.js"],
        "env": {
          "FIRECRAWL_API_URL": "http://localhost:3002",
          "FIRECRAWL_MODE": "local"
        }
      }
    }
  }
}
```

## Running with NPX (Alternative)

```bash
# Set environment variables and run directly
FIRECRAWL_API_URL=http://localhost:3002 FIRECRAWL_MODE=local npx -y firecrawl-mcp
```

## Docker Compose Services

The included `docker-compose.yaml` file starts the following services:

- **api** (port 3002): Main Firecrawl API server
- **worker**: Background job processor
- **redis**: Cache and job queue
- **playwright-service**: Browser automation for scraping

### Managing Services

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Reset everything (including volumes)
docker-compose down -v
```

## Available MCP Tools

### 1. firecrawl_scrape
Scrape content from a single URL with advanced options.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ | The URL to scrape |
| `formats` | array | ❌ | Content formats: `markdown`, `html`, `rawHtml`, `screenshot`, `links`, `screenshot@fullPage`, `extract` (default: `['markdown']`) |
| `onlyMainContent` | boolean | ❌ | Extract only main content, filtering out navigation, footers |
| `includeTags` | array | ❌ | HTML tags to specifically include |
| `excludeTags` | array | ❌ | HTML tags to exclude |
| `waitFor` | number | ❌ | Time in milliseconds to wait for dynamic content |
| `timeout` | number | ❌ | Maximum time in milliseconds to wait for page load |
| `actions` | array | ❌ | Actions to perform before scraping (click, wait, scroll, etc.) |
| `extract` | object | ❌ | Configuration for structured data extraction |
| `mobile` | boolean | ❌ | Use mobile viewport |
| `skipTlsVerification` | boolean | ❌ | Skip TLS certificate verification |
| `removeBase64Images` | boolean | ❌ | Remove base64 encoded images |
| `location` | object | ❌ | Location settings (country, languages) |
| `maxAge` | number | ❌ | Maximum age in ms for cached content (0 = always fresh) |
| `output_file` | string | ❌ | File path to save scraped content |

**Example:**
```json
{
  "url": "https://example.com",
  "formats": ["markdown", "links"],
  "onlyMainContent": true,
  "waitFor": 2000
}
```

### 2. firecrawl_map
Map a website to discover all indexed URLs.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ | Starting URL for discovery |
| `search` | string | ❌ | Search term to filter URLs |
| `ignoreSitemap` | boolean | ❌ | Skip sitemap.xml discovery |
| `sitemapOnly` | boolean | ❌ | Only use sitemap.xml for discovery |
| `includeSubdomains` | boolean | ❌ | Include URLs from subdomains |
| `limit` | number | ❌ | Maximum number of URLs to return |
| `output_file` | string | ❌ | File path to save discovered URLs |

**Example:**
```json
{
  "url": "https://example.com",
  "limit": 100,
  "includeSubdomains": false
}
```

### 3. firecrawl_crawl
Start an asynchronous crawl job on a website.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ | Starting URL for crawl |
| `excludePaths` | array | ❌ | URL paths to exclude |
| `includePaths` | array | ❌ | Only crawl these URL paths |
| `maxDepth` | number | ❌ | Maximum link depth to crawl |
| `ignoreSitemap` | boolean | ❌ | Skip sitemap.xml discovery |
| `limit` | number | ❌ | Maximum number of pages to crawl |
| `allowBackwardLinks` | boolean | ❌ | Allow crawling parent directories |
| `allowExternalLinks` | boolean | ❌ | Allow crawling external domains |
| `webhook` | string/object | ❌ | Webhook URL for completion notification |
| `deduplicateSimilarURLs` | boolean | ❌ | Remove similar URLs during crawl |
| `ignoreQueryParameters` | boolean | ❌ | Ignore query parameters when comparing URLs |
| `scrapeOptions` | object | ❌ | Options for scraping each page |
| `output_file` | string | ❌ | File path to save crawl results |

**Example:**
```json
{
  "url": "https://example.com/blog",
  "maxDepth": 2,
  "limit": 50,
  "allowExternalLinks": false,
  "scrapeOptions": {
    "formats": ["markdown"],
    "onlyMainContent": true
  }
}
```

### 4. firecrawl_check_crawl_status
Check the status of a crawl job.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | ✅ | Crawl job ID to check |

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5. firecrawl_search
Search the web and optionally extract content from results.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search query string |
| `limit` | number | ❌ | Maximum number of results (default: 5) |
| `lang` | string | ❌ | Language code (default: "en") |
| `country` | string | ❌ | Country code (default: "us") |
| `tbs` | string | ❌ | Time-based search filter |
| `filter` | string | ❌ | Search filter |
| `location` | string | ❌ | Location for search results |
| `scrapeOptions` | object | ❌ | Options for scraping search results |
| `output_file` | string | ❌ | File path to save search results |

**Example:**
```json
{
  "query": "latest AI developments 2024",
  "limit": 10,
  "lang": "en",
  "scrapeOptions": {
    "formats": ["markdown"],
    "onlyMainContent": true
  }
}
```

### 6. firecrawl_extract
Extract structured information from web pages using LLM capabilities.

**⚠️ Note:** Requires LLM configuration (OpenAI/Ollama) in your local Firecrawl instance.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | array | ✅ | List of URLs to extract from |
| `prompt` | string | ❌ | Custom prompt for LLM extraction |
| `systemPrompt` | string | ❌ | System prompt to guide the LLM |
| `schema` | object | ❌ | JSON schema for structured data extraction |
| `allowExternalLinks` | boolean | ❌ | Allow extraction from external links |
| `enableWebSearch` | boolean | ❌ | Enable web search for additional context |
| `includeSubdomains` | boolean | ❌ | Include subdomains in extraction |
| `output_file` | string | ❌ | File path to save extracted data |

**Example:**
```json
{
  "urls": ["https://example.com/product1", "https://example.com/product2"],
  "prompt": "Extract product information",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "price": {"type": "number"},
      "description": {"type": "string"}
    }
  }
}
```

### 7. firecrawl_deep_research
Conduct deep web research using intelligent crawling and LLM analysis.

**⚠️ Note:** Requires LLM configuration in your local Firecrawl instance.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Research question or topic |
| `maxDepth` | number | ❌ | Maximum recursive depth (1-10, default: 3) |
| `timeLimit` | number | ❌ | Time limit in seconds (30-300, default: 120) |
| `maxUrls` | number | ❌ | Maximum URLs to analyze (1-1000, default: 50) |
| `output_file` | string | ❌ | File path to save research results |

**Example:**
```json
{
  "query": "What are the latest breakthroughs in quantum computing?",
  "maxDepth": 3,
  "timeLimit": 180,
  "maxUrls": 75
}
```

### 8. firecrawl_generate_llmstxt
Generate a standardized llms.txt file for a given domain.

**Arguments:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ | The base URL of the website |
| `maxUrls` | number | ❌ | Max URLs to include (1-100, default: 10) |
| `showFullText` | boolean | ❌ | Include llms-full.txt contents |
| `output_file` | string | ❌ | File path to save the generated file |

**Example:**
```json
{
  "url": "https://example.com",
  "maxUrls": 20,
  "showFullText": true
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIRECRAWL_API_URL` | URL of local Firecrawl instance | `http://localhost:3002` |
| `FIRECRAWL_MODE` | Set to 'local' for local development | `local` |
| `LOGGING_LEVEL` | Logging verbosity (debug, info, warning, error) | `info` |
| `FIRECRAWL_RETRY_MAX_ATTEMPTS` | Maximum retry attempts for rate limiting | `3` |
| `FIRECRAWL_RETRY_INITIAL_DELAY` | Initial retry delay in milliseconds | `1000` |
| `FIRECRAWL_RETRY_MAX_DELAY` | Maximum retry delay in milliseconds | `10000` |
| `FIRECRAWL_RETRY_BACKOFF_FACTOR` | Exponential backoff factor | `2` |
| `SSE_LOCAL` | Enable SSE mode instead of stdio | `false` |
| `PORT` | Port for SSE mode | `3000` |

## Local Development Tips

### 1. Configure LLM Support (Optional)
For tools like `extract` and `deep_research`, configure OpenAI or Ollama in your local Firecrawl instance.

Edit the `docker-compose.yaml` environment section:

```yaml
environment:
  # For OpenAI
  OPENAI_API_KEY: your-openai-key
  # OR for Ollama
  OLLAMA_BASE_URL: http://host.docker.internal:11434
```

Then restart the services:
```bash
docker-compose down
docker-compose up -d
```

### 2. Monitor Logs

```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# View all logs
docker-compose logs -f
```

### 3. Performance Tuning

- Adjust `waitFor` and `timeout` values based on target sites
- Use `maxAge` parameter for caching frequently accessed pages
- Limit crawl depth and page count to avoid overwhelming local resources

### 4. Troubleshooting

**Services not starting:**
```bash
# Check if ports are already in use
lsof -i :3002
lsof -i :6379

# Reset and restart
docker-compose down -v
docker-compose up -d
```

**Connection errors:**
- Ensure Docker services are running: `docker-compose ps`
- Check if Firecrawl API is accessible: `curl http://localhost:3002/health`
- Verify environment variables are set correctly

**LLM features not working:**
- Ensure OpenAI API key or Ollama is configured in docker-compose.yaml
- Check worker logs for LLM-related errors: `docker-compose logs -f worker`

## How to Choose the Right Tool

| Use Case | Recommended Tool | Why |
|----------|-----------------|-----|
| Single known URL | `firecrawl_scrape` | Optimized for single page extraction |
| Multiple known URLs | `firecrawl_map` + `firecrawl_scrape` | Better control over what to scrape |
| Discover URLs on a site | `firecrawl_map` | Returns all URLs without content |
| Full site content | `firecrawl_crawl` | Gets content from all pages (use limits!) |
| Web search | `firecrawl_search` | Searches across the web |
| Structured data | `firecrawl_extract` | LLM-powered extraction (requires LLM config) |
| Research task | `firecrawl_deep_research` | Multi-source analysis (requires LLM config) |
| LLMs.txt generation | `firecrawl_generate_llmstxt` | Creates AI interaction guidelines |

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Run in development mode
npm run dev
```

## License

MIT

## Support

For issues related to:
- MCP Server: [GitHub Issues](https://github.com/mendableai/firecrawl-mcp-server/issues)
- Firecrawl: [Firecrawl GitHub](https://github.com/mendableai/firecrawl)