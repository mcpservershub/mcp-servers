# Grype MCP Server

An MCP (Model Context Protocol) server that provides tools for vulnerability scanning using Grype by Anchore.

## Features

- **Docker Image Scanning**: Scan Docker images for vulnerabilities
- **Filesystem Scanning**: Scan local directories and files for vulnerabilities
- **SBOM Scanning**: Scan Software Bill of Materials (SBOM) files
- **Database Management**: Update and check vulnerability database status
- **Flexible Output Formats**: Support for multiple output formats

## Prerequisites

- Python 3.12+
- Grype CLI installed and available in PATH
- MCP-compatible client

## Installation

1. Install Grype CLI:
   ```bash
   # Using curl
   curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

   # Or using Homebrew (macOS/Linux)
   brew install grype

   # Or download binary directly
   wget https://github.com/anchore/grype/releases/download/v0.74.0/grype_0.74.0_linux_amd64.tar.gz
   tar -xzf grype_0.74.0_linux_amd64.tar.gz
   sudo mv grype /usr/local/bin/
   ```

2. Install the MCP server:
   ```bash
   pip install -e .
   ```

## Usage

### Running the Server

```bash
grype-mcp-server
```

### Environment Variables

- `GRYPE_MCP_DEBUG=true` - Enable debug logging

### Available Tools

1. **scan_docker_image**
   - Scan Docker images for vulnerabilities
   - Parameters:
     - `image`: Docker image name (e.g., alpine:latest)
     - `output_file`: Where to save results (required)
     - `fail_on`: Set exit code to 1 if vulnerability >= severity (optional)
     - `format`: Output format (default: table)
     - `scope`: Scan scope - squashed or all-layers (default: squashed)
     - `only_fixed`: Only show vulnerabilities with fixes (default: false)

2. **scan_filesystem**
   - Scan local directories or files
   - Parameters:
     - `path`: Path to scan
     - `output_file`: Where to save results (required)
     - `fail_on`: Set exit code to 1 if vulnerability >= severity (optional)
     - `format`: Output format (default: table)
     - `exclude`: Comma-separated paths to exclude
     - `only_fixed`: Only show vulnerabilities with fixes (default: false)

3. **scan_sbom**
   - Scan SBOM files for vulnerabilities
   - Parameters:
     - `sbom_file`: Path to SBOM file
     - `output_file`: Where to save results (required)
     - `fail_on`: Set exit code to 1 if vulnerability >= severity (optional)
     - `format`: Output format (default: table)
     - `only_fixed`: Only show vulnerabilities with fixes (default: false)

4. **update_database**
   - Update Grype's vulnerability database
   - No parameters required

5. **check_database_status**
   - Check vulnerability database status
   - No parameters required

6. **check_grype_status**
   - Check Grype installation and version
   - No parameters required

### Supported Output Formats

- `table`: Human-readable table format (default)
- `json`: JSON format
- `cyclonedx`: CycloneDX XML format
- `cyclonedx-json`: CycloneDX JSON format
- `sarif`: SARIF format
- `template`: Custom template format

### Severity Levels

- `UNKNOWN`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Examples

```python
# Scan a Docker image
await scan_docker_image(
    image="alpine:latest",
    output_file="/tmp/alpine_scan.json",
    format="json",
    scope="all-layers"
)

# Scan a local directory
await scan_filesystem(
    path="/path/to/project",
    output_file="/tmp/project_scan.txt",
    exclude="node_modules,vendor",
    only_fixed=True
)

# Scan an SBOM file
await scan_sbom(
    sbom_file="/path/to/sbom.json",
    output_file="/tmp/sbom_scan.json",
    format="json"
)

# Update vulnerability database
await update_database()
```

## Notes

- Grype does not support direct GitHub repository scanning. To scan a repository, clone it locally first and use `scan_filesystem`.
- The `severity` parameter is included for consistency but Grype doesn't have built-in severity filtering. Use the output format and parse results as needed.
- For SBOM generation, use the separate Syft MCP server.

## License

MIT