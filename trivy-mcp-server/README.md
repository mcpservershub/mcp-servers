# Trivy MCP Server

An MCP (Model Context Protocol) server that provides tools for vulnerability scanning using Trivy.

## Features

- **Filesystem Scanning**: Scan local directories and files for vulnerabilities
- **GitHub Repository Scanning**: Scan remote GitHub repositories
- **Docker Image Scanning**: Scan Docker images (local or remote)
- **Configuration Scanning**: Scan for IaC misconfigurations
- **SBOM Generation**: Generate Software Bill of Materials
- **Vulnerability Database Info**: Get information about the vulnerability database

## Prerequisites

- Python 3.12+
- Trivy CLI installed and available in PATH
- MCP-compatible client

## Installation

1. Install Trivy CLI:
    Trivy is pre-installed in the MCP Server Container image.

2. Install the MCP server:
   ```bash
   pip install -e .
   ```

## Usage

### Running the Server

 #### Docker:
```json
 {
    "mcpServers": {
        "syftScanner": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--mount",
                "type=bind,src=/home/santosh/genval,dst=/app/genval",
                "santoshkal/trvy-mcp:test"
            ]
        }
    }
}
 ```

Or:

```bash
trivy-mcp-server
```

### Available Tools

1. **scan_filesystem**
   - Scan local directories for vulnerabilities
   - Parameters:
     - `path`: Path to scan
     - `output_file`: Where to save results (required)
     - `severity`: Filter by severity levels (optional)
     - `format`: Output format (default: table)

2. **scan_github_repo**
   - Scan GitHub repositories
   - Parameters:
     - `repo_url`: Repository URL
     - `output_file`: Where to save results (required)
     - `branch`: Specific branch to scan (optional)
     - `severity`: Filter by severity levels (optional)
     - `format`: Output format (default: table)

3. **scan_docker_image**
   - Scan Docker images
   - Parameters:
     - `image`: Image name or tag
     - `output_file`: Where to save results (required)
     - `severity`: Filter by severity levels (optional)
     - `format`: Output format (default: table)

4. **scan_config**
   - Scan for misconfigurations
   - Parameters:
     - `path`: Path to scan
     - `output_file`: Where to save results (required)
     - `policy_type`: Type of policies to check (optional)
     - `format`: Output format (default: table)

5. **scan_sbom**
   - Generate SBOM
   - Parameters:
     - `target`: Target to scan
     - `output_file`: Where to save SBOM (required)
     - `sbom_format`: SBOM format (default: cyclonedx)

6. **list_vulnerabilities**
   - Get vulnerability database info
   - Parameters:
     - `output_file`: Where to save info (required)
     - `db_type`: Database type (default: vulnerability)

### Supported Output Formats

- `table`: Human-readable table format
- `json`: JSON format
- `sarif`: SARIF format
- `github`: GitHub Actions format
- `gitlab`: GitLab format
- `cyclonedx`: CycloneDX SBOM format
- `spdx`: SPDX SBOM format

### Severity Levels

- `UNKNOWN`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Examples

```python
# Scan a local project
await scan_filesystem(
    path="/path/to/project",
    output_file="/tmp/scan_results.json",
    severity="HIGH,CRITICAL",
    format="json"
)

# Scan a GitHub repository
await scan_github_repo(
    repo_url="https://github.com/aquasecurity/trivy",
    output_file="/tmp/repo_scan.json",
    branch="main",
    format="json"
)

# Scan a Docker image
await scan_docker_image(
    image="alpine:3.10",
    output_file="/tmp/alpine_scan.json",
    format="json"
)
```

## License

MIT
