# Complete Qdrant MCP Server Workflow Guide

This guide walks you through the entire process of setting up a local Qdrant instance, loading mock data, and using the MCP Server to query and add data.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ installed
- Node.js (for MCP Inspector) or Python environment

---

## Phase 1: Initial Setup

### Step 1: Start Qdrant Vector Database

```bash
cd /home/santosh/compare/mcp-server-qdrant

# Start Qdrant container
docker-compose up -d

# Verify Qdrant is running
curl http://localhost:6333/health

# Check the dashboard (optional)
# Open browser: http://localhost:6333/dashboard
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install individually
pip install qdrant-client sentence-transformers mcp-server-qdrant
```

### Step 3: Load Initial Mock Data

```bash
# Load mock data into the local Qdrant instance
python3 load_mock_data_client.py

# Or with options:
# python3 load_mock_data_client.py --recreate  # Start fresh
# python3 load_mock_data_client.py --collection my-data  # Custom collection name
```

After this step, your Qdrant instance will have:
- Code snippets
- Documentation
- Troubleshooting guides
- Architecture decisions

---

## Phase 2: Start MCP Server

### Step 4: Configure Environment

```bash
# Option A: Use environment file
source .env

# Option B: Export variables manually
export QDRANT_URL="http://localhost:6333"
export COLLECTION_NAME="test-collection"
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

### Step 5: Start the MCP Server

Choose one of the following methods:

#### Method 1: Direct stdio mode (for MCP Inspector)
```bash
uvx mcp-server-qdrant
```

#### Method 2: HTTP Server mode (for REST API access)
```bash
FASTMCP_PORT=8000 uvx mcp-server-qdrant
```

#### Method 3: Using Python directly
```bash
python -m mcp_server_qdrant
```

---

## Phase 3: Connect and Interact via MCP

### Option A: Using MCP Inspector

#### Step 6A: Install and Start MCP Inspector

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Start MCP Inspector
npx @modelcontextprotocol/inspector uvx mcp-server-qdrant
```

This will open a browser at http://localhost:5173

#### Step 7A: Test MCP Tools in Inspector

1. **List Available Tools**
   - You should see: `qdrant-store` and `qdrant-find`

2. **Query Existing Data**
   ```json
   {
     "tool": "qdrant-find",
     "arguments": {
       "query": "How to implement authentication in FastAPI",
       "limit": 5
     }
   }
   ```

3. **Add New Information**
   ```json
   {
     "tool": "qdrant-store",
     "arguments": {
       "information": "Redis Cluster Setup: Use redis-cli --cluster create command with at least 3 master nodes. Each master should have at least one replica for high availability. Configure cluster-enabled yes in redis.conf.",
       "metadata": {
         "type": "documentation",
         "category": "redis",
         "tags": ["redis", "cluster", "high-availability"]
       }
     }
   }
   ```

4. **Verify New Data Was Stored**
   ```json
   {
     "tool": "qdrant-find",
     "arguments": {
       "query": "Redis cluster setup",
       "limit": 3
     }
   }
   ```

### Option B: Using Python MCP Client

#### Step 6B: Create Python MCP Client

Create a file `mcp_client_test.py`:

```python
#!/usr/bin/env python3
"""
Simple MCP Client for testing Qdrant MCP Server
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_qdrant_mcp():
    """Test the Qdrant MCP Server tools"""
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-qdrant"],
        env={
            "QDRANT_URL": "http://localhost:6333",
            "COLLECTION_NAME": "test-collection"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test 1: Search for existing data
            print("\n1. Searching for FastAPI authentication...")
            result = await session.call_tool(
                "qdrant-find",
                arguments={
                    "query": "FastAPI authentication WebSocket",
                    "limit": 3
                }
            )
            print(f"Search results: {json.dumps(result, indent=2)}")
            
            # Test 2: Store new information
            print("\n2. Storing new information...")
            result = await session.call_tool(
                "qdrant-store",
                arguments={
                    "information": "GraphQL Subscription Implementation: Use WebSockets or Server-Sent Events for real-time updates. Implement connection lifecycle management. Handle authentication in connection params. Use DataLoader to prevent N+1 queries in subscriptions.",
                    "metadata": {
                        "type": "documentation",
                        "category": "graphql",
                        "tags": ["graphql", "subscriptions", "real-time", "websocket"]
                    }
                }
            )
            print(f"Store result: {result}")
            
            # Test 3: Verify the new data
            print("\n3. Verifying stored data...")
            result = await session.call_tool(
                "qdrant-find",
                arguments={
                    "query": "GraphQL subscriptions real-time",
                    "limit": 2
                }
            )
            print(f"Verification results: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_qdrant_mcp())
```

#### Step 7B: Run the Python Client

```bash
# Make the script executable
chmod +x mcp_client_test.py

# Install MCP Python client if needed
pip install mcp

# Run the test client
python3 mcp_client_test.py
```

---

## Phase 4: Advanced Usage Examples

