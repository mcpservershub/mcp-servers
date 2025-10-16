# Testing MCP Servers with Coding Agents

## Overview

This comprehensive guide covers configuring Model Context Protocol (MCP) servers with Claude Code CLI and other AI agents. MCP servers extend AI agent capabilities by providing specialized tools for code analysis, database queries, file operations, and more.

## ⚠️ IMPORTANT: Session Restart Required

**After configuring MCP servers, you MUST restart your Claude Code CLI session for the changes to take effect:**

1. **Exit current session**: Press `Ctrl+C` or type `exit`
2. **Restart Claude Code**: Run `claude` again in the same directory
3. **Verify connections**: Use `claude mcp list` to confirm servers are connected
4. **Test functionality**: Try the sample prompts provided in this guide

**Why restart is required:**
- MCP server discovery happens during Claude Code initialization
- Configuration changes are only loaded at session startup
- Tool registration requires a fresh protocol handshake
- Cached connection states need to be cleared

**Best Practice**: Always restart Claude Code after:
- Adding/removing MCP servers
- Modifying `.mcp.json` configuration
- Changing server parameters or environment variables
- Updating MCP server images or executables

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Understanding MCP Configuration Scopes](#understanding-mcp-configuration-scopes)
3. [MCP Server Configuration Methods](#mcp-server-configuration-methods)
4. [Local Scope Configuration](#local-scope-configuration)
5. [Project Scope Configuration](#project-scope-configuration)
6. [User Scope Configuration](#user-scope-configuration)
7. [Example Configurations](#example-configurations)
8. [Verifying MCP Server Configuration](#verifying-mcp-server-configuration)
9. [Using MCP Servers with AI Agents](#using-mcp-servers-with-ai-agents)
10. [Sample Test Prompts](#sample-test-prompts)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

## Prerequisites

- Claude Code CLI installed and authenticated
- Docker installed (for containerized MCP servers)
- Basic understanding of JSON configuration files
- Access to MCP server images or executables

## Understanding MCP Configuration Scopes

MCP servers can be configured at three different scopes:

### Local Scope
- **Location**: Stored in Claude Code's local configuration for the current project
- **Visibility**: Only available in the current project directory
- **Use Case**: Project-specific tools that shouldn't be available globally
- **Sharing**: Not shared with team members

### Project Scope
- **Location**: Stored in `.mcp.json` file in project root
- **Visibility**: Available to anyone working in the project directory
- **Use Case**: Team-shared project-specific tools
- **Sharing**: Committed to version control, shared with team

### User Scope
- **Location**: Stored in user's global Claude Code configuration
- **Visibility**: Available across all projects for the user
- **Use Case**: Personal productivity tools used across projects
- **Sharing**: Personal to the user, not shared

## MCP Server Configuration Methods

### Method 1: Command Line Configuration

#### Local Scope
```bash
claude mcp add --scope local <server-name> [options] -- <command> [args...]
```

#### User Scope
```bash
claude mcp add --scope user <server-name> [options] -- <command> [args...]
```

#### Project Scope (via .mcp.json)
Create or edit `.mcp.json` in project root directory.

### Method 2: JSON Configuration Files

Project scope configuration uses `.mcp.json` files with specific format requirements.

## Local Scope Configuration

### Adding Local Scope MCP Servers

```bash
# Example: Add a local filesystem MCP server
claude mcp add --scope local filesystem -- npx @modelcontextprotocol/server-filesystem /path/to/allowed/directory

# Example: Add a local Docker-based server
claude mcp add --scope local multilspy-server -- docker run --rm -i --volume /workspace:/workspace multilspy-mcp-server:latest

# Example: Add with environment variables
claude mcp add --scope local postgres-server --env DATABASE_URL=postgresql://user:pass@localhost/db -- npx @modelcontextprotocol/server-postgres
```

### Viewing Local Configuration

```bash
claude mcp list
claude mcp get <server-name>
```

### Removing Local Servers

```bash
claude mcp remove --scope local <server-name>
```

## Project Scope Configuration

### Creating .mcp.json

Project scope configuration requires a `.mcp.json` file in the project root:

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio|sse|http",
      "command": "executable-path",
      "args": ["optional", "arguments"],
      "env": {
        "OPTIONAL_ENV_VAR": "value"
      }
    }
  }
}
```

### Required Fields

- **`type`**: Transport protocol (`"stdio"`, `"sse"`, or `"http"`)
- **`command`**: Executable command or path
- **`args`**: Array of command-line arguments (optional)
- **`env`**: Environment variables object (optional)

### Transport Types

#### stdio (Standard Input/Output)
- Most common for local processes and Docker containers
- Direct process communication
- Suitable for: Local executables, Docker containers, Node.js scripts

#### sse (Server-Sent Events)
- For remote HTTP-based servers with streaming
- Real-time bidirectional communication
- Suitable for: Remote services, web-based MCP servers

#### http (HTTP Request/Response)
- Traditional HTTP request/response pattern
- Simpler than SSE but less real-time
- Suitable for: REST-like MCP services

## User Scope Configuration

### Adding User Scope Servers

```bash
# Add a server available across all projects
claude mcp add --scope user github-server --env GITHUB_TOKEN=${GITHUB_TOKEN} -- npx @modelcontextprotocol/server-github

# Add a personal productivity server
claude mcp add --scope user notes-server -- npx @modelcontextprotocol/server-filesystem ${HOME}/notes
```

### Viewing User Configuration

```bash
claude mcp list --scope user
```

## Example Configurations

### Example 1: Language Server Protocol (LSP) Integration

**Scenario**: COBOL development with SuperBOL LSP server

#### Local Scope (Command Line)
```bash
claude mcp add --scope local multilspy-cobol -- docker run --rm -i --volume "$(pwd):/workspace" multilspy-mcp-server:superbol-official
```

#### Project Scope (.mcp.json)
```json
{
  "mcpServers": {
    "multilspy-cobol": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--volume",
        "${PWD}:/workspace",
        "multilspy-mcp-server:superbol-official"
      ],
      "env": {}
    }
  }
}
```

### Example 2: Code Indexing with CTags

**Scenario**: Universal CTags for symbol indexing

#### Local Scope (Command Line)
```bash
claude mcp add --scope local ctags-indexer -- docker run --rm -i --volume "$(pwd):/workspace" ctags-mcp:latest
```

#### Project Scope (.mcp.json)
```json
{
  "mcpServers": {
    "ctags-indexer": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--volume",
        "${PWD}:/workspace",
        "ctags-mcp:latest"
      ],
      "env": {}
    }
  }
}
```

### Example 3: Database Integration

**Scenario**: PostgreSQL database access

#### User Scope (Command Line)
```bash
claude mcp add --scope user postgres-db --env DATABASE_URL=postgresql://user:password@localhost:5432/mydb -- npx @modelcontextprotocol/server-postgres
```

#### Project Scope (.mcp.json)
```json
{
  "mcpServers": {
    "project-database": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-postgres"
      ],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Example 4: Filesystem Access

**Scenario**: Restricted filesystem access for document processing

#### Local Scope (.mcp.json)
```json
{
  "mcpServers": {
    "document-fs": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "${PWD}/documents",
        "${PWD}/output"
      ],
      "env": {}
    }
  }
}
```

### Example 5: Web Services Integration

**Scenario**: GitHub API integration

#### User Scope (.mcp.json)
```json
{
  "mcpServers": {
    "github-api": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Example 6: Remote HTTP Server

**Scenario**: Remote MCP server via HTTP

```json
{
  "mcpServers": {
    "remote-analyzer": {
      "type": "http",
      "url": "https://mcp-server.example.com/api",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}",
        "Content-Type": "application/json"
      },
      "env": {}
    }
  }
}
```

### Example 7: Multiple Servers Configuration

**Scenario**: Complete development environment

```json
{
  "mcpServers": {
    "lsp-server": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--volume", "${PWD}:/workspace",
        "multilspy-mcp-server:latest"
      ],
      "env": {}
    },
    "ctags-indexer": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--volume", "${PWD}:/workspace",
        "ctags-mcp:latest"
      ],
      "env": {}
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "${PWD}"
      ],
      "env": {}
    },
    "git-integration": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-git",
        "--repository=${PWD}"
      ],
      "env": {}
    }
  }
}
```

## Verifying MCP Server Configuration

### Check Server Status
```bash
# List all configured servers
claude mcp list

