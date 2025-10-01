# Gitingest MCP Server

Turn any Git repository into a prompt-friendly text ingest for LLMs.

## Available tool

- _ingest_gitrepo_
  - args:
    - input: <string> - Local directory path or a Github URL
    - output_file: <string> - The output path to which the ingested content will be written to.

## Starting the Server

Mount the directory that we wish to work upon and use the ingest tool on it.

```json
{
  "mcpServer": {
    "gitingest": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--mount",
        "type=bind,src=/home/santosh/genval,dst=/app/genval",
        "santoshkal/gitingest-mcp:test"
      ]
    }
  }
}
```

---
*Last updated: 2025-07-29 16:13:12 UTC*
