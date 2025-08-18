# Qdrant MCP Server - Local Testing Setup

## 🚀 Quick Start

Run the complete workflow test to set up everything automatically:

```bash
./test_complete_workflow.sh
```

This will:
1. Start Qdrant locally in Docker
2. Load mock data (code snippets, docs, troubleshooting guides)
3. Test the MCP Server
4. Verify everything is working

## 📋 Step-by-Step Workflow

### 1️⃣ Start Qdrant Database
```bash
docker-compose up -d
# Verify at: http://localhost:6333/dashboard
```

### 2️⃣ Load Mock Data
```bash
# Install dependencies
pip install qdrant-client sentence-transformers

# Load mock data
python3 load_mock_data_client.py
```

This loads:
- 8 code snippets (Python, JS, Go, Rust, SQL)
- 8 technical documentation entries
- 5 troubleshooting guides
- 4 architecture decision records

### 3️⃣ Start MCP Server

**For MCP Inspector (Browser UI):**
```bash
npx @modelcontextprotocol/inspector uvx mcp-server-qdrant
```
Then open http://localhost:5173

**For Direct stdio mode:**
```bash
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="test-collection" \
uvx mcp-server-qdrant
```

### 4️⃣ Use MCP Tools

The MCP Server provides two tools:

#### `qdrant-store` - Store Information
```json
{
  "tool": "qdrant-store",
  "arguments": {
    "information": "Your content here",
    "metadata": {
      "type": "documentation",
      "tags": ["tag1", "tag2"]
    }
  }
}
```

#### `qdrant-find` - Search Information
```json
{
  "tool": "qdrant-find",
  "arguments": {
    "query": "search query",
    "limit": 5
  }
}
```

### 5️⃣ Test with Python Client
```bash
python3 mcp_client_test.py
```

This will:
- Search existing mock data
- Store new information
- Verify the stored data

## 📁 File Structure

```
mcp-server-qdrant/
├── docker-compose.yml          # Qdrant container setup
├── .env                        # Environment configuration
├── requirements.txt            # Python dependencies
├── load_mock_data_client.py    # Mock data loader (uses Qdrant client)
├── mcp_client_test.py          # Python MCP client for testing
├── test_complete_workflow.sh   # Automated workflow test
├── COMPLETE_WORKFLOW.md        # Detailed step-by-step guide
└── mcp-config.json            # MCP server configuration
```

## 🧪 Example Queries to Test

After loading mock data, try these queries:

1. **Code Search:**
   - "FastAPI WebSocket authentication"
   - "React hooks for data fetching"
   - "Go middleware rate limiting"

2. **Documentation Search:**
   - "Zero downtime deployment strategies"
   - "Event-driven architecture patterns"
   - "Database connection pooling"

3. **Troubleshooting:**
   - "Kubernetes pod CrashLoopBackOff"
   - "Node.js high memory usage"
   - "Docker build optimization"

## 🔧 IDE Integration

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
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

### VS Code / Cursor
Add to `.cursor/mcp.json`:
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

## 🛠️ Troubleshooting

### Check Qdrant Status
```bash
curl http://localhost:6333/health
docker logs qdrant-local
```

### Verify Data Loaded
```bash
curl http://localhost:6333/collections/test-collection
```

### Test MCP Server
```bash
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | \
  QDRANT_URL="http://localhost:6333" \
  COLLECTION_NAME="test-collection" \
  uvx mcp-server-qdrant
```

### Clean Up
```bash
# Stop Qdrant
docker-compose down

# Remove all data
docker-compose down -v
rm -rf qdrant_storage qdrant_snapshots
```

## 📚 Additional Resources

- [Full Workflow Guide](COMPLETE_WORKFLOW.md) - Detailed instructions
- [Testing Instructions](TESTING_INSTRUCTIONS.md) - Original testing guide
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MCP Protocol Docs](https://github.com/anthropics/mcp)

## 💡 Next Steps

1. **Add Domain-Specific Data**: Modify `load_mock_data_client.py` to add your own content
2. **Use Different Models**: Change `EMBEDDING_MODEL` in `.env` for different embeddings
3. **Build Applications**: Use the MCP server in your apps for semantic search
4. **Production Setup**: Add authentication and deploy to cloud services