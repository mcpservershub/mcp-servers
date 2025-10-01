# SonarQube MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with SonarQube/SonarCloud APIs. This server enables AI assistants to analyze code quality metrics, security issues, hotspots, and duplications from SonarQube projects.

## Overview

The SonarQube MCP server is written in Go and provides tools to:
- List and search SonarQube projects
- Retrieve code issues with various filters
- Analyze security hotspots
- Check for code duplications
- Fetch project metrics and measures

## Prerequisites

- Docker installed on your system
- Access to a SonarQube instance (self-hosted or SonarCloud)
- SonarQube API token (for authentication if required)
- MCP-compatible client (e.g., Claude Desktop, Cline)

## Available Tools

### 1. `sonar_projects`
Lists all SonarQube projects for a given organization.

**Parameters:**
- `organization` (required): The SonarCloud organization name (e.g., "my_organization")

**Returns:** List of projects with details including key, name, visibility, and last analysis date

### 2. `sonar_issues`
Searches and retrieves all issues for a specified SonarQube project.

**Parameters:**
- `projectKey` (required): Key of the project (e.g., "my_project")
- `organization` (optional): The SonarCloud organization key or name
- `branch` (optional): The SCM branch key or name (default: "main")
- `impactSeverities` (optional): Array of severities - BLOCKER, HIGH, MEDIUM, LOW, INFO (default: ["BLOCKER", "HIGH"])
- `issueStatus` (optional): Array of statuses - OPEN, CONFIRMED, FALSE_POSITIVE, ACCEPTED, FIXED (default: ["OPEN"])
- `resolved` (optional): Filter by resolved status - "true", "false", "yes", "no"

**Returns:** List of issues with full details including severity, message, location, and impacts

### 3. `sonar_hotspots`
Searches and retrieves security hotspots in source files of a specified project.

**Parameters:**
- `projectKey` (required): Key of the project (e.g., "my_project")
- `files` (optional): Array of file paths to filter
- `status` (optional): Hotspot status filter
- `branch` (optional): The SCM branch key or name

**Returns:** List of security hotspots with vulnerability probability and status

### 4. `sonar_duplications`
Shows code duplications between source files within a branch, pull request, or specific file.

**Parameters:**
- `branch` (optional): The SCM branch key or name (default: "main")
- `key` (optional): The file key (e.g., "my_project:/src/foo/Bar.php")
- `pullRequest` (optional): The pull request key (e.g., "5461")

**Returns:** Duplication blocks showing duplicated code locations

### 5. `sonar_measures`
Fetches measures for specified metrics from SonarQube scan results.

**Parameters:**
- `projectKey` (required): Project identification key (e.g., "my_project")
- `outputFile` (required): Output path to store the fetched measures JSON file
- `metricKeys` (required): Array of metric keys (e.g., ["complexity", "violations", "security"])

**Returns:** Project metrics and measures in JSON format

## Configuration

### Docker Configuration

To use the SonarQube MCP server with Docker, add the following configuration to your MCP client's settings:

```json
{
  "mcpServers": {
    "sonarqube": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env=SONARQUBE_URL=https://sonarcloud.io/",
        "--env=SONARQUBE_TOKEN=your-token-here",
        "santoshkal/sonarqube-mcp"
      ]
    }
  }
}
```

### Environment Variables

The server supports the following environment variables:

- `SONARQUBE_URL`: The URL of your SonarQube instance (default: "http://localhost:9000/")
- `SONARQUBE_TOKEN`: Authentication token for SonarQube API (if required)
- `PORT`: Port for SSE transport mode (default: "2222")
- `BASE_URL`: Base URL for SSE transport mode (default: "http://localhost:2222")

### Transport Modes

The server supports two transport modes:

1. **stdio** (default): Standard input/output communication
2. **sse**: Server-Sent Events for HTTP-based communication

To use SSE mode:

```json
{
  "mcpServers": {
    "sonarqube": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-p", "2222:2222",
        "--env=SONARQUBE_URL=https://sonarcloud.io/",
        "--env=SONARQUBE_TOKEN=your-token-here",
        "santoshkal/sonarqube-mcp",
        "-t", "sse"
      ]
    }
  }
}
```

## Usage Examples

### List Projects in Organization

```
Tool: sonar_projects
Arguments:
{
  "organization": "my-org"
}
```

### Get Critical Issues for a Project

```
Tool: sonar_issues
Arguments:
{
  "projectKey": "my-project",
  "organization": "my-org",
  "branch": "main",
  "impactSeverities": ["BLOCKER", "HIGH"],
  "issueStatus": ["OPEN", "CONFIRMED"]
}
```

### Check Security Hotspots

```
Tool: sonar_hotspots
Arguments:
{
  "projectKey": "my-project",
  "branch": "develop"
}
```

### Analyze Code Duplications

```
Tool: sonar_duplications
Arguments:
{
  "key": "my-project:/src/main/java/com/example/Service.java",
  "branch": "main"
}
```

### Fetch Project Metrics

```
Tool: sonar_measures
Arguments:
{
  "projectKey": "my-project",
  "outputFile": "/tmp/sonar-metrics.json",
  "metricKeys": ["complexity", "coverage", "violations", "code_smells", "bugs", "vulnerabilities"]
}
```

## Building the Docker Image

If you want to build the image yourself:

```bash
cd sonarqube-mcp
docker build -t sonarqube-mcp .
```

## Development

### Local Development

1. Clone the repository
2. Install Go 1.21 or later
3. Run the server locally:

```bash
go run main.go -t stdio
```

### Building from Source

```bash
go build -o sonarqube-mcp-server main.go
./sonarqube-mcp-server -t stdio
```

## Troubleshooting

### Common Issues

1. **"Unable to retrieve sonar projects" error**
   - Verify your SONARQUBE_URL is correct
   - Check if you need authentication (SONARQUBE_TOKEN)
   - Ensure network connectivity to SonarQube instance

2. **"Missing organization parameter" error**
   - Some operations require organization parameter for SonarCloud
   - For self-hosted SonarQube, this may not be required

3. **Connection timeouts**
   - Check firewall rules
   - Verify Docker container can reach SonarQube instance
   - Consider increasing timeout values

### API Endpoints

The server connects to the following SonarQube API endpoints:
- `/api/projects/search` - List projects
- `/api/issues/search` - Search issues
- `/api/hotspots/search` - Search security hotspots
- `/api/duplications/show` - Show duplications
- `/api/measures/component` - Get project measures

## Security Considerations

- Store SonarQube tokens securely
- Use read-only tokens when possible
- Consider network isolation for sensitive projects
- The server only performs read operations on SonarQube

## License

This MCP server is provided as-is for integration with SonarQube/SonarCloud services.