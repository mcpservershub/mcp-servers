# PostgreSQL MCP Server Usage Guide

This guide provides practical examples and step-by-step instructions for using the PostgreSQL MCP Server.

## Quick Start

### 1. Set Up PostgreSQL Database

First, ensure you have a PostgreSQL database running. Here's a quick Docker setup:

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name postgres-mcp-test \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:15

# Wait for database to be ready
sleep 5

# Create sample tables
docker exec -i postgres-mcp-test psql -U testuser -d testdb << 'EOF'
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES 
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com');

INSERT INTO posts (user_id, title, content, published) VALUES 
    (1, 'First Post', 'Hello World!', true),
    (1, 'Second Post', 'More content here', false),
    (2, 'Bob''s Post', 'Bob''s thoughts', true);
EOF
```

### 2. Start the MCP Server

```bash
# Using npm/npx
npx @modelcontextprotocol/server-postgres "postgresql://testuser:testpass@localhost:5432/testdb"

# Using Docker
docker run -it --network host postgres-mcp:latest "postgresql://testuser:testpass@localhost:5432/testdb"

# From source
node dist/index.js "postgresql://testuser:testpass@localhost:5432/testdb"
```

### 3. Configure Your MCP Client

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "postgres-test": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://testuser:testpass@localhost:5432/testdb"
      ]
    }
  }
}
```

## Common Use Cases

### 1. Database Exploration

**List all tables in the database:**

Ask your AI assistant: "What tables are available in the database?"

The assistant will use the resource listing to show all tables.

**Explore table structure:**

Ask: "What columns does the users table have?"

The assistant will read the schema resource for the users table.

### 2. Data Analysis Queries

**Count records:**
```sql
SELECT COUNT(*) as total_users FROM users;
```

**Join queries:**
```sql
SELECT 
    u.username,
    COUNT(p.id) as post_count,
    SUM(CASE WHEN p.published THEN 1 ELSE 0 END) as published_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.username
ORDER BY post_count DESC;
```

**Date filtering:**
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### 3. Data Quality Checks

**Find duplicates:**
```sql
SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;
```

**Check for NULL values:**
```sql
SELECT 
    COUNT(*) as total_posts,
    COUNT(title) as posts_with_title,
    COUNT(*) - COUNT(title) as posts_without_title
FROM posts;
```

### 4. Complex Analytics

**User engagement metrics:**
```sql
WITH user_stats AS (
    SELECT 
        u.id,
        u.username,
        COUNT(p.id) as total_posts,
        COUNT(p.id) FILTER (WHERE p.published) as published_posts,
        MAX(p.created_at) as last_post_date
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id, u.username
)
SELECT 
    username,
    total_posts,
    published_posts,
    ROUND(100.0 * published_posts / NULLIF(total_posts, 0), 2) as publish_rate,
    last_post_date,
    CURRENT_DATE - DATE(last_post_date) as days_since_last_post
FROM user_stats
ORDER BY total_posts DESC;
```

## Best Practices

### 1. Query Optimization

- Use LIMIT for large tables
- Add indexes on frequently queried columns
- Use EXPLAIN ANALYZE to understand query performance

### 2. Security

Create a read-only user for MCP:

```sql
-- As superuser, create read-only role
CREATE ROLE mcp_reader WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE testdb TO mcp_reader;
GRANT USAGE ON SCHEMA public TO mcp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_reader;
```

Then use this connection string:
```
postgresql://mcp_reader:secure_password@localhost:5432/testdb
```

### 3. Connection Management

For production use, consider connection pooling parameters:

```
postgresql://user:pass@host/db?pool_max=5&pool_min=1&pool_idle_timeout=30000
```

## Interaction Patterns

### 1. Conversational Queries

You can ask natural language questions, and the AI will translate them to SQL:

- "Show me all users who joined this month"
- "What's the average number of posts per user?"
- "Find users who haven't posted anything"

### 2. Iterative Analysis

Start broad and drill down:

1. "How many tables are in the database?"
2. "What does the posts table look like?"
3. "Show me the most recent 10 posts"
4. "Which users created those posts?"

### 3. Data Export

While the MCP server returns JSON, you can ask the AI to format results:

- "Show the results as a markdown table"
- "Create a CSV format of the user data"
- "Summarize the key findings"

## Troubleshooting Common Issues

### Connection Issues

**Error: Connection refused**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection with psql
psql postgresql://testuser:testpass@localhost:5432/testdb -c "SELECT 1"
```

**Error: Authentication failed**
```bash
# Verify credentials
docker exec postgres-mcp-test psql -U postgres -c "\du"
```

### Query Issues

**Error: Permission denied**
- Ensure the user has SELECT permissions
- Check schema permissions

**Error: Relation does not exist**
- Verify table name and schema
- Check case sensitivity (PostgreSQL is case-sensitive with quotes)

## Advanced Usage

### 1. JSON Data Queries

```sql
-- If you have JSONB columns
SELECT 
    id,
    data->>'name' as name,
    data->'settings'->>'theme' as theme
FROM user_profiles
WHERE data->>'active' = 'true';
```

### 2. Window Functions

```sql
-- Rank users by post count
SELECT 
    username,
    post_count,
    RANK() OVER (ORDER BY post_count DESC) as rank,
    LAG(post_count) OVER (ORDER BY post_count DESC) as previous_user_count
FROM (
    SELECT u.username, COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.username
) user_post_counts;
```

### 3. CTEs for Complex Analysis

```sql
WITH RECURSIVE user_hierarchy AS (
    -- Base case
    SELECT id, username, manager_id, 1 as level
    FROM users
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case
    SELECT u.id, u.username, u.manager_id, uh.level + 1
    FROM users u
    JOIN user_hierarchy uh ON u.manager_id = uh.id
)
SELECT * FROM user_hierarchy ORDER BY level, username;
```

## Integration Examples

### Python Script Using MCP

```python
import subprocess
import json

def query_via_mcp(sql_query):
    # Start MCP server process
    process = subprocess.Popen(
        ['mcp-server-postgres', 'postgresql://localhost/testdb'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    # Send query request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "query",
            "arguments": {"sql": sql_query}
        },
        "id": 1
    }
    
    process.stdin.write(json.dumps(request) + '\n')
    process.stdin.flush()
    
    # Read response
    response = json.loads(process.stdout.readline())
    return response

# Example usage
result = query_via_mcp("SELECT COUNT(*) FROM users")
print(result)
```

## Monitoring and Logging

Enable query logging for debugging:

```sql
-- In PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- View logs
docker logs postgres-mcp-test
```

## Next Steps

1. Set up automated backups before running queries
2. Create views for commonly used queries
3. Implement row-level security if needed
4. Consider using read replicas for analytics