# Get detailed info about a specific server
claude mcp get <server-name>

# Check server health
claude mcp list --verbose
```

### Test Server Connectivity
```bash
# Test with explicit configuration
claude --mcp-config .mcp.json --print "Hello" --timeout 10

# Test specific server tools
claude --debug mcp --print "List available tools from MCP servers"
```

### Validate Configuration File
```bash
# Validate JSON syntax
python3 -m json.tool .mcp.json

# Check for common issues
claude mcp validate-config .mcp.json
```

## Using MCP Servers with AI Agents

### Claude Code CLI Integration

#### Direct Tool Access
Once configured, MCP server tools become available in Claude Code sessions:

```bash
# Start Claude Code in project directory
claude

# Tools are automatically discovered and available
# Use prompts that reference MCP server capabilities
```

#### Example Usage Prompts

**For LSP Servers:**
```
"Use the multilspy-cobol server to find all references to CUSTOMER-RECORD in my COBOL files"

"Get code completion suggestions for the WORKING-STORAGE section using the LSP server"

"Navigate to the definition of UPDATE-CUSTOMER-INFO using multilspy-cobol"
```

**For CTags Servers:**
```
"Use ctags-indexer to generate tags for all source files in the workspace"

"Find all COBOL paragraphs containing 'DISPLAY' using the CTags server"

