# llm-sandbox-mcp

The LLM-Sandbox MCP Server executes the provided code inside a container and writes the results to a
file. This would require to mount a project directory to the container.

## mcpServer configuration

```json
{
  "mcpServer": {
    "llm-sandbox-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount",
        "type=bind,src=/home/santosh/mcp_workdir,dst=/app",
        "santoshkal/llm-sandbox-mcp:santosh"
      ]
    }
  }
}
```

Note: Change the `--mount` path while using the MCP Server
