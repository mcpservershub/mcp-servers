# Cosign MCP Server

A Model Context Protocol (MCP) server for interacting with the Cosign CLI tool. This server provides tools to verify container images and artifacts using Cosign's signature verification capabilities.

## Features

- **verify_image**: Verify container image signatures
- **verify_artifact**: Verify artifact signatures
- **check_version**: Check installed Cosign version

## Installation

### Using UV (Recommended)

```bash
cd cosign-mcp-server
uv pip install -e .
```

### Using Docker

Build the Docker image:

```bash
docker build -t cosign-mcp-server .
```

## Usage

### As a CLI Application

```bash
cosign-mcp-server
```

### Using Docker

```bash
docker run -it cosign-mcp-server
```

## Tools

### verify_image

Verifies a container image signature.

Parameters:
- `image_name`: Container image to verify (e.g., `docker.io/example/image:tag`)
- `output_file`: Path to write verification output
- `certificate_identity_regexp`: Regular expression for certificate identity (default: `*@intelops.dev`)
- `certificate_oidc_issuer_regexp`: Regular expression for OIDC issuer (default: `*`)

### verify_artifact

Verifies an artifact signature.

Parameters:
- `artifact_name`: Artifact to verify (file path or URL)
- `output_file`: Path to write verification output
- `certificate_identity_regexp`: Regular expression for certificate identity (default: `*@intelops.dev`)
- `certificate_oidc_issuer_regexp`: Regular expression for OIDC issuer (default: `*`)

### check_version

Checks the installed Cosign version.

Parameters:
- `output_file`: Path to write version output

## Development

This project uses Python 3.12 and UV for dependency management. The MCP server is built using FastMCP for simplified server setup.

## License

MIT