#!/usr/bin/env python3
"""
Genval MCP Server

A Model Context Protocol (MCP) server that provides AI agents with comprehensive access
to the Genval CLI tool for configuration validation and generation.

This server exposes all genval commands as MCP tools, enabling AI agents to:
- Validate and generate Dockerfiles, Kubernetes manifests, and Terraform files
- Work with Rego, CEL, and Cue policies
- Manage OCI artifacts with signing and verification
- Generate secure configurations using AI
- Validate configurations with regex patterns

Author: Genval Contributors
License: Apache 2.0
"""

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP Server
app = FastMCP("genval-mcp-server")


# ============================================================================
# Helper Functions
# ============================================================================

async def run_genval_command(args: list[str]) -> dict[str, Any]:
    """
    Execute a genval command and return structured results.

    Genval writes results.json and other diagnostic logs to the current working directory.
    This function executes genval from /tmp (always writable) and optionally copies
    results.json to /output with a timestamp to avoid overwriting.

    Args:
        args: Command arguments to pass to genval

    Returns:
        Dictionary containing success status, stdout, stderr, and exit code

    Raises:
        RuntimeError: If genval executable is not found
    """
    import os
    import shutil
    import time

    try:
        # Check if genval is available
        result = await asyncio.create_subprocess_exec(
            "which", "genval",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.communicate()

        if result.returncode != 0:
            raise RuntimeError(
                "genval executable not found. Please ensure genval is installed and in PATH."
            )

        # Execute genval command from /tmp (always writable by nonroot user)
        # User-specified paths like /workspace/input or /output/file are absolute and work
        process = await asyncio.create_subprocess_exec(
            "genval",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/tmp"
        )

        stdout, stderr = await process.communicate()

        # Copy results.json to /output if it exists and /output is writable
        results_path = None
        try:
            results_exists = os.path.exists("/tmp/results.json")
            output_writable = os.path.isdir("/output") and os.access("/output", os.W_OK)

            if results_exists and output_writable:
                # Add timestamp to avoid overwriting previous results
                timestamp = int(time.time())
                results_path = f"/output/results-{timestamp}.json"
                shutil.copy2("/tmp/results.json", results_path)
                logger.info(f"Results copied to {results_path}")
        except Exception as copy_error:
            logger.warning(f"Could not copy results.json to /output: {copy_error}")

        return {
            "success": process.returncode == 0,
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "command": f"genval {' '.join(args)}",
            "results_file": results_path if results_path else "/tmp/results.json (not copied)"
        }

    except Exception as e:
        logger.error(f"Error executing genval command: {e}")
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "command": f"genval {' '.join(args)}"
        }


def format_result(result: dict[str, Any]) -> str:
    """
    Format command result for display.

    Args:
        result: Command execution result dictionary

    Returns:
        Formatted string representation
    """
    output = f"Command: {result['command']}\n"
    output += f"Exit Code: {result['exit_code']}\n"
    output += f"Success: {result['success']}\n"

    if result.get('results_file'):
        output += f"Results File: {result['results_file']}\n"

    output += "\n"

    if result['stdout']:
        output += f"Standard Output:\n{result['stdout']}\n"

    if result['stderr']:
        output += f"Standard Error:\n{result['stderr']}\n"

    return output


# ============================================================================
# Version Tool
# ============================================================================

@app.tool()
async def genval_version() -> str:
    """
    Get Genval version information.

    Returns version details of the installed genval binary.
    This is useful for debugging and ensuring compatibility.

    Returns:
        Version information as a string
    """
    result = await run_genval_command(["version"])
    return format_result(result)


# ============================================================================
# Artifact Management Tools
# ============================================================================

