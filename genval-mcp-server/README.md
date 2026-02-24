# Genval MCP Server

A comprehensive Model Context Protocol (MCP) server that provides AI agents with full access to the [Genval](https://github.com/intelops/genval) CLI tool for configuration validation and generation.

## Overview

This MCP server exposes all Genval commands as MCP tools, enabling AI agents and LLMs to:

- **Validate and Generate** Dockerfiles, Kubernetes manifests, and Terraform files
- **Work with Multiple Policy Languages** including Rego (OPA), CEL, and Cue
- **Manage OCI Artifacts** with signing and verification via Sigstore Cosign
- **Generate Secure Configurations** using AI-powered generation
- **Validate with Regex Patterns** for simple validation rules
- **Remediate Issues** automatically using AI models

## Features

### Core Validation Tools

- **Rego Validation (regoval)**: Validate Dockerfiles, Kubernetes manifests, and Terraform files using OPA Rego policies
- **CEL Validation (celval)**: Validate using Common Expression Language policies for more expressive rules
- **Cue Validation**: Validate and generate Kubernetes manifests with Cue definitions
- **Regex Validation**: Simple pattern-based validation

### Artifact Management

- **Build**: Create OCI-compliant artifacts from configuration files
- **Push**: Push artifacts to container registries with optional signing
- **Pull**: Download and verify artifacts from registries

### AI-Powered Generation

- **GenAI**: Generate secure Infrastructure as Code using LLM backends (OpenAI, Ollama, etc.)

### Utilities

- **showJSON**: Convert Dockerfiles and Terraform files to JSON for policy development
- **version**: Get Genval version information

## Prerequisites

- Python 3.12 or higher
- [Genval](https://github.com/intelops/genval) CLI installed and in PATH
- [uv](https://github.com/astral-sh/uv) for fast Python package management (recommended)

### Installing Genval

```bash
# Download the latest release
curl -sSfL https://raw.githubusercontent.com/intelops/genval/main/install.sh | sh

# Or install from source
git clone https://github.com/intelops/genval.git
cd genval
make build
sudo mv genval /usr/local/bin/
```

## Installation

### Option 1: Using uv (Recommended)

```bash
cd genval-mcp-server

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -e .
```

### Option 2: Using pip

```bash
cd genval-mcp-server

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Running the MCP Server

### Standalone Mode (STDIO)

```bash
python src/genval_mcp_server.py
```

### With MCP Inspector (Testing)

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Run the inspector
mcp-inspector python src/genval_mcp_server.py
```

This will open a web interface at `http://localhost:5173` where you can:
- View all available tools
- Test tool invocations interactively
- See request/response payloads
- Debug tool implementations

## MCP Configuration

### For Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "genval": {
      "command": "python",
      "args": [
        "/absolute/path/to/genval-mcp-server/src/genval_mcp_server.py"
      ]
    }
  }
}
```

### For Other MCP Clients

```json
{
  "mcpServers": {
    "genval": {
      "command": "python",
      "args": [
        "/absolute/path/to/genval-mcp-server/src/genval_mcp_server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "ARTIFACT_REGISTRY_USERNAME": "your_username",
        "ARTIFACT_REGISTRY_PASSWORD": "your_password"
      }
    }
  }
}
```

## Docker Deployment

### Building the Docker Image

```bash
docker build -t genval-mcp-server:latest .
```

### Running in Docker

```bash
# Basic run
docker run -i genval-mcp-server:latest

# With environment variables
docker run -i \
  -e GITHUB_TOKEN=your_token \
  -e ARTIFACT_REGISTRY_USERNAME=your_username \
  -e ARTIFACT_REGISTRY_PASSWORD=your_password \
  genval-mcp-server:latest

# With volume mounts for input files and output
docker run -i \
  -v $(pwd):/workspace \
  -v $(pwd)/output:/output \
  genval-mcp-server:latest

# For MCP Inspector testing
npx @modelcontextprotocol/inspector docker run -i \
  --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/output:/output \
  genval-mcp-server:latest