"Create a symbol outline for CUSTOMER.COB using ctags-indexer"
```

**For Database Servers:**
```
"Query the customer table using the postgres-db server to show recent orders"

"Use the database server to analyze the schema and suggest optimizations"
```

### MCP Tool Discovery

MCP server tools are automatically discovered through the MCP protocol handshake:

1. **Initialization**: Client sends `initialize` request
2. **Capabilities**: Server responds with supported capabilities
3. **Notification**: Client sends `notifications/initialized`
4. **Tool Discovery**: Client queries `tools/list` to get available tools
5. **Integration**: Tools become available in AI agent sessions

### Tool Naming Convention

MCP tools follow the pattern: `mcp__<server-name>__<tool-name>`

Example:
- `mcp__multilspy-cobol__code_navigate_definition`
- `mcp__ctags-indexer__find_symbol`
- `mcp__postgres-db__query_database`

## Sample Test Prompts

After configuring your MCP servers and restarting Claude Code, use these test prompts to verify functionality and explore capabilities.

### Basic Connectivity Testing

#### Test All MCP Servers
```
"List all available MCP servers and show me their current connection status"

"Show me all the tools available from each configured MCP server"

"Test the connectivity to all MCP servers and report any connection issues"
```

### Language Server Protocol (LSP) MCP Servers

#### multilspy-mcp-server / SuperBOL COBOL

**Basic Functionality Tests:**
```
"Use the multilspy LSP server to analyze all COBOL files in the workspace and show me the available symbols"

"Get document symbols from CUSTOMER.COB using the LSP server"

"Show me the program structure of INVENTORY.COB using multilspy server tools"
```

**Code Navigation Tests:**
```
"Use multilspy server to navigate to the definition of CUSTOMER-RECORD in my COBOL files"

"Find all references to UPDATE-CUSTOMER-INFO using the LSP server"

"Show me hover information for CUSTOMER-ID field using multilspy tools"
```

**Code Completion Tests:**
```
"Get code completion suggestions for line 25, column 10 in CUSTOMER.COB using the LSP server"

"Use multilspy server to provide completion suggestions in the WORKING-STORAGE SECTION"
```

**Workspace Analysis:**
```
"Use the multilspy server to search for all COBOL paragraphs containing 'DISPLAY' across the entire workspace"

"Analyze all COBOL files using multilspy and create a comprehensive symbol report"
```

#### Generic LSP Server Tests

**For Python Projects:**
```
"Use the Python LSP server to find the definition of the 'process_data' function"

"Get code completion suggestions for the Flask app import statements using LSP"

"Use LSP server to find all references to the 'DatabaseConnection' class"
```

**For JavaScript/TypeScript Projects:**
```
"Use the TypeScript LSP server to analyze the main.ts file and show all exported functions"

"Find all references to the 'handleUserClick' function using the LSP server"

"Get type information for the 'userConfig' variable using TypeScript LSP tools"
```

### CTags MCP Servers

#### ctags-mcp / Universal CTags

**Tag Generation Tests:**
```
"Use the ctags server to generate a comprehensive tags file for all source code in the workspace"

"Generate ctags index specifically for COBOL files, excluding test files"

"Create tags for the entire project with recursive directory scanning using ctags server"
```

**Symbol Search Tests:**
```
"Use ctags server to find all symbols named 'CUSTOMER' with partial matching"

"Search for all function definitions using the ctags server"

"Find all COBOL paragraph definitions containing 'UPDATE' using ctags"
```

**Code Navigation Tests:**
```
"Use ctags server to go to the definition of 'MAIN-PROGRAM' paragraph"

"Find all references to 'WS-CUSTOMER-RECORD' using the ctags server"

