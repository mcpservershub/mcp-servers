# Qdrant MCP Server - Local Testing Instructions

## Prerequisites

1. Docker and Docker Compose installed
2. Python 3.10+ with `uv` package manager
3. Claude Code, Cursor, or VS Code with MCP support

## Step 1: Start Qdrant Vector Database

```bash
# Navigate to the project directory
cd /home/santosh/compare/mcp-server-qdrant

# Start Qdrant container
docker-compose up -d

# Verify Qdrant is running
curl http://localhost:6333/health
```

The Qdrant dashboard will be available at: http://localhost:6333/dashboard

## Step 2: Install MCP Server Dependencies

```bash
# Install uv if not already installed
pip install uv

# Install the MCP server package
uv pip install mcp-server-qdrant

# Or install from the local directory
cd /home/santosh/compare/mcp-server-qdrant
uv pip install -e .
```

## Step 3: Start the MCP Server

### Option A: Using environment variables
```bash
source .env
uvx mcp-server-qdrant
```

### Option B: Direct command with variables
```bash
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="test-collection" \
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2" \
uvx mcp-server-qdrant
```

### Option C: Using the HTTP server mode
```bash
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="test-collection" \
FASTMCP_PORT=8000 \
uvx mcp-server-qdrant
```

## Step 4: Configure Your IDE

### For Claude Code

Add to your `claude.json` configuration:

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

### For Cursor/Windsurf

Add to your `.cursor/mcp.json` or `.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "qdrant-local": {
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

## Step 5: Test the MCP Server

### Test 1: Store Information

Use the `qdrant-store` tool to store some information:

```
Store this information: "The Qdrant MCP Server allows semantic storage and retrieval of code snippets and documentation. It uses vector embeddings to find similar content."
```

### Test 2: Retrieve Information

Use the `qdrant-find` tool to search:

```
Find information about: "semantic storage"
```

### Test 3: Store Code Snippets

```
Store this code snippet: 
def calculate_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    import numpy as np
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
```

### Test 4: Search Code

```
Find code related to: "cosine similarity calculation"
```

## Step 6: Verify in Qdrant Dashboard

1. Open http://localhost:6333/dashboard
2. Navigate to Collections
3. You should see "test-collection"
4. Click on it to view stored vectors and metadata

## Testing with Python Script

Run the provided test script:

```bash
python test_qdrant_mcp.py
```

## Troubleshooting

### Issue: Connection Refused
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check logs
docker-compose logs qdrant
```

### Issue: Collection Not Found
```bash
# Create collection manually
curl -X PUT http://localhost:6333/collections/test-collection \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'
```

### Issue: Embedding Model Not Loading
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

## Advanced Testing

### Test Different Embedding Models

1. Update `.env` file:
```env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
VECTOR_SIZE=768
```

2. Restart MCP server
3. Create new collection with appropriate vector size

### Test with Multiple Collections

```bash
# Collection for code
COLLECTION_NAME="code-snippets" uvx mcp-server-qdrant

# Collection for documentation
COLLECTION_NAME="documentation" uvx mcp-server-qdrant
```

### Performance Testing

Use the bulk insert test in `test_qdrant_mcp.py` to test with larger datasets.

## Cleanup

```bash
# Stop Qdrant
docker-compose down

# Remove volumes (WARNING: This deletes all stored data)
docker-compose down -v

# Clean up storage directories
rm -rf qdrant_storage qdrant_snapshots
```

## Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MCP Protocol Specification](https://github.com/anthropics/mcp)
- [Sentence Transformers Models](https://www.sbert.net/docs/pretrained_models.html)