@app.tool()
async def artifact_build(
    reqinput: str = Field(
        ..., description="Path to source files/directory to build artifact from"
    ),
    output: str = Field(
        default=".", description="Path to store the built artifact (default: current directory)"
    )
) -> str:
    """
    Build an OCI-compliant artifact from configuration files.

    Takes a directory or set of configuration files and bundles them into
    an OCI-compliant tar.gz bundle ready to be pushed to a container registry.

    Args:
        reqinput: Path to source files or directory
        output: Path where the artifact will be saved

    Returns:
        Command execution result
    """
    args = ["artifact", "build", "--reqinput", reqinput, "--output", output]
    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def artifact_push(
    reqinput: str = Field(..., description="Path to source files to push"),
    dest: str = Field(
        ..., description="Destination URL for the registry (e.g., oci://ghcr.io/org/repo:tag)"
    ),
    sign: bool = Field(
        default=False, description="Sign the artifact with cosign in keyless mode"
    ),
    cosign_key: str | None = Field(
        default=None, description="Path to cosign private key for signing"
    ),
    credentials: str | None = Field(
        default=None, description="Registry credentials in USER:PAT or PAT format"
    ),
    annotations: list[str] | None = Field(
        default=None, description="Custom annotations in key=value format"
    )
) -> str:
    """
    Push an artifact to an OCI-compliant container registry.

    Builds and pushes configuration files as an OCI artifact. Supports signing
    with Sigstore cosign for supply chain security.

    Args:
        reqinput: Path to source files
        dest: Destination registry URL
        sign: Whether to sign with cosign
        cosign_key: Path to cosign private key (optional)
        credentials: Registry credentials (optional)
        annotations: List of custom annotations (optional)

    Returns:
        Command execution result
    """
    args = ["artifact", "push", "--reqinput", reqinput, "--dest", dest]

    if sign:
        args.extend(["--sign"])

    if cosign_key:
        args.extend(["--cosign-key", cosign_key])

    if credentials:
        args.extend(["--credentials", credentials])

    if annotations:
        for annotation in annotations:
            args.extend(["--annotations", annotation])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def artifact_pull(
    dest: str = Field(
        ..., description="Source URL to pull artifact from (e.g., oci://ghcr.io/org/repo:tag)"
    ),
    path: str = Field(..., description="Path to store the pulled artifact"),
    verify: bool = Field(
        default=False, description="Verify artifact signature using cosign"
    ),
    pub_key: str | None = Field(
        default=None, description="Cosign public key for verification"
    ),
    credentials: str | None = Field(
        default=None, description="Registry credentials in USER:PAT or PAT format"
    )
) -> str:
    """
    Pull an artifact from an OCI-compliant container registry.

    Downloads and extracts artifacts from registries. Supports signature
    verification using Sigstore cosign.

    Args:
        dest: Source registry URL
        path: Destination path for extracted files
        verify: Whether to verify signatures
        pub_key: Cosign public key path (optional)
        credentials: Registry credentials (optional)

    Returns:
        Command execution result
    """
    args = ["artifact", "pull", "--dest", dest, "--path", path]

    if verify:
        args.append("--verify")

    if pub_key:
        args.extend(["--pub-key", pub_key])

    if credentials:
        args.extend(["--credentials", credentials])

    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Dockerfile Tools
# ============================================================================

@app.tool()
async def dockerfile_generate(
    reqinput: str = Field(..., description="Input JSON/YAML file for generating Dockerfile"),
    output: str = Field(..., description="Path to write the generated Dockerfile"),
    inputpolicy: str | None = Field(default=None, description="Path/URL to input policy (Rego)"),
    outputpolicy: str | None = Field(default=None, description="Path/URL to output policy (Rego)"),
    credentials: str | None = Field(default=None, description="Credentials for OCI registries"),
    takeaction: bool = Field(default=False, description="Remediate failures automatically")
) -> str:
    """
    Generate and validate a Dockerfile from JSON/YAML input.

    Takes a JSON/YAML input file, validates it against input policies,
    generates a Dockerfile, and validates the generated Dockerfile against
    output policies. Supports policies from local paths, remote URLs, or OCI registries.

    Args:
        reqinput: Input template file path/URL
        output: Output Dockerfile path
        inputpolicy: Input validation policy (optional)
        outputpolicy: Output validation policy (optional)
        credentials: OCI registry credentials (optional)
        takeaction: Enable automatic remediation (optional)

    Returns:
        Command execution result
    """
    args = ["dockerfile", "--reqinput", reqinput, "--output", output]

    if inputpolicy:
        args.extend(["--inputpolicy", inputpolicy])

    if outputpolicy:
        args.extend(["--outputpolicy", outputpolicy])

    if credentials:
        args.extend(["--credentials", credentials])

    if takeaction:
        args.append("--takeaction")

    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Regoval (Rego Validation) Tools
