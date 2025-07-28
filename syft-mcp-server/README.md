# Syft MCP Server

An MCP (Model Context Protocol) server that provides tools for SBOM (Software Bill of Materials) generation using Syft by Anchore.

## Features

- **Container Image SBOM Generation**: Generate SBOMs from Docker/OCI container images
- **Filesystem SBOM Generation**: Generate SBOMs from local directories and files
- **Archive SBOM Generation**: Generate SBOMs from archive files (tar, zip, etc.)
- **SBOM Format Conversion**: Convert between different SBOM formats
- **Package Listing**: Simple package listing without full SBOM structure
- **Multiple Output Formats**: Support for SPDX, CycloneDX, and Syft formats

## Prerequisites

- Python 3.12+
- Syft CLI installed and available in PATH
- MCP-compatible client

## Installation

1. Install Syft CLI:
   ```bash
   # Using curl (recommended)
   curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

   # Or using Homebrew (macOS/Linux)
   brew install syft

   # Or download binary directly
   wget https://github.com/anchore/syft/releases/latest/download/syft_<VERSION>_linux_amd64.tar.gz
   tar -xzf syft_<VERSION>_linux_amd64.tar.gz
   sudo mv syft /usr/local/bin/
   ```

2. Install the MCP server:
   ```bash
   pip install -e .
   ```

## Usage

### Running the Server

#### Docker
NOTE: Mount the required Project into the container to have the MCP Server access to the project.

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
                "santoshkal/syft-mcp:test"
            ]
        }
    }
}
```


```bash
syft-mcp-server
```

### Environment Variables

- `SYFT_MCP_DEBUG=true` - Enable debug logging

### Available Tools

1. **generate_sbom_from_image**
   - Generate SBOM from container images
   - Parameters:
     - `image`: Container image name (e.g., alpine:latest)
     - `output_file`: Where to save SBOM (required)
     - `format`: SBOM format (default: spdx-json)
     - `scope`: Scan scope - squashed or all-layers (default: squashed)

2. **generate_sbom_from_filesystem**
   - Generate SBOM from local directories or files
   - Parameters:
     - `path`: Path to scan
     - `output_file`: Where to save SBOM (required)
     - `format`: SBOM format (default: spdx-json)
     - `exclude`: Comma-separated globs to exclude from scanning

3. **generate_sbom_from_archive**
   - Generate SBOM from archive files
   - Parameters:
     - `archive_path`: Path to archive file
     - `output_file`: Where to save SBOM (required)
     - `format`: SBOM format (default: spdx-json)

4. **convert_sbom**
   - Convert between SBOM formats
   - Parameters:
     - `input_file`: Path to input SBOM file (required)
     - `output_file`: Where to save converted SBOM (required)
     - `output_format`: Target format (required)

5. **list_packages**
   - Generate simple package list
   - Parameters:
     - `target`: Target to scan (image, directory, file, or archive)
     - `output_file`: Where to save package list (required)
     - `format`: Output format (default: syft-table)

6. **check_syft_status**
   - Check Syft installation and version
   - No parameters required

### Supported SBOM Formats

- `spdx-json`: SPDX JSON format
- `spdx-tag-value`: SPDX tag-value format
- `cyclonedx-json`: CycloneDX JSON format
- `cyclonedx-xml`: CycloneDX XML format
- `syft-json`: Syft native JSON format (most detailed)

### Package List Formats

- `syft-table`: Human-readable table format
- `syft-text`: Simple text format
- `syft-json`: JSON format with package details

## Examples

```python
# Generate SBOM from Docker image
await generate_sbom_from_image(
    image="node:16-alpine",
    output_file="/tmp/node_sbom.json",
    format="cyclonedx-json",
    scope="all-layers"
)

# Generate SBOM from local project
await generate_sbom_from_filesystem(
    path="/path/to/project",
    output_file="/tmp/project_sbom.json",
    format="spdx-json",
    exclude="test,docs,*.log"
)

# Convert SBOM format
await convert_sbom(
    input_file="/tmp/sbom_spdx.json",
    output_file="/tmp/sbom_cyclonedx.json",
    output_format="cyclonedx-json"
)

# List packages in simple format
await list_packages(
    target="alpine:latest",
    output_file="/tmp/alpine_packages.txt",
    format="syft-table"
)
```

## Notes

- Syft can detect packages from various sources including package managers, language-specific files, and even binary executables
- The `syft-json` format provides the most comprehensive information
- For vulnerability scanning of generated SBOMs, use the Grype MCP server

## License

MIT
