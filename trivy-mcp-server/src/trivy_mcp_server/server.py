#!/usr/bin/env python3
"""MCP Server for Trivy vulnerability scanner."""

import asyncio
import json
import os
import subprocess
import tempfile
import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP
from mcp.types import TextContent

# Initialize the MCP server
mcp = FastMCP("trivy-mcp-server")

# Debug flag - set via environment variable
DEBUG = os.environ.get("TRIVY_MCP_DEBUG", "").lower() == "true"

def debug_log(message: str):
    """Log debug messages to stderr."""
    if DEBUG:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}", file=sys.stderr, flush=True)


async def run_trivy_command(
    args: List[str], output_file: Optional[str] = None, timeout: int = 300
) -> Dict[str, Any]:
    """Run a Trivy command and return the result.
    
    Args:
        args: Command arguments (should include the full command like ["trivy", "fs", ...])
        output_file: Path to save output
        timeout: Command timeout in seconds (default: 300s)
    """
    start_time = time.time()
    debug_log(f"Running command: {' '.join(args)}")
    debug_log(f"Timeout: {timeout}s")
    debug_log(f"Output file: {output_file}")
    
    try:
        # Run the command with shell=True for better container compatibility
        # This helps when running inside Docker containers
        cmd_str = ' '.join(args)
        result = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "TRIVY_TIMEOUT": f"{timeout}s"}
        )
        debug_log(f"Process started with PID: {result.pid}")
        
        try:
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=timeout
            )
            elapsed = time.time() - start_time
            debug_log(f"Command completed in {elapsed:.2f}s")
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            debug_log(f"Command timed out after {elapsed:.2f}s")
            result.terminate()
            await result.wait()
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "output_file": None,
            }

        # Decode output
        stdout_text = stdout.decode("utf-8")
        stderr_text = stderr.decode("utf-8")
        
        debug_log(f"Return code: {result.returncode}")
        debug_log(f"Stdout length: {len(stdout_text)} chars")
        debug_log(f"Stderr length: {len(stderr_text)} chars")
        if stderr_text:
            debug_log(f"Stderr preview: {stderr_text[:200]}...")

        # If output file is specified, write the output
        if output_file and stdout_text:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(stdout_text)
            debug_log(f"Output written to: {output_file}")

        return {
            "success": result.returncode == 0,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "returncode": result.returncode,
            "output_file": output_file,
        }
    except FileNotFoundError:
        debug_log("ERROR: Trivy not found in PATH")
        return {
            "success": False,
            "stdout": "",
            "stderr": "Trivy not found. Please install Trivy first.",
            "returncode": -1,
            "output_file": None,
        }
    except Exception as e:
        debug_log(f"ERROR: Unexpected exception: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "output_file": None,
        }


@mcp.tool()
async def scan_filesystem(
    path: str,
    output_file: str,
    severity: Optional[str] = "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
    format: Optional[str] = "table",
) -> str:
    """
    Scan a local filesystem path for vulnerabilities.

    Args:
        path: Path to scan
        output_file: Path to save scan results
        severity: Comma-separated list of severities to include (default: UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
        format: Output format (table, json, sarif, github, gitlab, cyclonedx, spdx)
    """
    debug_log(f"scan_filesystem called: path={path}, output_file={output_file}")
    debug_log(f"Options: severity={severity}, format={format}")
    
    # Check if path exists
    if not Path(path).exists():
        error_msg = f"Path does not exist: {path}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Build full trivy command
    args = ["trivy", "fs"]
    
    # Add format flag
    args.extend(["--format", format])
    
    # Add no-progress flag to prevent interactive output
    args.append("--no-progress")
    
    # Add quiet flag to reduce output
    args.append("--quiet")
    
    # Only scan for vulnerabilities (not secrets/misconfig) to speed up
    args.extend(["--scanners", "vuln"])
    
    # Skip common directories that don't have dependencies
    args.extend(["--skip-dirs", "node_modules,vendor,.git,test,tests,__pycache__,.venv,venv"])

    # Add severity filter
    args.extend(["--severity", severity])

    # Add the path to scan
    args.append(path)
    
    debug_log(f"Final command: {' '.join(args)}")

    # Use reasonable timeout for filesystem scans
    result = await run_trivy_command(args, output_file, timeout=120)

    if result["success"]:
        return f"Filesystem scan completed successfully. Results saved to: {output_file}"
    else:
        return f"Filesystem scan failed: {result['stderr']}"