"Show me the file outline for UTILITIES.COB using ctags server tools"
```

**Symbol Analysis:**
```
"List all symbols defined in CUSTOMER.COB using the ctags server, grouped by kind"

"Use ctags to create a hierarchical outline of symbols in the entire project"

"Validate the tags file and check for any missing or invalid entries using ctags server"
```

### Database MCP Servers

#### PostgreSQL MCP Server

**Connection and Schema Tests:**
```
"Use the postgres server to show me all tables in the database"

"Query the database schema and show me the structure of the 'users' table"

"Use postgres MCP server to check the database connection status"
```

**Data Query Tests:**
```
"Query the customers table using postgres server and show the first 10 records"

"Use the database server to find all orders from the last 30 days"

"Execute a complex JOIN query using postgres server to show customer order history"
```

**Analytics Tests:**
```
"Use postgres server to analyze table sizes and suggest optimization opportunities"

"Query database statistics using the postgres MCP server and identify slow queries"

"Generate a data quality report using database server tools"
```

#### SQLite MCP Server

**File Database Tests:**
```
"Use sqlite server to analyze the local database file and show all tables"

"Query the sqlite database to show recent application logs"

"Use sqlite MCP server to backup and validate the database file"
```

### Filesystem MCP Servers

#### Basic Filesystem Server

**File Operations:**
```
"Use the filesystem server to list all files in the project directory"

"Search for files containing 'TODO' comments using the filesystem server"

"Use filesystem tools to analyze disk usage and identify large files"
```

**Directory Analysis:**
```
"Use the filesystem server to create a directory tree structure of the project"

"Find all configuration files (.json, .yaml, .conf) using filesystem server"

"Analyze file modifications in the last week using filesystem tools"
```

### Git MCP Servers

#### Git Integration Server

**Repository Analysis:**
```
"Use the git server to show me the current branch status and recent commits"

"Analyze the git history using MCP tools and show contributors statistics"

"Use git server to identify files with the most frequent changes"
```

**Change Analysis:**
```
"Show me uncommitted changes using the git MCP server"

"Use git tools to analyze the diff between current branch and main"

"Generate a release notes summary using git server tools"
```

### Web Services MCP Servers

#### GitHub API Server

**Repository Management:**
```
"Use the GitHub server to show me all open issues in the repository"

"List recent pull requests using GitHub MCP tools"

"Use GitHub server to analyze repository statistics and contributor activity"
```

**Issue Tracking:**
```
"Create a new GitHub issue using the MCP server with title 'Bug in customer module'"

"Use GitHub tools to search for issues tagged with 'bug' label"

"Generate a project status report using GitHub server data"
```

### Multi-Server Integration Tests

#### Combined Analysis
```
"Use both LSP and ctags servers to provide a comprehensive analysis of the COBOL codebase"

"Combine filesystem and git servers to identify recently modified source files and analyze their changes"

"Use database and git servers together to correlate code changes with database schema modifications"
```

#### Workflow Tests
```
"Use LSP server to find a function definition, then use git server to show its modification history"

"Combine ctags indexing with filesystem analysis to create a complete project documentation"

"Use database server to identify data issues, then use git server to find related code changes"
```

### Error Testing and Diagnostics

#### Connectivity Tests
```
"Test all MCP servers and report which ones are responding correctly"

"Use each configured MCP server to perform a simple operation and verify functionality"

"Diagnose any MCP server connection issues and suggest solutions"
```

#### Performance Tests
```
"Benchmark the response time of each MCP server with a simple query"

"Test concurrent access to multiple MCP servers and report performance"

"Use MCP servers to process large datasets and monitor resource usage"
```

### Advanced Integration Scenarios

#### Development Workflow
```
"Create a development workflow that uses LSP for code analysis, ctags for navigation, and git for version control"

"Set up a code review process using GitHub MCP server and LSP tools for static analysis"

"Design a CI/CD pipeline integration using multiple MCP servers for testing and deployment"
```

#### Documentation Generation
```
"Use LSP and ctags servers to automatically generate API documentation for the project"

"Create a code architecture diagram using multiple MCP server data sources"

"Generate a comprehensive project report combining data from all configured MCP servers"
```

### Troubleshooting Test Prompts

#### Diagnostic Commands
```
"Show me the detailed status of all MCP servers including connection health"

"Test each MCP server individually and report any configuration issues"

"Verify that all required MCP server tools are properly exposed and accessible"
```

#### Configuration Validation
```
"Validate the current MCP server configuration and suggest improvements"