```

**Important Notes:**

- **Input Files**: Mount your input directory to `/workspace` for Genval to access configuration files
- **Output Files**: Mount an output directory to `/output` for generated artifacts and results
- **Results Logging**: Genval writes `results.json` to the working directory. The MCP server automatically copies this to `/output/results-<timestamp>.json` if the `/output` mount is writable
- **Permissions**: Ensure the output directory is writable. Run `chmod 777 ./output` or `chown 65532:65532 ./output` (UID 65532 is Chainguard's `nonroot` user)

### MCP Configuration for Docker

```json
{
  "mcpServers": {
    "genval": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/workspace:/workspace",
        "-v",
        "/path/to/output:/output",
        "genval-mcp-server:latest"
      ]
    }
  }
}
```

**Note**: The `/output` mount is optional but recommended for capturing `results.json` files generated by Genval commands.

## Available Tools

### Version Information

#### `genval_version`

Get the installed Genval version.

**Parameters**: None

**Example**:
```json
{}
```

**Returns**: Version information string

---

### Artifact Management

#### `artifact_build`

Build an OCI-compliant artifact from configuration files.

**Parameters**:
- `reqinput` (required): Path to source files/directory
- `output` (optional): Path to store artifact (default: ".")

**Example**:
```json
{
  "reqinput": "./templates/inputs",
  "output": "./output/artifact.tar.gz"
}
```

#### `artifact_push`

Push an artifact to an OCI registry.

**Parameters**:
- `reqinput` (required): Path to source files
- `dest` (required): Destination URL (e.g., `oci://ghcr.io/org/repo:tag`)
- `sign` (optional): Sign with cosign (default: false)
- `cosign_key` (optional): Path to cosign private key
- `credentials` (optional): Registry credentials (`USER:PAT` or `PAT`)
- `annotations` (optional): List of annotations (`key=value`)

**Example**:
```json
{
  "reqinput": "./policies",
  "dest": "oci://ghcr.io/myorg/policies:v1.0.0",
  "sign": true,
  "annotations": ["org.opencontainers.image.description=My policies"]
}
```

#### `artifact_pull`

Pull an artifact from an OCI registry.

**Parameters**:
- `dest` (required): Source URL
- `path` (required): Path to store pulled artifact
- `verify` (optional): Verify signature (default: false)
- `pub_key` (optional): Cosign public key path
- `credentials` (optional): Registry credentials

**Example**:
```json
{
  "dest": "oci://ghcr.io/myorg/policies:v1.0.0",
  "path": "./downloaded",
  "verify": true
}
```

---

### Dockerfile Tools

#### `dockerfile_generate`

Generate and validate a Dockerfile from JSON/YAML input.

**Parameters**:
- `reqinput` (required): Input template file
- `output` (required): Output Dockerfile path
- `inputpolicy` (optional): Input validation policy
- `outputpolicy` (optional): Output validation policy
- `credentials` (optional): OCI registry credentials
- `takeaction` (optional): Enable remediation (default: false)

**Example**:
```json
{
  "reqinput": "./input.json",
  "output": "./Dockerfile",
  "inputpolicy": "./policies/input.rego",
  "outputpolicy": "./policies/output.rego"
}
```

---

### Rego Validation (regoval)

#### `regoval_dockerfile`

Validate Dockerfile using Rego policies.

**Parameters**:
- `reqinput` (required): Dockerfile path
- `policy` (required): Rego policy path/URL
- `credentials` (optional): Registry credentials
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model for remediation
- `output` (optional): Output path

**Example**:
```json
{
  "reqinput": "./Dockerfile",
  "policy": "./policies/dockerfile.rego",
  "takeaction": true,
  "model": "gpt-4"
}
```

#### `regoval_infrafile`

Validate Kubernetes manifests using Rego policies.

**Parameters**:
- `reqinput` (required): Manifest file (YAML/JSON)
- `policy` (required): Rego policy path/URL
- `credentials` (optional): Registry credentials
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model for remediation
- `output` (optional): Output path

**Example**:
```json
{
  "reqinput": "./deployment.yaml",
  "policy": "oci://ghcr.io/intelops/policyhub/genval/infrafile_policies:v0.0.1"
}
```

#### `regoval_terraform`

Validate Terraform files using Rego policies.

**Parameters**:
- `reqinput` (required): Terraform .tf file
- `policy` (required): Rego policy path/URL
- `credentials` (optional): Registry credentials
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model