@mcp.tool()
async def scan_github_repo(
    repo_url: str,
    output_file: str,
    branch: Optional[str] = None,
    severity: Optional[str] = "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
    format: Optional[str] = "table",
) -> str:
    """
    Scan a remote GitHub repository for vulnerabilities.

    Args:
        repo_url: GitHub repository URL
        output_file: Path to save scan results
        branch: Branch to scan (optional)
        severity: Comma-separated list of severities to include (default: UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
        format: Output format (table, json, sarif, github, gitlab, cyclonedx, spdx)
    """
    # Build full trivy command
    args = ["trivy", "repo", "--format", format]
    
    # Add performance flags
    args.append("--no-progress")
    args.append("--quiet")
    
    # Add severity filter
    args.extend(["--severity", severity])

    if branch:
        args.extend(["--branch", branch])

    args.append(repo_url)

    result = await run_trivy_command(args, output_file)

    if result["success"]:
        return f"Repository scan completed successfully. Results saved to: {output_file}"
    else:
        return f"Repository scan failed: {result['stderr']}"


@mcp.tool()
async def scan_docker_image(
    image: str,
    output_file: str,
    severity: Optional[str] = "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
    format: Optional[str] = "table",
) -> str:
    """
    Scan a Docker image for vulnerabilities.

    Args:
        image: Docker image name (local or remote)
        output_file: Path to save scan results
        severity: Comma-separated list of severities to include (default: UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
        format: Output format (table, json, sarif, github, gitlab, cyclonedx, spdx)
    """
    # Build full trivy command
    args = ["trivy", "image", "--format", format]
    
    # Add performance flags
    args.append("--no-progress")
    args.append("--quiet")
    
    # Add severity filter
    args.extend(["--severity", severity])

    args.append(image)

    result = await run_trivy_command(args, output_file)

    if result["success"]:
        return f"Docker image scan completed successfully. Results saved to: {output_file}"
    else:
        return f"Docker image scan failed: {result['stderr']}"


@mcp.tool()
async def scan_config(
    path: str,
    output_file: str,
    policy_type: Optional[str] = None,
    format: Optional[str] = "table",
) -> str:
    """
    Scan for IaC misconfigurations.

    Args:
        path: Path to scan for misconfigurations
        output_file: Path to save scan results
        policy_type: Type of policies to check (kubernetes, dockerfile, terraform, cloudformation)
        format: Output format (table, json, sarif, github, gitlab)
    """
    # Build full trivy command
    args = ["trivy", "config", "--format", format]

    if policy_type:
        args.extend(["--policy-type", policy_type])

    args.append(path)

    result = await run_trivy_command(args, output_file)

    if result["success"]:
        return f"Configuration scan completed successfully. Results saved to: {output_file}"
    else:
        return f"Configuration scan failed: {result['stderr']}"


@mcp.tool()
async def scan_sbom(
    target: str,
    output_file: str,
    sbom_format: Optional[str] = "cyclonedx",
) -> str:
    """
    Generate or scan SBOM (Software Bill of Materials).

    Args:
        target: Target to generate SBOM for (filesystem path, image, or repo)
        output_file: Path to save SBOM
        sbom_format: SBOM format (cyclonedx, spdx, spdx-json)
    """
    # Determine target type
    if target.startswith("http://") or target.startswith("https://"):
        target_type = "repo"
    elif ":" in target and "/" in target:
        target_type = "image"
    else:
        target_type = "fs"

    # Build full trivy command
    args = ["trivy", target_type, "--format", sbom_format, "--list-all-pkgs"]
    args.append(target)

    result = await run_trivy_command(args, output_file)

    if result["success"]:
        return f"SBOM generation completed successfully. Results saved to: {output_file}"
    else:
        return f"SBOM generation failed: {result['stderr']}"


@mcp.tool()
async def list_vulnerabilities(
    output_file: str,
    db_type: Optional[str] = "vulnerability",
) -> str:
    """
    Get information about the vulnerability database.

    Args:
        output_file: Path to save database information
        db_type: Database type (vulnerability, misconfiguration)
    """
    # First, check database status
    args = ["trivy", "--version"]
    result = await run_trivy_command(args)

    if not result["success"]:
        return f"Failed to get Trivy version: {result['stderr']}"

    # Get database info
    db_info = {
        "trivy_version": result["stdout"].strip(),
        "db_type": db_type,
        "note": "Run 'trivy image --download-db-only' to update the vulnerability database",
    }

    # Save to output file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(db_info, indent=2))

    return f"Database information saved to: {output_file}"


@mcp.tool()
async def check_trivy_status() -> str:
    """
    Check Trivy installation status and version.
    """
    try:
        # Use shell command for better container compatibility
        result = await asyncio.create_subprocess_shell(
            "trivy --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            version_info = stdout.decode("utf-8").strip()
            return f"Trivy is installed and working:\n{version_info}"
        else:
            return f"Trivy check failed: {stderr.decode('utf-8')}"
    except FileNotFoundError:
        return "Trivy is not installed or not in PATH"
    except Exception as e:
        return f"Error checking Trivy status: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    import sys

    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()