### Example 1: Store Code Snippet via MCP

```python
# Using qdrant-store tool
{
  "tool": "qdrant-store",
  "arguments": {
    "information": """
Python async context manager for database transactions:

async with db.transaction() as tx:
    await tx.execute('INSERT INTO users (name) VALUES ($1)', 'Alice')
    await tx.execute('UPDATE balance SET amount = amount - 100 WHERE user_id = $1', user_id)
    # Automatically commits on success, rolls back on exception
    """,
    "metadata": {
      "type": "code_snippet",
      "language": "python",
      "tags": ["async", "database", "transactions", "context-manager"]
    }
  }
}
```

### Example 2: Complex Query

```python
# Using qdrant-find tool
{
  "tool": "qdrant-find",
  "arguments": {
    "query": "Kubernetes pod debugging CrashLoopBackOff memory limits",
    "limit": 5,
    "score_threshold": 0.7
  }
}
```

### Example 3: Store Troubleshooting Guide

```python
{
  "tool": "qdrant-store",
  "arguments": {
    "information": "Docker Multi-Stage Build Issues: If COPY fails in later stages, ensure files exist in the correct stage. Use COPY --from=builder syntax. Name your stages for clarity. Check that the source path in earlier stage matches.",
    "metadata": {
      "type": "troubleshooting",
      "category": "docker",
      "tags": ["docker", "multi-stage", "build", "debugging"]
    }
  }
}
```

---

## Phase 5: Integration with IDEs

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "qdrant-local": {
      "command": "uvx",
      "args": ["mcp-server-qdrant"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "COLLECTION_NAME": "test-collection",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

Then in Claude Desktop, you can:
- Ask: "Find information about Docker optimization"
- Say: "Store this information: [your content]"

### For Cursor/Windsurf

Add to `.cursor/mcp.json` or `.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "qdrant": {
      "command": "uvx",
      "args": ["mcp-server-qdrant"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "COLLECTION_NAME": "test-collection"
      }
    }
  }
}
```

---

## Monitoring and Verification

### Check Data in Qdrant Dashboard

1. Open http://localhost:6333/dashboard
2. Navigate to Collections → test-collection
3. View points and their metadata
4. Use the search interface to test queries

### Verify via API

```bash
# Get collection info
curl http://localhost:6333/collections/test-collection

# Count points
curl -X POST http://localhost:6333/collections/test-collection/points/count \
  -H 'Content-Type: application/json' \
  -d '{}'

# Search directly
curl -X POST http://localhost:6333/collections/test-collection/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, ...],  # 384-dimensional vector
    "limit": 5
  }'
```

---

## Troubleshooting

### Issue: MCP Server won't start
```bash
# Check Qdrant is running
docker ps | grep qdrant

# Test connection
curl http://localhost:6333/health

# Check collection exists
curl http://localhost:6333/collections/test-collection
```

### Issue: No results from queries
```bash
# Verify data is loaded
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='localhost', port=6333)
info = client.get_collection('test-collection')
print(f'Points in collection: {info.points_count}')
"

# Reload mock data if needed
python3 load_mock_data_client.py
```

### Issue: MCP tools not available
```bash
# Test MCP server directly
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | uvx mcp-server-qdrant
```

---

## Complete Test Workflow Script

Save as `test_complete_workflow.sh`:

```bash
#!/bin/bash

echo "🚀 Testing Complete Qdrant MCP Workflow"

# 1. Check Qdrant
echo "1. Checking Qdrant..."
curl -s http://localhost:6333/health > /dev/null && echo "✅ Qdrant is running" || echo "❌ Start Qdrant first"

# 2. Load mock data
echo "2. Loading mock data..."
python3 load_mock_data_client.py --skip-search

# 3. Test MCP Server
echo "3. Testing MCP Server..."
python3 mcp_client_test.py

# 4. Verify in dashboard
echo "4. Dashboard available at: http://localhost:6333/dashboard"

echo "✅ Workflow complete!"
```

---

## Next Steps

1. **Extend the mock data** - Add domain-specific content
2. **Create custom embeddings** - Use specialized models for your domain
3. **Build applications** - Create apps that use the MCP server for semantic search
4. **Implement RAG** - Use the vector store for Retrieval-Augmented Generation
5. **Set up production** - Deploy with proper authentication and scaling

---

## Quick Reference

| Component | URL/Command | Purpose |
|-----------|-------------|---------|
| Qdrant Dashboard | http://localhost:6333/dashboard | Visual interface |
| Start Qdrant | `docker-compose up -d` | Run vector database |
| Load Mock Data | `python3 load_mock_data_client.py` | Populate with test data |
| Start MCP Server | `uvx mcp-server-qdrant` | Run MCP interface |
| MCP Inspector | `npx @modelcontextprotocol/inspector uvx mcp-server-qdrant` | Test MCP tools |
| Test Client | `python3 mcp_client_test.py` | Python MCP client |