# Docker Testing Guide - Pytest MCP Server

## Quick Start

### 1. Build and Run Container
```bash
# Using Docker Compose (recommended)
docker-compose up --build pytest-mcp-server

# Or using Docker directly
docker build -t pytest-mcp-server:latest .
docker run -p 8000:8000 -v pytest_mcp_data:/app/data pytest-mcp-server:latest
```

### 2. Verify Server is Running
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools
```

### 3. Run Automated Tests
```bash
# Make script executable
chmod +x test_docker_tools.sh

# Run all tests
./test_docker_tools.sh
```

## All 9 MCP Tools - Docker Test Commands

### Tool 1: `record_session_start`
```bash
curl -X POST http://localhost:8000/tools/record_session_start \
  -H "Content-Type: application/json" \
  -d '{
    "environment": {
      "os": "Linux",
      "python_version": "3.12.0"
    }
  }'
```

### Tool 2: `record_test_outcome` (Passing)
```bash
curl -X POST http://localhost:8000/tools/record_test_outcome \
  -H "Content-Type: application/json" \
  -d '{
    "nodeid": "test_example.py::test_pass",
    "outcome": "passed",
    "duration": 0.123
  }'
```

### Tool 3: `record_test_outcome` (Failing)
```bash
curl -X POST http://localhost:8000/tools/record_test_outcome \
  -H "Content-Type: application/json" \
  -d '{
    "nodeid": "test_example.py::test_fail",
    "outcome": "failed",
    "duration": 0.456,
    "error": "AssertionError: assert 1 == 2"
  }'
```

### Tool 4: `record_session_finish`
```bash
curl -X POST http://localhost:8000/tools/record_session_finish \
  -H "Content-Type: application/json" \
  -d '{
    "summary": {
      "total_tests": 2,
      "passed": 1,
      "failed": 1,
      "skipped": 0,
      "exitstatus": 1,
      "duration": 0.579
    }
  }'
```

### Tool 5: `get_session_status`
```bash
curl -X POST http://localhost:8000/tools/get_session_status \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Tool 6: `get_failure_analysis`
```bash
curl -X POST http://localhost:8000/tools/get_failure_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "test_nodeid": "test_example.py::test_fail"
  }'
```

### Tool 7: `find_similar_failures`
```bash
curl -X POST http://localhost:8000/tools/find_similar_failures \
  -H "Content-Type: application/json" \
  -d '{
    "error_pattern": "AssertionError",
    "limit": 5
  }'
```

### Tool 8: `track_debugging_progress`
```bash
curl -X POST http://localhost:8000/tools/track_debugging_progress \
  -H "Content-Type: application/json" \
  -d '{
    "failure_id": "demo-failure",
    "action": "add_step",
    "step_description": "Analyzed the assertion"
  }'
```

### Tool 9: `generate_debugging_prompt`
```bash
curl -X POST http://localhost:8000/tools/generate_debugging_prompt \
  -H "Content-Type: application/json" \
  -d '{
    "test_nodeid": "test_example.py::test_fail"
  }'
```

### Tool 10: `get_test_statistics`
```bash
curl -X POST http://localhost:8000/tools/get_test_statistics \
  -H "Content-Type: application/json" \
  -d '{}'
```

## MCP Inspector Testing

1. **Start container:** `docker-compose up pytest-mcp-server`
2. **Install MCP Inspector:** `npx @modelcontextprotocol/inspector`
3. **Open:** `http://localhost:5173`
4. **Connect to server:** `http://localhost:8000`
5. **Test all tools interactively**

## Expected Responses

All successful tool calls return:
```json
{
  "success": true,
  "message": "...",
  // tool-specific data
}
```

Failed calls return:
```json
{
  "success": false,
  "error": "error description",
  // optional error details
}
```

## Container Management

```bash
# View container logs
docker logs pytest-mcp-server

# Stop container
docker stop pytest-mcp-server

# Remove container
docker rm pytest-mcp-server

# Remove image
docker rmi pytest-mcp-server:latest

# Clean up volumes
docker volume rm pytest_mcp_data
```

## Environment Variables

Configure the container:
```bash
docker run -p 8000:8000 \
  -e PYTEST_MCP_DB_PATH=/app/data/pytest_mcp.db \
  -e PYTEST_MCP_LOG_LEVEL=DEBUG \
  -v pytest_mcp_data:/app/data \
  pytest-mcp-server:latest
```

Available variables:
- `PYTEST_MCP_DB_PATH`: Database path
- `PYTEST_MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `PYTEST_MCP_HOST`: Bind host (default: 0.0.0.0)
- `PYTEST_MCP_PORT`: Port (default: 8000)

## Troubleshooting

**Container won't start:**
```bash
docker logs pytest-mcp-server
```

**Can't connect to server:**
```bash
curl -v http://localhost:8000/health
```

**Tools return errors:**
- Check request JSON syntax
- Verify required parameters
- Check container logs for details

**Database issues:**
- Ensure volume is mounted: `-v pytest_mcp_data:/app/data`
- Check database path environment variable