"Check for conflicts between multiple MCP servers and recommend resolutions"

"Test environment variable expansion in MCP server configurations"
```

## Usage Tips for Test Prompts

### Getting Started
1. **Start Simple**: Begin with basic connectivity tests before complex operations
2. **Test Individually**: Test each MCP server separately before combining them
3. **Verify Outputs**: Check that server responses match expected formats
4. **Error Handling**: Test error scenarios to ensure robust configurations

### Progressive Testing
1. **Basic → Advanced**: Move from simple queries to complex operations
2. **Single → Multiple**: Test individual servers before multi-server scenarios
3. **Read → Write**: Start with read-only operations before write operations
4. **Local → Remote**: Test local servers before remote/network-dependent servers

### Best Practices for Testing
- **Document Results**: Keep track of which prompts work with your specific setup
- **Modify for Context**: Adapt prompts to match your actual file/data structure
- **Test Edge Cases**: Try prompts with non-existent files or invalid parameters
- **Performance Monitoring**: Note response times for different types of operations

## Troubleshooting

### Common Issues

#### 1. Server Not Connecting

**Symptoms:**
- Server shows as "Disconnected" in `claude mcp list`
- Error messages about connection failures

**Solutions:**
```bash
# Check if command is valid
docker run --rm multilspy-mcp-server:latest --help

# Verify paths and permissions
ls -la /path/to/workspace

# Test manual connection
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run --rm -i multilspy-mcp-server:latest
```

#### 2. Missing Transport Type

**Error:** Configuration validation fails

**Solution:** Add `"type": "stdio"` to `.mcp.json`:
```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",  // ← Required field
      "command": "docker",
      // ...
    }
  }
}
```

#### 3. Environment Variables Not Expanded

**Error:** Variables like `${PWD}` not substituted

**Solutions:**
```bash
# Use absolute paths instead
"--volume", "/full/path/to/workspace:/workspace"

# Or use proper environment variables
"--volume", "${HOME}/project:/workspace"
```

#### 4. Tools Not Available in Session

**Symptoms:**
- Server connects but tools don't appear
- No MCP tool functions available

**Debugging:**
```bash
# Enable MCP debugging
claude --debug mcp --print "Test MCP integration"

# Check tool discovery manually
python3 mcp_bridge.py <server-name> list-tools
```

#### 5. Docker Volume Mount Issues

**Error:** Permission denied or path not found

**Solutions:**
```bash
# Use absolute paths
"--volume", "/home/user/project:/workspace"

# Fix permissions
chmod -R 755 /path/to/project

# Check Docker access
docker run --rm -v "$(pwd):/test" alpine ls -la /test
```

### Debug Commands

```bash
# Comprehensive debug information
claude --debug mcp mcp list

# Test specific configuration
claude --mcp-config .mcp.json --debug mcp --print "debug test"

# Manual MCP protocol testing
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test","version":"1.0"}}}' | <your-server-command>
```

## Best Practices

### Security

1. **Verify Third-Party Servers**: Only use trusted MCP servers
2. **Limit File System Access**: Restrict filesystem servers to necessary directories
3. **Environment Variables**: Use environment variables for sensitive data
4. **Regular Updates**: Keep MCP servers updated

### Configuration Management

1. **Version Control**: Commit `.mcp.json` to share with team
2. **Documentation**: Document server purposes and requirements
3. **Environment Specific**: Use different configs for dev/prod environments
4. **Backup**: Keep backups of working configurations

### Performance

1. **Resource Limits**: Set appropriate Docker resource limits
2. **Concurrent Servers**: Limit number of simultaneous servers
3. **Cleanup**: Remove unused server configurations
4. **Monitoring**: Monitor server resource usage

### Development Workflow

1. **Local Development**: Use local scope for experimental servers
2. **Team Sharing**: Use project scope for team-shared tools
3. **Personal Tools**: Use user scope for personal productivity tools
4. **Testing**: Test configurations in isolated environments

### Example Development Setup

```json
{
  "mcpServers": {
    // Core development tools (shared with team)
    "lsp-server": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "--volume", "${PWD}:/workspace", "project-lsp:latest"],
      "env": {}
    },

    // Code indexing (shared with team)
    "indexer": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "--volume", "${PWD}:/workspace", "ctags-mcp:latest"],
      "env": {}
    },

    // Project database (environment specific)
    "database": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL:-postgresql://localhost/devdb}"
      }
    }
  }
}
```

This configuration provides a complete development environment with language server support, code indexing, and database access, while following best practices for security and team collaboration.
