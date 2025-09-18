# Shadcn UI MCP Server - Docker Setup

This Docker setup provides a secure, minimal container for running the Shadcn UI MCP Server using Chainguard base images.

## Features

- **Multi-stage build** for minimal image size
- **Chainguard base images** for enhanced security (CVE-free, minimal attack surface)
- **Framework flexibility** via environment variables
- **GitHub API key support** for increased rate limits
- **Non-root execution** by default
- **Distroless runtime** image (no shell, package managers, or unnecessary binaries)

## Quick Start

### Build the Image

```bash
docker build -t shadcn-ui-mcp-server .
```

### Run with Different Frameworks

```bash
# React (default)
docker run --rm shadcn-ui-mcp-server

# Vue
docker run --rm -e FRAMEWORK=vue shadcn-ui-mcp-server

# Svelte
docker run --rm -e FRAMEWORK=svelte shadcn-ui-mcp-server

# React Native
docker run --rm -e FRAMEWORK=react-native shadcn-ui-mcp-server
```

### Run with GitHub API Key

```bash
# Basic usage (60 requests/hour)
docker run --rm shadcn-ui-mcp-server

# With GitHub token (5000 requests/hour) - Recommended
docker run --rm -e GITHUB_API_KEY=ghp_your_token_here shadcn-ui-mcp-server
```

## Docker Compose Usage

### Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your GitHub API key (optional but recommended)

### Run with Docker Compose

```bash
# Run React framework (default)
docker-compose --profile react up

# Run Vue framework
docker-compose --profile vue up

# Run Svelte framework
docker-compose --profile svelte up

# Run React Native framework
docker-compose --profile react-native up

# Run with dynamic framework selection (uses .env file)
docker-compose --profile all up
```

### Run in Background

```bash
docker-compose --profile react up -d
```

### View Logs

```bash
docker-compose logs -f shadcn-mcp-react
```

### Stop Services

```bash
docker-compose down
```

## Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `FRAMEWORK` | UI framework to use | `react` | `react`, `vue`, `svelte`, `react-native` |
| `GITHUB_API_KEY` | GitHub personal access token | (empty) | Your GitHub token |
| `NODE_ENV` | Node.js environment | `production` | `production`, `development` |

## Security Features

1. **Chainguard Base Images**:
   - Regularly updated with latest security patches
   - Minimal attack surface
   - No known CVEs

2. **Distroless Runtime**:
   - No shell access
   - No package managers
   - Only Node.js runtime and application code

3. **Non-root User**:
   - Runs as UID 65532 (non-root) by default
   - Cannot modify system files

4. **Minimal Dependencies**:
   - Only production dependencies in final image
   - Development dependencies removed after build

## Image Details

The Docker image is built in three stages:

1. **Builder Stage** (`cgr.dev/chainguard/node:latest-dev`):
   - Installs dependencies
   - Compiles TypeScript to JavaScript
   - Removes development dependencies

2. **Runtime Prep Stage** (`cgr.dev/chainguard/node:latest-dev`):
   - Creates the entrypoint script for handling environment variables

3. **Final Stage** (`cgr.dev/chainguard/node:latest`):
   - Distroless image with only Node.js runtime
   - Contains only production code and dependencies
   - Minimal size and attack surface

## Troubleshooting

### Rate Limiting Issues

If you encounter rate limiting (60 requests/hour without token), add a GitHub API key:

```bash
docker run --rm -e GITHUB_API_KEY=ghp_your_token_here shadcn-ui-mcp-server
```

### Framework Not Switching

Ensure you're using the correct framework name:
- `react` (not `React` or `REACT`)
- `vue` (not `Vue` or `VUE`)
- `svelte` (not `Svelte` or `SVELTE`)
- `react-native` (not `react_native` or `ReactNative`)

### Building Behind Proxy

If building behind a corporate proxy:

```bash
docker build \
  --build-arg HTTP_PROXY=http://proxy.example.com:8080 \
  --build-arg HTTPS_PROXY=http://proxy.example.com:8080 \
  -t shadcn-ui-mcp-server .
```

## Advanced Usage

### Custom Command Arguments

You can pass additional arguments to the MCP server:

```bash
docker run --rm shadcn-ui-mcp-server --custom-arg value
```

### Volume Mounting for Cache

If the MCP server supports caching, you can mount a volume:

```bash
docker run --rm \
  -v $(pwd)/cache:/app/cache \
  -e GITHUB_API_KEY=ghp_your_token \
  shadcn-ui-mcp-server
```

## License

This Docker configuration follows the same MIT license as the original Shadcn UI MCP Server project.