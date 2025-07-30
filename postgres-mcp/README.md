# PostgreSQL MCP Server

A Model Context Protocol (MCP) server that provides secure, read-only access to PostgreSQL databases. This server allows AI assistants to explore database schemas and execute read-only SQL queries.

## Features

- 🔍 **Schema Exploration**: List all tables and explore their column structures
- 🔒 **Read-Only Access**: All queries are executed within read-only transactions for safety
- 📊 **Resource System**: Tables exposed as browseable resources with schema information
- 🛡️ **Secure Design**: Connection strings never exposed through the protocol

## Available Tools

### 1. `query`
Execute read-only SQL queries against the connected PostgreSQL database.

**Parameters:**
- `sql` (string, required): The SQL query to execute

**Example:**
```json
{
  "name": "query",
  "arguments": {
    "sql": "SELECT * FROM users LIMIT 10"
  }
}
```

**Returns:** JSON array of query results

## Available Resources

The server exposes database tables as resources that can be explored:

- **Resource URI Format**: `postgres://[host]/[table_name]/schema`
- **MIME Type**: `application/json`
- **Content**: JSON array of column definitions with their data types

### Example Resource
```
postgres://localhost/users/schema
```
Returns:
```json
[
  {
    "column_name": "id",
    "data_type": "integer"
  },
  {
    "column_name": "email",
    "data_type": "character varying"
  },
  {
    "column_name": "created_at",
    "data_type": "timestamp without time zone"
  }
]
```

## Installation

### Using npm
```bash
npm install @modelcontextprotocol/server-postgres
```

### Using Docker
```bash
docker build -t postgres-mcp:latest .
docker run -it postgres-mcp:latest "postgresql://user:password@host:port/database"
```

## Configuration

### Command Line Usage
The server requires a PostgreSQL connection string as a command-line argument:

```bash
mcp-server-postgres "postgresql://user:password@localhost:5432/mydb"
```

### MCP Client Configuration

#### Claude Desktop Configuration
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "mcp-server-postgres",
      "args": ["postgresql://user:password@localhost:5432/mydb"]
    }
  }
}
```

#### Alternative with npx
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://user:password@localhost:5432/mydb"
      ]
    }
  }
}
```

#### Docker Configuration
```json
{
  "mcpServers": {
    "postgres": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network", "host",
        "postgres-mcp:latest",
        "postgresql://user:password@localhost:5432/mydb"
      ]
    }
  }
}
```

## Connection String Format

The PostgreSQL connection string should follow the standard format:

```
postgresql://[user[:password]@][host][:port][/dbname][?param1=value1&...]
```

### Examples:
- Basic: `postgresql://localhost/mydb`
- With auth: `postgresql://user:password@localhost/mydb`
- With port: `postgresql://user:password@localhost:5432/mydb`
- With SSL: `postgresql://user:password@localhost/mydb?sslmode=require`

## Usage Examples

### 1. List All Tables
First, the client can request available resources to see all tables:

```json
{
  "method": "resources/list"
}
```

Response:
```json
{
  "resources": [
    {
      "uri": "postgres://localhost/users/schema",
      "mimeType": "application/json",
      "name": "\"users\" database schema"
    },
    {
      "uri": "postgres://localhost/products/schema",
      "mimeType": "application/json",
      "name": "\"products\" database schema"
    }
  ]
}
```

### 2. Explore Table Schema
Read a specific table's schema:

```json
{
  "method": "resources/read",
  "params": {
    "uri": "postgres://localhost/users/schema"
  }
}
```

### 3. Execute Queries
Run SQL queries using the query tool:

```json
{
  "method": "tools/call",
  "params": {
    "name": "query",
    "arguments": {
      "sql": "SELECT COUNT(*) as total_users FROM users"
    }
  }
}
```

### 4. Complex Query Example
```json
{
  "method": "tools/call",
  "params": {
    "name": "query",
    "arguments": {
      "sql": "SELECT u.email, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.email ORDER BY order_count DESC LIMIT 10"
    }
  }
}
```

## Security Considerations

1. **Read-Only Transactions**: All queries are executed within read-only transactions that are automatically rolled back
2. **Connection String Security**: The database password is never exposed through the MCP protocol
3. **Query Validation**: Consider implementing additional query validation or whitelisting for production use
4. **Network Security**: Use SSL connections in production (`sslmode=require`)
5. **Access Control**: Run the MCP server with minimal database privileges

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure PostgreSQL is running and accessible
   - Check firewall settings
   - Verify the connection string format

2. **Authentication Failed**
   - Verify username and password
   - Check pg_hba.conf settings
   - Ensure user has CONNECT privilege

3. **SSL/TLS Errors**
   - Add `?sslmode=disable` for local development
   - Use `?sslmode=require` for production
   - Check SSL certificate configuration

4. **Docker Networking**
   - Use `--network host` for localhost databases
   - Or use host.docker.internal on macOS/Windows
   - Ensure database allows connections from Docker network

### Debug Mode
To see detailed logs, run with Node.js debug flags:
```bash
NODE_DEBUG=mcp mcp-server-postgres "postgresql://..."
```

## Development

### Building from Source
```bash
npm install
npm run build
```

### Running Tests
```bash
npm test
```

### TypeScript Configuration
The project uses TypeScript with the following key settings:
- Target: ES2022
- Module: Node16
- Strict mode enabled
- Source maps enabled

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.