**Example**:
```json
{
  "reqinput": "./main.tf",
  "policy": "./policies/terraform.rego"
}
```

---

### CEL Validation (celval)

#### `celval_dockerfile`

Validate Dockerfile using CEL policies.

**Parameters**:
- `reqinput` (required): Dockerfile path
- `policy` (required): CEL policy directory
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model
- `output` (optional): Output path

**Example**:
```json
{
  "reqinput": "./Dockerfile",
  "policy": "./policies/cel"
}
```

#### `celval_infrafile`

Validate Kubernetes manifests using CEL policies.

**Parameters**:
- `reqinput` (required): Manifest file
- `policy` (required): CEL policy file
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model
- `output` (optional): Output path

**Example**:
```json
{
  "reqinput": "./deployment.yaml",
  "policy": "./policies/k8s_cel.yaml"
}
```

#### `celval_terraform`

Validate Terraform files using CEL policies.

**Parameters**:
- `reqinput` (required): Terraform file
- `policy` (required): CEL policy file
- `config` (optional): YAML config file
- `takeaction` (optional): Enable remediation
- `model` (optional): AI model
- `output` (optional): Output path

**Example**:
```json
{
  "reqinput": "./main.tf",
  "policy": "./policies/terraform_cel.yaml"
}
```

---

### Cue Validation

#### `cue_validate_generate`

Validate and generate Kubernetes manifests using Cue.

**Parameters**:
- `reqinput` (required): Input manifest file/URL
- `resource` (required): Top-level Cue definition label
- `policy` (required): Policy directory with cue.mod
- `output` (optional): Output directory
- `verbose` (optional): Enable verbose logging

**Example**:
```json
{
  "reqinput": "./k8s/app.yaml",
  "resource": "Application",
  "policy": "./policy",
  "output": "./output"
}
```

#### `cuemod_init`

Initialize Cue workspace.

**Parameters**:
- `tool` (required): Tool identifier (e.g., `k8s:latest`, `argocd:latest`)
- `credentials` (optional): Registry credentials
- `key` (optional): Cosign public key

**Example**:
```json
{
  "tool": "k8s:latest"
}
```

---

### Regex Validation

#### `regex_validate`

Validate files using regex patterns.

**Parameters**:
- `reqinput` (required): Input file
- `policy` (required): Regex policy file

**Example**:
```json
{
  "reqinput": "./deployment.json",
  "policy": "./policies/regex_policy.yaml"
}
```

---

### AI Generation

#### `genai_generate`

Generate IaC using AI models.

**Parameters**:
- `prompt` (required): User prompt
- `model` (required): AI model (e.g., "GPT4", "Ollama")
- `output` (required): Output file path
- `endpoint` (optional): LLM endpoint
- `assistant` (optional): Assistant identifier
- `user_system_prompt` (optional): Custom system prompt
- `config` (optional): Config file

**Example**:
```json
{
  "prompt": "Create a secure Kubernetes deployment for nginx",
  "model": "GPT4",
  "output": "./deployment.yaml"
}
```

#### `genai_init`

Initialize GenAI resources.

**Parameters**: None

**Example**:
```json
{}
```

---

### Utilities

#### `show_json`

Display JSON representation of Dockerfile or .tf file.

**Parameters**:
- `reqinput` (required): Dockerfile or .tf file path

**Example**:
```json
{
  "reqinput": "./Dockerfile"
}
```

## Example Workflows

### Workflow 1: Validate Kubernetes Deployment

```python
# 1. Check Genval version
genval_version()

# 2. Validate deployment with Rego policies
regoval_infrafile(
    reqinput="./k8s/deployment.yaml",
    policy="./policies/k8s.rego"
)
```

### Workflow 2: Generate and Validate Dockerfile

```python
# 1. Generate Dockerfile from template
dockerfile_generate(
    reqinput="./templates/app.json",
    output="./Dockerfile",
    inputpolicy="./policies/input.rego",
    outputpolicy="./policies/output.rego"
)

# 2. Show JSON representation
show_json(reqinput="./Dockerfile")

# 3. Validate with CEL policies
celval_dockerfile(
    reqinput="./Dockerfile",
    policy="./policies/cel"
)
```

### Workflow 3: Build and Push Artifact

