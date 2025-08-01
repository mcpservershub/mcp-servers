# Neo4j-Memory MCP Server


Use the MCP Config as following:
```json
{
  "mcpServers": {
    "neo4j-memory": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "neo4j",
        "-e",
        "NEO4J_URL=bolt://neo4j-memory;7867",
        "-e",
        "NEO4J_USERNAME=neo4j",
        "-e",
        "NEO4J_PASSWORD=iamtesting",
        "mcp/neo4j-memory:0.1.4"
      ]
    }
  }
}
```
 
 ## Note:
- The `NEO4J_URL` Env, this should point to the Container name of the Neo4j instance running on
another container.
- Bothe the Neo4j instance and the MCP Server container should share the same network. Attach both
the container to the same network with `--network` flag while starting the containers.



**** 


---
*Last updated: 2025-07-29 16:13:12 UTC*