# ============================================================================

@app.tool()
async def regoval_dockerfile(
    reqinput: str = Field(..., description="Dockerfile to validate"),
    policy: str = Field(
        ..., description="Path/URL to Rego policy directory or OCI registry URL"
    ),
    credentials: str | None = Field(default=None, description="OCI registry credentials"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(
        default=None, description="AI model for remediation (required if takeaction=true)"
    ),
    output: str | None = Field(
        default=None, description="Output path for remediated Dockerfile"
    )
) -> str:
    """
    Validate Dockerfile using Rego policies.

    Validates a Dockerfile against Rego policies. Policies can be from local
    filesystem, remote URLs, or OCI registries. Supports AI-powered remediation.

    Args:
        reqinput: Dockerfile path
        policy: Rego policy path/URL
        credentials: Registry credentials (optional)
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)
        output: Output path (optional)

    Returns:
        Command execution result
    """
    args = ["regoval", "dockerfileval", "--reqinput", reqinput, "--policy", policy]

    if credentials:
        args.extend(["--credentials", credentials])

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    if output:
        args.extend(["--output", output])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def regoval_infrafile(
    reqinput: str = Field(..., description="Kubernetes manifest file (YAML/JSON)"),
    policy: str = Field(..., description="Path/URL to Rego policy or OCI registry URL"),
    credentials: str | None = Field(default=None, description="OCI registry credentials"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(default=None, description="AI model for remediation"),
    output: str | None = Field(default=None, description="Output path for remediated manifest")
) -> str:
    """
    Validate Kubernetes manifests using Rego policies.

    Validates Kubernetes and related infrastructure manifests against Rego policies.
    Supports validation from local files, remote URLs, and OCI registries.

    Args:
        reqinput: Manifest file path (YAML/JSON)
        policy: Rego policy path/URL
        credentials: Registry credentials (optional)
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)
        output: Output path (optional)

    Returns:
        Command execution result
    """
    args = ["regoval", "infrafile", "--reqinput", reqinput, "--policy", policy]

    if credentials:
        args.extend(["--credentials", credentials])

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    if output:
        args.extend(["--output", output])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def regoval_terraform(
    reqinput: str = Field(..., description="Terraform .tf file to validate"),
    policy: str = Field(..., description="Path/URL to Rego policy or OCI registry URL"),
    credentials: str | None = Field(default=None, description="OCI registry credentials"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(default=None, description="AI model for remediation")
) -> str:
    """
    Validate Terraform files using Rego policies.

    Validates Terraform .tf files against Rego policies for security and
    best practices compliance.

    Args:
        reqinput: Terraform file path
        policy: Rego policy path/URL
        credentials: Registry credentials (optional)
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)

    Returns:
        Command execution result
    """
    args = ["regoval", "terraform", "--reqinput", reqinput, "--policy", policy]

    if credentials:
        args.extend(["--credentials", credentials])

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Celval (CEL Validation) Tools
# ============================================================================

@app.tool()
async def celval_dockerfile(
    reqinput: str = Field(..., description="Dockerfile to validate"),
    policy: str = Field(..., description="Path/URL to CEL policy directory"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(default=None, description="AI model for remediation"),
    output: str | None = Field(default=None, description="Output path for remediated Dockerfile")
) -> str:
    """
    Validate Dockerfile using Common Expression Language (CEL) policies.

    Validates Dockerfile against CEL policies, providing a more expressive
    and flexible policy language compared to Rego.

    Args:
        reqinput: Dockerfile path
        policy: CEL policy directory path/URL
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)
        output: Output path (optional)

    Returns:
        Command execution result
    """
    args = ["celval", "dockerfileval", "--reqinput", reqinput, "--policy", policy]

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    if output:
        args.extend(["--output", output])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def celval_infrafile(
    reqinput: str = Field(..., description="Kubernetes manifest file (YAML/JSON)"),
    policy: str = Field(..., description="Path/URL to CEL policy file (YAML)"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(default=None, description="AI model for remediation"),
    output: str | None = Field(default=None, description="Output path for remediated manifest")
) -> str:
    """
    Validate Kubernetes manifests using CEL policies.

    Validates Kubernetes and related infrastructure manifests using Common
    Expression Language policies for flexible validation rules.

    Args:
        reqinput: Manifest file path (YAML/JSON)
        policy: CEL policy file path/URL
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)
        output: Output path (optional)

    Returns:
        Command execution result
    """
    args = ["celval", "infrafile", "--reqinput", reqinput, "--policy", policy]

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    if output:
        args.extend(["--output", output])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def celval_terraform(
    reqinput: str = Field(..., description="Terraform .tf file to validate"),
    policy: str = Field(..., description="Path/URL to CEL policy file (YAML)"),
    config: str | None = Field(default=None, description="Path to YAML config file"),
    takeaction: bool = Field(default=False, description="Remediate failures"),
    model: str | None = Field(default=None, description="AI model for remediation"),
    output: str | None = Field(default=None, description="Output path for remediated file")
) -> str:
    """
    Validate Terraform files using CEL policies.

    Validates Terraform .tf files using Common Expression Language policies
    for infrastructure security and compliance.

    Args:
        reqinput: Terraform file path
        policy: CEL policy file path/URL
        config: YAML config file (optional)
        takeaction: Enable remediation (optional)
        model: AI model for remediation (optional)
        output: Output path (optional)

    Returns:
        Command execution result
    """
    args = ["celval", "terraform", "--reqinput", reqinput, "--policy", policy]

    if config:
        args.extend(["--config", config])

    if takeaction:
        args.append("--takeaction")

    if model:
        args.extend(["--model", model])

    if output:
        args.extend(["--output", output])

    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Cue Validation and Generation Tools
# ============================================================================

@app.tool()
async def cue_validate_generate(
    reqinput: str = Field(..., description="Input manifest file (JSON/YAML) or URL"),
    resource: str = Field(..., description="Top-level label for Cue definition"),
    policy: str = Field(..., description="Directory containing cue.mod and definitions"),
    output: str | None = Field(default=None, description="Directory path to write output"),
    verbose: bool = Field(default=False, description="Enable verbose logging")
) -> str:
    """
    Validate and generate Kubernetes manifests using Cue definitions.

    Validates input manifests against Cue definitions and generates complete
    manifests with defaults and constraints. Supports local files and GitHub URLs.

    Args:
        reqinput: Input manifest file or URL
        resource: Top-level Cue definition label
        policy: Policy directory path
        output: Output directory (optional)
        verbose: Enable verbose output (optional)

    Returns:
        Command execution result
    """
    args = ["cue", "--reqinput", reqinput, "--resource", resource, "--policy", policy]

    if output:
        args.extend(["--output", output])

    if verbose:
        args.append("--verbose")

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def cuemod_init(
    tool: str = Field(
        ...,
        description=(
            "Tool to create workspace for (e.g., k8s:latest, argocd:latest, tektoncd:latest)"
        )
    ),
    credentials: str | None = Field(default=None, description="OCI registry credentials"),
    key: str | None = Field(
        default=None, description="Cosign public key for artifact verification"
    )
) -> str:
    """
    Initialize Cue workspace for policy development.

    Creates the necessary directory structure and downloads required dependencies
    for working with Cue validation. Supports Kubernetes, ArgoCD, TektonCD,
    Crossplane, and Cluster API.

    Args:
        tool: Tool identifier (e.g., k8s:latest)
        credentials: Registry credentials (optional)
        key: Cosign public key (optional)

    Returns:
        Command execution result
    """
    args = ["cuemod", "init", "--tool", tool]

    if credentials:
        args.extend(["--credentials", credentials])

    if key:
        args.extend(["--key", key])

    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Regex Validation Tools
# ============================================================================

@app.tool()
async def regex_validate(
    reqinput: str = Field(..., description="Input file to validate (JSON/YAML)"),
    policy: str = Field(..., description="Path/URL to regex policy file (YAML)")
) -> str:
    """
    Validate resource files using regex pattern matching.

    Validates configuration files against regex patterns defined in a policy file.
    Useful for simple pattern-based validation rules.

    Args:
        reqinput: Input file path/URL
        policy: Regex policy file path/URL

    Returns:
        Command execution result
    """
    args = ["regex", "--reqinput", reqinput, "--policy", policy]
    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# GenAI Tools
# ============================================================================

@app.tool()
async def genai_generate(
    prompt: str = Field(..., description="User prompt for IaC generation"),
    model: str = Field(..., description="AI model to use (e.g., GPT4, Ollama)"),
    output: str = Field(..., description="Path to output file"),
    endpoint: str | None = Field(default=None, description="LLM endpoint URL"),
    assistant: str | None = Field(default=None, description="Assistant identifier"),
    user_system_prompt: str | None = Field(
        default=None, description="Custom system prompt (only if assistant='user')"
    ),
    config: str | None = Field(default=None, description="Path to config file (YAML)")
) -> str:
    """
    Generate secure Infrastructure as Code using AI.

    Interacts with LLM backends (OpenAI, Llama3, etc.) to generate secure
    IaC configurations based on user prompts.

    Args:
        prompt: User prompt describing desired IaC
        model: AI model identifier
        output: Output file path
        endpoint: LLM endpoint (optional)
        assistant: Assistant identifier (optional)
        user_system_prompt: Custom system prompt (optional)
        config: Config file path (optional)

    Returns:
        Command execution result
    """
    args = ["genai", "--prompt", prompt, "--model", model, "--output", output]

    if endpoint:
        args.extend(["--endpoint", endpoint])

    if assistant:
        args.extend(["--assistant", assistant])

    if user_system_prompt:
        args.extend(["--user-system-prompt", user_system_prompt])

    if config:
        args.extend(["--config", config])

    result = await run_genval_command(args)
    return format_result(result)


@app.tool()
async def genai_init() -> str:
    """
    Initialize GenAI configurations.

    Downloads necessary resources and sets up the environment for GenAI
    functionality. This should be run before using genai_generate.

    Returns:
        Command execution result
    """
    args = ["genai", "init"]
    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Utility Tools
# ============================================================================

@app.tool()
async def show_json(
    reqinput: str = Field(..., description="Dockerfile or .tf file path/URL")
) -> str:
    """
    Display JSON representation of Dockerfile or Terraform files.

    Converts Dockerfiles and .tf files to JSON format for policy development
    and debugging. This is useful for understanding the structure when writing
    Rego or CEL policies.

    Args:
        reqinput: Dockerfile or .tf file path/URL

    Returns:
        JSON representation of the file
    """
    args = ["showJSON", "--reqinput", reqinput]
    result = await run_genval_command(args)
    return format_result(result)


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Run the MCP server in STDIO mode."""
    logger.info("Starting Genval MCP Server...")
    app.run()


if __name__ == "__main__":
    main()
