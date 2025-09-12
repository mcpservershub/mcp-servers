# OneFileLLM MCP Server - Simple Version

A lightweight MCP server for OneFileLLM with essential features only.

## Features

- 🚀 **Minimal size** - Alpine-based Docker image (~200MB vs 1GB+)
- 🎯 **Essential tools only** - Core functionality without bloat
- 🔑 **Simple token handling** - Build-time token configuration
- ⚡ **Fast startup** - No complex wrappers or multiple layers

## Available Tools

1. **github_repo** - Fetch GitHub repository contents
2. **github_issue** - Fetch GitHub issue with comments  
3. **github_pr** - Fetch GitHub pull request with diff
4. **crawl_web** - Crawl website and extract text
5. **youtube_transcript** - Get YouTube video transcript
6. **arxiv_paper** - Fetch ArXiv paper content
7. **count_tokens** - Count tokens in text

## Building

### With GitHub Token (Required for GitHub operations)

```bash
docker build --build-arg GITHUB_TOKEN="your_github_token_here" -t onefilellm-simple .
```

### Without GitHub Token (Web-only operations)

```bash
docker build -t onefilellm-simple .
```

## Running with MCP Inspector

```bash
npx @modelcontextprotocol/inspector docker run -i onefilellm-simple
```

## Direct Testing

Test a specific tool:
```bash
docker run --rm onefilellm-simple python -c "
import asyncio
from server import crawl_web
result = asyncio.run(crawl_web('https://example.com', 1))
print(result[:500])
"
```

## Security Note

The GitHub token is embedded in the Docker image when built with `--build-arg`. 
Do not push images with tokens to public registries.

## Size Comparison

- Original: ~1.2GB (Debian-based, full Python environment)
- Simple: ~200MB (Alpine-based, minimal dependencies)

## Requirements

- Docker
- GitHub Personal Access Token (for GitHub operations)
- MCP Inspector (for testing)