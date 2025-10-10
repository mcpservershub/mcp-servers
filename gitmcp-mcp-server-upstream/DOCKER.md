# Docker Setup for GitMCP

This document provides instructions for building and running GitMCP using Docker.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the container:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f git-mcp
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image:**
   ```bash
   docker build -t git-mcp:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name git-mcp \
     -p 8787:8787 \
     git-mcp:latest
   ```

3. **View logs:**
   ```bash
   docker logs -f git-mcp
   ```

4. **Stop and remove the container:**
   ```bash
   docker stop git-mcp
   docker rm git-mcp
   ```

## Configuration

### Environment Variables

You can pass environment variables to the container using the `-e` flag or by creating a `.env` file:

```bash
docker run -d \
  --name git-mcp \
  -p 8787:8787 \
  -e OPENAI_API_KEY=your_key_here \
  -e ANTHROPIC_API_KEY=your_key_here \
  -e XAI_API_KEY=your_key_here \
  git-mcp:latest
```

Or using Docker Compose, uncomment the environment variables in `docker-compose.yml` and create a `.env` file:

```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
XAI_API_KEY=your_key_here
```

### Custom Configuration

To use a custom wrangler configuration, mount your config file:

```bash
docker run -d \
  --name git-mcp \
  -p 8787:8787 \
  -v $(pwd)/wrangler.jsonc:/app/wrangler.jsonc:ro \
  git-mcp:latest
```

## Single-stage Build

The Dockerfile uses a single-stage build process with Chainguard Node.js as the base image for optimal size, security, and compatibility:

1. **Chainguard Base**: Uses Chainguard's Node.js image (glibc-based, minimal, secure)
2. **Dependencies**: Installs all dependencies using pnpm with frozen lockfile
3. **Build**: Compiles the application
4. **Security**: Runs as a non-root user (node user by default in Chainguard)

### Why Chainguard instead of Alpine?

- **glibc compatibility**: Cloudflare's `workerd` binary requires glibc (not available in Alpine's musl)
- **Smaller size**: ~875MB vs 1.5GB+ with Alpine or Debian
- **Security-focused**: Chainguard images are minimal and regularly updated for security
- **No compatibility layers needed**: Works directly with native binaries

This approach is optimal for this application because:
- Wrangler requires devDependencies to run
- The application runs in development mode (`wrangler dev`)
- Simpler to maintain and debug
- Faster build times with proper layer caching
- Native glibc support for workerd binary

## Health Checks

The container includes a health check that verifies the application is running:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' git-mcp
```

## Accessing the Application

Once the container is running, you can access GitMCP at:

- **Local Development**: http://localhost:8787
- **MCP Server**: The container exposes the MCP protocol on port 8787

## Troubleshooting

### Container won't start

Check the logs for errors:
```bash
docker logs git-mcp
```

### Port already in use

Change the host port in the docker run command or docker-compose.yml:
```bash
docker run -d --name git-mcp -p 8788:8787 git-mcp:latest
```

### Build failures

Clean Docker cache and rebuild:
```bash
docker builder prune -a
docker build --no-cache -t git-mcp:latest .
```

### Permission issues

The container runs as a non-root user (node user in Chainguard) for security. If you encounter permission issues, ensure mounted volumes have appropriate permissions.

## Production Deployment

For production deployments, consider:

1. **Using secrets management** for API keys instead of environment variables
2. **Setting resource limits**:
   ```yaml
   services:
     git-mcp:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 2G
           reservations:
             cpus: '0.5'
             memory: 1G
   ```

3. **Using a reverse proxy** (nginx, Traefik, etc.) for SSL/TLS termination
4. **Implementing logging and monitoring** solutions
5. **Regular image updates** to include security patches

## Image Size Optimization

The Chainguard-based build produces an optimized image (~875MB):

```bash
# Check image size
docker images git-mcp
```

The Chainguard image is significantly smaller than Alpine (which doesn't work with workerd) or Debian-based images.

To further optimize:
- Remove unnecessary dependencies from package.json
- Use `.dockerignore` to exclude files (already configured)
- Consider using multi-architecture builds
- Review and minimize runtime dependencies

## Development with Docker

For active development, you can mount your source code:

```bash
docker run -d \
  --name git-mcp-dev \
  -p 8787:8787 \
  -v $(pwd)/src:/app/src:ro \
  git-mcp:latest
```

Note: You'll need to rebuild the image after code changes as Wrangler doesn't support hot reload in containers.

## Building for Different Architectures

Build for multiple platforms using buildx:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t git-mcp:latest \
  --push .
```

## Cleanup

Remove all GitMCP containers and images:

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi git-mcp:latest

# Remove dangling images
docker image prune -f
```

## Support

For issues related to Docker deployment, please check:
- [GitMCP GitHub Issues](https://github.com/idosal/git-mcp/issues)
- [Docker Documentation](https://docs.docker.com/)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
