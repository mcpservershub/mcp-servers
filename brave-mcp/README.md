# Brave search MCP Server

This MCP Server requires `BRAVE_API_KEY` to interact with Brave search engine.
`export BRAVE_API_KEY=<Brave API Key>

### Getting an API Key

1. Sign up for a [Brave Search API account](https://brave.com/search/api/)
2. Choose a plan (Free tier available with 2,000 queries/month)
3. Generate your API key [from the developer dashboard](https://api-dashboard.search.brave.com/app/keys)

The config to start the MCP Server in a container:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "BRAVE_API_KEY",
        "santoshkal/brave-search-mcp"
      ],
      "env": {
        "BRAVE_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

## Available tools

- **brave_web_search**

  - Execute web searches with pagination and filtering
  - Inputs:
    - `query` (string): Search terms
    - `count` (number, optional): Results per page (max 20)
    - `offset` (number, optional): Pagination offset (max 9)

- **brave_local_search**
  - Search for local businesses and services
  - Inputs:
    - `query` (string): Local search terms
    - `count` (number, optional): Number of results (max 20)
  - Automatically falls back to web search if no local results found

---
*Last updated: 2025-07-29 16:13:12 UTC*
