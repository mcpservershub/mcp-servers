# MCP Server for ChromaDB

The Chroma MCP interacts with a ChromaDB instance running locally and listning on port 8000
`docker run -v -d ./chroma-data:/data --network chromadb -p 8000:8000 chromadb/chroma`

The config for starting the Chroma MCP Server as a Docker container:

```json
{
  "mcpServers": {
    "chrmoaDB": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "chromadb",
        "santoshkal/chromamcp:main"
      ]
    }
  }
}
```

The .env used in the current implementation:

```sh

CHROMA_DOTENV_PATH="/app/.env" # Path to the .env within the container # Optional
CHROMA_CLIENT_TYPE="http" # ChromaDB Client type # Required
CHROMA_HOST="chromadb" # Docker network on which the ChromaDB instance is running #Required
CHROMA_PORT=8000 # Port of the ChromaDB instance listnining on # Required
CHROMA_SSL="false" # SSL mode if using HTTP # Required
```
