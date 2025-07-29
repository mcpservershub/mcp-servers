# Renovate MCP Server

An MCP (Model Context Protocol) server for managing automated dependency updates using Renovate CLI.

## Features

This MCP server provides the following tools:

1. **run_renovate** - Execute Renovate on specified repositories (supports local platform)
2. **run_renovate_local** - Run Renovate on local filesystem (for testing configurations)
3. **check_config** - Validate Renovate configuration files
4. **get_dependency_updates** - List available dependency updates (supports local platform)
5. **create_onboarding_pr** - Create initial Renovate configuration PR
6. **get_renovate_logs** - Retrieve Renovate execution logs
7. **manage_dashboard** - View/manage dependency dashboard
8. **schedule_run** - Schedule or trigger Renovate runs
9. **validate_credentials** - Test authentication and permissions

## Prerequisites

- Python 3.12+
- Node.js and npm (for Renovate CLI)
- Renovate CLI (`npm install -g renovate`)
- A GitHub/GitLab/Bitbucket personal access token

## Installation

### Option 1: Local Installation

1. Clone this repository:
```bash
cd renovate-mcp-server
```

2. Create a virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Install Renovate CLI globally:
```bash
npm install -g renovate
```

### Option 2: Docker Installation

1. Build the Docker image:
```bash
docker build -t renovate-mcp-server:latest .
```

2. Run with Docker:
```bash
docker run -it -e RENOVATE_TOKEN=your-token renovate-mcp-server:latest
```

See [README.Docker.md](README.Docker.md) for detailed Docker usage instructions.

## Configuration

### Authentication

Set your repository platform token as an environment variable:

```bash
export RENOVATE_TOKEN="your-github-token-here"
```

### MCP Client Configuration

Add the server to your MCP client configuration:

```json
{
  "servers": {
    "renovate": {
      "command": "python",
      "args": ["-m", "renovate_mcp.server"],
      "env": {
        "RENOVATE_TOKEN": "your-token-here"
      }
    }
  }
}
```

Or if installed via pip:

```json
{
  "servers": {
    "renovate": {
      "command": "renovate-mcp",
      "env": {
        "RENOVATE_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Usage Examples

### Running Renovate on a Repository

```python
# Basic run
result = await run_renovate(
    repositories=["owner/repo"],
    platform="github"
)

# Dry run mode
result = await run_renovate(
    repositories=["owner/repo"],
    platform="github",
    dry_run=True
)

# Autodiscover repositories
result = await run_renovate(
    repositories=["owner/*"],
    platform="github",
    autodiscover=True
)
```

### Running Renovate on Local Filesystem

```python
# Using run_renovate_local (dedicated tool)
result = await run_renovate_local(
    directory=".",
    dry_run_mode="lookup"
)

# Using run_renovate with local platform
result = await run_renovate(
    repositories=["/path/to/project"],
    platform="local",
    dry_run=True
)

# Using get_dependency_updates with local platform
updates = await get_dependency_updates(
    repository="/home/user/my-node-project",
    platform="local"
)

# Test with specific config file
result = await run_renovate_local(
    directory="/path/to/project",
    config_file="/path/to/renovate.json",
    dry_run_mode="extract",
    log_level="debug"
)
```

### Checking for Available Updates

```python
updates = await get_dependency_updates(
    repository="owner/repo",
    branch="main",
    filter="npm"
)
```

### Creating an Onboarding PR

```python
result = await create_onboarding_pr(
    repository="owner/repo",
    config_template='{"extends": ["config:base"]}'
)
```

### Validating Credentials

```python
result = await validate_credentials(
    platform="github",
    token="your-token"
)
```

## Renovate Configuration

Create a `renovate.json` file in your repository:

```json
{
  "extends": [
    "config:base"
  ],
  "schedule": [
    "every weekend"
  ],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    }
  ]
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Building the Package

```bash
python -m build
```

## Local Platform Notes

The `run_renovate_local` tool is designed for testing Renovate configurations on your local filesystem:

- **Dry Run Only**: Local platform only supports dry-run modes (`extract` or `lookup`)
- **No Branch Creation**: Cannot create branches or pull requests
- **Current Directory**: Renovate must be run from within the target directory
- **Package Files**: Works with various package managers (npm, pip, gem, go, etc.)
- **Config Testing**: Ideal for testing `renovate.json` configurations before deployment

## Troubleshooting

1. **Authentication Issues**: Ensure your token has the necessary permissions (repo access, pull request creation)
2. **Renovate Not Found**: Make sure Renovate CLI is installed globally: `npm install -g renovate`
3. **Platform Access**: Some platforms may require additional configuration (e.g., GitLab requires API URL)
4. **Local Platform**: Ensure you have read access to the directory and it contains valid package files

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
---
*Last updated: 2025-07-29 16:13:12 UTC*
