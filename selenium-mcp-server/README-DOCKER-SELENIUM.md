# Docker Selenium Grid Setup

This guide explains how to use the Selenium MCP Server with docker-selenium for a secure, scalable, and minimal deployment.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Selenium MCP   │    │  Selenium Hub   │    │   Browser Nodes │
│     Server      │◄──►│      4444       │◄──►│ Chrome/Firefox/ │
│  (Chainguard)   │    │                 │    │      Edge       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Using Chainguard Base Image (Secure & Minimal)

```bash
# Build and start the complete Selenium Grid with MCP Server
docker-compose -f docker-compose.selenium-grid.yml up -d

# Check services status
docker-compose -f docker-compose.selenium-grid.yml ps

# View MCP Server logs
docker-compose -f docker-compose.selenium-grid.yml logs -f selenium-mcp
```

### 2. Development Mode

```bash
# Start with development profile (hot reload)
docker-compose -f docker-compose.selenium-grid.yml --profile dev up -d selenium-mcp-dev

# View development logs
docker-compose -f docker-compose.selenium-grid.yml logs -f selenium-mcp-dev
```

### 3. With VNC Debugging

```bash
# Start with UI profile for VNC access
docker-compose -f docker-compose.selenium-grid.yml --profile ui up -d

# Access VNC interfaces:
# Chrome: http://localhost:5900 (password: secret)
# Firefox: http://localhost:5901 (password: secret)
# Edge: http://localhost:5902 (password: secret)
# Selenium UI: http://localhost:7900 (password: secret)
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SELENIUM_GRID_HOST` | `selenium-hub` | Selenium Hub hostname |
| `SELENIUM_GRID_PORT` | `4444` | Selenium Hub port |
| `SELENIUM_GRID_URL` | `http://selenium-hub:4444/wd/hub` | Full Grid URL |
| `LOG_LEVEL` | `INFO` | Logging level |

### Browser Node Scaling

Scale browser nodes based on your needs:

```bash
# Scale Chrome nodes to 3 instances
docker-compose -f docker-compose.selenium-grid.yml up -d --scale chrome=3

# Scale all browser types
docker-compose -f docker-compose.selenium-grid.yml up -d --scale chrome=2 --scale firefox=2 --scale edge=1
```

## 🐳 Container Details

### Selenium Hub
- **Image:** `selenium/hub:latest`
- **Ports:** 4442 (events), 4443 (publisher), 4444 (web/grid)
- **Max Sessions:** 16 concurrent
- **Timeout:** 300 seconds

### Browser Nodes

#### Chrome Node
- **Image:** `selenium/node-chrome:latest`
- **VNC Port:** 5900 (for debugging)
- **Max Sessions:** 4 per node
- **Shared Memory:** 2GB

#### Firefox Node
- **Image:** `selenium/node-firefox:latest`
- **VNC Port:** 5901 (for debugging)
- **Max Sessions:** 4 per node
- **Shared Memory:** 2GB

#### Edge Node
- **Image:** `selenium/node-edge:latest`
- **VNC Port:** 5902 (for debugging)
- **Max Sessions:** 4 per node
- **Shared Memory:** 2GB

### MCP Server (Chainguard)
- **Base:** `cgr.dev/chainguard/python:latest`
- **Size:** ~50MB (vs ~500MB+ traditional images)
- **Security:** Minimal attack surface, distroless
- **User:** Non-root `selenium` user (UID: 1200)

## 🧪 Testing

### 1. Check Grid Status
```bash
# Grid console
curl http://localhost:4444/wd/hub/status | jq

# Available nodes
curl http://localhost:4444/grid/api/hub/status | jq
```

### 2. Test MCP Server with Grid

```bash
# Connect to MCP server container
docker exec -it selenium-mcp-server /bin/sh

# Test browser creation (should use Grid)
python -c "
from selenium_mcp.browser_manager import BrowserManager
from selenium_mcp.models import BrowserType, BrowserOptions
import asyncio

async def test():
    manager = BrowserManager()
    session_id = await manager.create_session(BrowserType.CHROME, BrowserOptions())
    print(f'Created session: {session_id}')
    await manager.close_session(session_id)

asyncio.run(test())
"
```