```python
# 1. Build artifact from configs
artifact_build(
    reqinput="./configs",
    output="./artifact.tar.gz"
)

# 2. Push to registry with signing
artifact_push(
    reqinput="./configs",
    dest="oci://ghcr.io/myorg/configs:v1.0.0",
    sign=True,
    credentials="USERNAME:TOKEN"
)
```

### Workflow 4: AI-Powered Generation

```python
# 1. Initialize GenAI
genai_init()

# 2. Generate secure deployment
genai_generate(
    prompt="Create a production-ready Kubernetes deployment for a Python Flask app with security best practices",
    model="GPT4",
    output="./deployment.yaml"
)

# 3. Validate generated manifest
regoval_infrafile(
    reqinput="./deployment.yaml",
    policy="oci://ghcr.io/intelops/policyhub/genval/infrafile_policies:v0.0.1"
)
```

## Testing

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_tools.py
```

### Manual Testing with MCP Inspector

1. Start MCP Inspector:
   ```bash
   mcp-inspector python src/genval_mcp_server.py
   ```

2. Open http://localhost:5173 in your browser

3. Select a tool from the list

4. Fill in the parameters

5. Click "Run Tool" to see the output

## Environment Variables

The server supports the following environment variables:

- `GITHUB_TOKEN`: GitHub Personal Access Token for accessing private repositories
- `ARTIFACT_REGISTRY_USERNAME`: OCI registry username
- `ARTIFACT_REGISTRY_PASSWORD`: OCI registry password/token
- `OPENAI_API_KEY`: OpenAI API key for GenAI features
- `OLLAMA_ENDPOINT`: Ollama endpoint URL for local LLM

## Troubleshooting

### Genval Not Found

```
Error: genval executable not found. Please ensure genval is installed and in PATH.
```

**Solution**: Install Genval and ensure it's in your PATH:
```bash
which genval  # Should show the path to genval
```

### Permission Denied

```
Error: Permission denied when accessing file
```

**Solution**: Ensure the MCP server has read/write permissions for the working directory:
```bash
chmod +x /path/to/genval-mcp-server/src/genval_mcp_server.py
```

### Docker Registry Authentication

```
Error: Failed to authenticate with registry
```

**Solution**: Provide credentials via environment variables or ensure `~/.docker/config.json` exists:
```bash
docker login ghcr.io
```

## Development

### Project Structure

```
genval-mcp-server/
├── src/
│   ├── __init__.py
│   └── genval_mcp_server.py    # Main MCP server implementation
├── tests/
│   ├── __init__.py
│   └── test_tools.py            # Test suite
├── Dockerfile                    # Multi-stage container build
├── pyproject.toml               # Project dependencies
├── README.md                     # This file
└── mcp_config.json              # Example MCP configuration
```

### Adding New Tools

1. Add a new function with the `@app.tool()` decorator
2. Define parameter types using Pydantic Field
3. Add comprehensive docstring
4. Use the `run_genval_command()` helper
5. Add tests in `tests/test_tools.py`
6. Update README with usage examples

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Performance Considerations

- **Subprocess Overhead**: Each tool call spawns a subprocess. For batch operations, consider using Genval's batch modes where available.
- **Large Files**: When working with large manifests or policies, ensure adequate memory is available.
- **Network Operations**: Artifact push/pull and remote policy fetching may be slow depending on network speed.
- **Docker Layer Caching**: The Dockerfile uses multi-stage builds to optimize build times.

## Security Considerations

- **Credentials**: Never hardcode credentials. Use environment variables or mounted secrets.
- **Input Validation**: The server validates inputs, but always review generated configurations.
- **Subprocess Injection**: User inputs are passed as separate arguments to prevent command injection.
- **Docker Isolation**: Run in Docker for additional isolation and security.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Resources

- [Genval Documentation](https://github.com/intelops/genval)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [OPA/Rego Documentation](https://www.openpolicyagent.org/docs/latest/)
- [CEL Documentation](https://github.com/google/cel-spec)
- [Cue Documentation](https://cuelang.org/)

## Support

For issues and questions:

- Genval Issues: https://github.com/intelops/genval/issues
- MCP Server Issues: Create an issue in this repository
- Community: Join discussions in the Genval community

---

**Built with Python 3.12 and FastMCP** | **Powered by Genval**
