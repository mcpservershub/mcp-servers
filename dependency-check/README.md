# Dependency Check MCP Server

An MCP (Model Context Protocol) server that integrates OWASP Dependency Check for vulnerability scanning of software projects. This server provides tools to scan projects, manage vulnerability databases, and analyze security reports across multiple programming languages.

## Features

- **Multi-language Support**: Automatically detects and scans projects in Python, JavaScript, Java, .NET, Go, Ruby, Rust, and more
- **Comprehensive Scanning**: Identifies known vulnerabilities using CVE database
- **Flexible Output**: Supports multiple report formats (JSON, XML, HTML, CSV, SARIF, etc.)
- **Database Management**: Update and maintain vulnerability databases
- **False Positive Management**: Generate suppression files for known false positives
- **Containerized**: Runs in Docker for consistent environments

## Installation

### Using Docker (Recommended)

1. Clone this repository:
```bash
git clone <repository-url>
cd dependency-check
```

2. Build the Docker image:
```bash
docker build -t dependency-check-mcp .
```

3. Run with docker-compose:
```bash
docker-compose up -d
```

### Local Installation

1. Ensure you have Python 3.10+ installed

2. Clone and install the package:
```bash
git clone <repository-url>
cd dependency-check
pip install -e .
```

3. For development, install with dev dependencies:
```bash
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

4. Download and install OWASP Dependency Check CLI

## Configuration

### Environment Variables

- `NVD_API_KEY`: (Recommended) NVD API key for faster database updates
- `WORKSPACE_PATH`: Local directory to mount for scanning (default: `./workspace`)
- `OUTPUT_PATH`: Directory for scan reports (default: `./output`)
- `SUPPRESSION_PATH`: Directory containing suppression files (default: `./suppressions`)

### Docker Compose Configuration

Edit `docker-compose.yml` to customize:
- Volume mounts for your projects
- Resource limits
- Environment variables

## MCP Tools

### 1. scan_project

Scans a project for known vulnerabilities.

**Arguments:**
- `path` (required): Path to project directory or files
- `output_file` (required): Path where scan results will be saved
- `output_format`: Report format (JSON, XML, HTML, CSV, SARIF, JUNIT, JENKINS, GITLAB, ALL)
- `exclude_patterns`: List of patterns to exclude from scanning
- `fail_on_cvss`: CVSS score threshold to fail the scan (0-10)
- `suppression_files`: List of suppression file paths
- `enable_experimental`: Enable experimental analyzers
- `nvd_api_key`: NVD API key for updates

**Example:**
```json
{
  "tool": "scan_project",
  "arguments": {
    "path": "/workspace/my-python-app",
    "output_file": "/output/scan-report.json",
    "output_format": "JSON",
    "exclude_patterns": ["**/venv/**", "**/test/**"],
    "fail_on_cvss": 7.0
  }
}
```

### 2. update_database

Updates the vulnerability database from NVD.

**Arguments:**
- `nvd_api_key`: NVD API key for faster updates
- `data_directory`: Directory to store the database
- `proxy_server`: Proxy server URL
- `proxy_port`: Proxy port
- `connection_timeout`: Connection timeout in seconds

**Example:**
```json
{
  "tool": "update_database",
  "arguments": {
    "nvd_api_key": "your-api-key-here"
  }
}
```

### 3. check_vulnerabilities

Searches for specific vulnerabilities in scan results.

**Arguments:**
- `report_path` (required): Path to scan report (JSON format)
- `cve_ids`: List of specific CVE IDs to search for
- `min_cvss_score`: Minimum CVSS score filter
- `severity_levels`: Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)

**Example:**
```json
{
  "tool": "check_vulnerabilities",
  "arguments": {
    "report_path": "/output/scan-report.json",
    "severity_levels": ["HIGH", "CRITICAL"],
    "min_cvss_score": 7.0
  }
}
```

### 4. generate_suppression

Creates suppression rules for false positives.

**Arguments:**
- `report_path` (required): Path to scan report
- `output_file` (required): Path to save suppression file
- `cpe_uri`: CPE URI to suppress
- `cve_id`: Specific CVE to suppress
- `file_path`: File path pattern to suppress
- `notes`: Notes about the suppression

**Example:**
```json
{
  "tool": "generate_suppression",
  "arguments": {
    "report_path": "/output/scan-report.json",
    "output_file": "/suppressions/project-suppressions.xml",
    "cve_id": "CVE-2021-12345",
    "notes": "False positive - not applicable to our usage"
  }
}
```

### 5. get_scan_summary

Provides a summary of vulnerabilities from a scan report.

**Arguments:**
- `report_path` (required): Path to scan report
- `group_by`: Group results by "severity", "dependency", or "cve"

**Example:**
```json
{
  "tool": "get_scan_summary",
  "arguments": {
    "report_path": "/output/scan-report.json",
    "group_by": "severity"
  }
}
```

## Usage Examples

### Python Example

```python
import mcp
import asyncio

async def scan_project():
    async with mcp.ClientSession() as session:
        client = await session.connect_to_server("dependency-check-mcp")
        
        # Scan a Python project
        result = await client.call_tool(
            "scan_project",
            {
                "path": "/workspace/my-django-app",
                "output_file": "/output/django-scan.json",
                "output_format": "JSON",
                "exclude_patterns": ["**/venv/**", "**/migrations/**"]
            }
        )
        print(result)
        
        # Get summary
        summary = await client.call_tool(
            "get_scan_summary",
            {
                "report_path": "/output/django-scan.json",
                "group_by": "severity"
            }
        )
        print(summary)

asyncio.run(scan_project())
```

### Running Tests

```bash
# Create virtual environment with Python 3.12
python3.12 -m venv venv
source venv/bin/activate

# Install package with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Supported Languages

The server automatically detects and configures scanning for:

- **Python**: requirements.txt, setup.py, pyproject.toml, Pipfile
- **JavaScript/Node**: package.json, yarn.lock, pnpm-lock.yaml
- **Java**: pom.xml, build.gradle, *.jar
- **.NET**: *.csproj, packages.config, *.dll
- **Ruby**: Gemfile, Gemfile.lock
- **Go**: go.mod, go.sum
- **PHP**: composer.json, composer.lock
- **Rust**: Cargo.toml, Cargo.lock
- And many more...

## Security Considerations

1. **Read-Only Mounts**: Project directories are mounted read-only to prevent modifications
2. **API Keys**: Store NVD API keys securely using environment variables
3. **Network Isolation**: Consider network policies when deploying
4. **Resource Limits**: Configure appropriate CPU and memory limits

## Troubleshooting

### Common Issues

1. **"Dependency Check binary not found"**
   - Ensure the Docker image built successfully
   - Check DEPENDENCY_CHECK_HOME environment variable

2. **"Database update failed"**
   - Verify internet connectivity
   - Check proxy settings if behind a firewall
   - Ensure NVD API key is valid

3. **"Path does not exist"**
   - Verify volume mounts in docker-compose.yml
   - Ensure paths are accessible from the container

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. OWASP Dependency Check is licensed under the Apache 2.0 License.
---
*Last updated: 2025-07-29 16:13:12 UTC*