### 3. MCP Inspector with Grid

```json
{
  "command": "docker",
  "args": ["exec", "-i", "selenium-mcp-server", "python", "-m", "selenium_mcp.server"],
  "env": {
    "SELENIUM_GRID_URL": "http://selenium-hub:4444/wd/hub"
  }
}
```

## 📊 Monitoring

### Grid Console
- **URL:** http://localhost:4444/grid/console
- **API:** http://localhost:4444/grid/api/hub

### Health Checks

```bash
# Check all services health
docker-compose -f docker-compose.selenium-grid.yml ps

# Individual service health
docker inspect selenium-hub --format='{{.State.Health.Status}}'
docker inspect selenium-mcp-server --format='{{.State.Health.Status}}'
```

### VNC Debugging (Optional)

Access browser sessions visually:

```bash
# Enable VNC (add to browser node env vars)
SE_VNC_NO_PASSWORD=1

# Access via VNC viewer or web:
# Chrome: vnc://localhost:5900
# Firefox: vnc://localhost:5901
# Edge: vnc://localhost:5902
```

## 🔒 Security Benefits

### Chainguard Base Images
- **CVE-free:** Regular security updates
- **Minimal:** ~50MB vs 500MB+ traditional images
- **Distroless:** No package manager, shell, or unnecessary tools
- **SBOM:** Software Bill of Materials included
- **Signed:** Cryptographically signed images

### Network Isolation
```yaml
networks:
  selenium-grid:
    driver: bridge
    internal: true  # Add this for complete isolation
```

### Resource Limits
```yaml
services:
  selenium-mcp:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

## 🚦 Production Deployment

### 1. Resource Optimization

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  selenium-hub:
    environment:
      - GRID_MAX_SESSION=32  # Increase for production
      - GRID_SESSION_TIMEOUT=300
      - GRID_BROWSER_TIMEOUT=600
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  chrome:
    deploy:
      replicas: 3  # Scale based on load
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 2. Persistent Storage

```yaml
volumes:
  - ./logs:/app/logs
  - ./screenshots:/home/selenium/screenshots:rw
  - ./downloads:/home/selenium/downloads:rw
```

### 3. Health Monitoring

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://selenium-hub:4444/wd/hub/status"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## 🛠️ Troubleshooting

### Common Issues

1. **Grid Not Ready**
   ```bash
   # Wait for grid to be healthy
   docker-compose -f docker-compose.selenium-grid.yml logs selenium-hub
   ```

2. **Browser Sessions Stuck**
   ```bash
   # Clean stuck sessions
   curl -X DELETE http://localhost:4444/se/grid/newsessionqueue/queue
   ```

3. **Resource Exhaustion**
   ```bash
   # Monitor resource usage
   docker stats

   # Scale down if needed
   docker-compose -f docker-compose.selenium-grid.yml down
   docker system prune -f
   ```

### Debug Commands

```bash
# Check grid status
curl http://localhost:4444/wd/hub/status | jq '.value.ready'

# List active sessions
curl http://localhost:4444/grid/api/sessions | jq

# MCP Server logs with Grid connection info
docker-compose -f docker-compose.selenium-grid.yml logs selenium-mcp | grep -i grid
```

## 📈 Performance Tuning

### Browser Node Optimization

```yaml
chrome:
  environment:
    - SE_NODE_OVERRIDE_MAX_SESSIONS=true
    - SE_NODE_MAX_SESSIONS=8  # Increase based on resources
    - SE_VNC_NO_PASSWORD=1
    - JAVA_OPTS="-Xmx1024m"  # JVM heap size
```

### Hub Optimization

```yaml
selenium-hub:
  environment:
    - GRID_MAX_SESSION=64
    - GRID_SESSION_TIMEOUT=600
    - JAVA_OPTS="-Xmx2048m"
```

This setup provides a production-ready, secure, and scalable Selenium Grid infrastructure using minimal Chainguard images! 🚀