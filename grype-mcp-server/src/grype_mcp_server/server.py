#!/usr/bin/env python3
"""MCP Server for Grype vulnerability scanner by Anchore."""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP
from mcp.types import TextContent

# Initialize the MCP server
mcp = FastMCP("grype-mcp-server")

# Debug flag - set via environment variable
DEBUG = os.environ.get("GRYPE_MCP_DEBUG", "").lower() == "true"

def debug_log(message: str):
    """Log debug messages to stderr."""
    if DEBUG:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}", file=sys.stderr, flush=True)


async def run_grype_command(
    args: List[str], output_file: Optional[str] = None, timeout: int = 300
) -> Dict[str, Any]:
    """Run a Grype command and return the result.
    
    Args:
        args: Command arguments (should include the full command like ["grype", "alpine:latest"])
        output_file: Path to save output
        timeout: Command timeout in seconds (default: 300s)
    """
    start_time = time.time()
    debug_log(f"Running command: {' '.join(args)}")
    debug_log(f"Timeout: {timeout}s")
    debug_log(f"Output file: {output_file}")
    
    try:
        # Run the command with shell=True for better container compatibility
        # Properly quote arguments that might contain special characters
        quoted_args = []
        for arg in args:
            if '*' in arg or '?' in arg or ' ' in arg:
                quoted_args.append(f'"{arg}"')
            else:
                quoted_args.append(arg)
        cmd_str = ' '.join(quoted_args)
        debug_log(f"Shell command: {cmd_str}")
        result = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ
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

        # With --file flag, Grype writes directly to the file
        # Check if output file was created
        if output_file and "--file" in args:
            if Path(output_file).exists():
                file_size = Path(output_file).stat().st_size
                debug_log(f"Output file created by Grype: {output_file} ({file_size} bytes)")
            else:
                debug_log(f"WARNING: Output file not created by Grype: {output_file}")

        return {
            "success": result.returncode == 0,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "returncode": result.returncode,
            "output_file": output_file,
        }
    except FileNotFoundError:
        debug_log("ERROR: Grype not found in PATH")
        return {
            "success": False,
            "stdout": "",
            "stderr": "Grype not found. Please install Grype first.",
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
async def scan_docker_image(
    image: str,
    output_file: str,
    format: str = "table",
    scope: str = "squashed",
    only_fixed: bool = False,
    fail_on: Optional[str] = None,
) -> str:
    """
    Scan a Docker image for vulnerabilities.

    Args:
        image: Docker image name (e.g., alpine:latest, ubuntu:22.04)
        output_file: Path to save scan results
        format: Output format (table, json, cyclonedx, cyclonedx-json, sarif, template)
        scope: Scope of image layers to include (squashed, all-layers, deep-squashed)
        only_fixed: Only show vulnerabilities with known fixes
        fail_on: Set exit code to 1 if vulnerability >= severity (negligible, low, medium, high, critical)
    """
    debug_log(f"scan_docker_image called: image={image}, output_file={output_file}")
    debug_log(f"Options: format={format}, scope={scope}, only_fixed={only_fixed}, fail_on={fail_on}")
    
    # Build full grype command
    # Docker images don't need a prefix, but check if one was provided
    if image.startswith(('docker:', 'registry:', 'docker-archive:', 'oci-archive:', 'oci-dir:', 'podman:')):
        # Image has an explicit source prefix, use as-is
        args = ["grype", image]
        debug_log(f"Using image with explicit source: {image}")
    else:
        # Standard image reference (no prefix needed)
        args = ["grype", image]
        debug_log(f"Using standard image reference: {image}")
    
    # Add output format
    if format:
        args.extend(["-o", format])
    
    # Add output file flag
    if output_file:
        args.extend(["--file", output_file])
    
    # Add scope flag only if specified and not default
    if scope and scope != "squashed":
        args.extend(["--scope", scope])
    
    # Add fail-on severity if specified
    if fail_on:
        args.extend(["--fail-on", fail_on])
    
    # Add only-fixed flag if requested
    if only_fixed:
        args.append("--only-fixed")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan with increased timeout for container environments
    result = await run_grype_command(args, output_file, timeout=300)

    if result["success"]:
        # Check if output was written
        if output_file and Path(output_file).exists():
            file_size = Path(output_file).stat().st_size
            return f"Docker image scan completed successfully. Results saved to: {output_file} ({file_size} bytes)"
        else:
            return f"Docker image scan completed but no output file was created"
    else:
        error_msg = result['stderr'] if result['stderr'] else f"Command failed with exit code {result['returncode']}"
        debug_log(f"Scan failed - return code: {result['returncode']}, stderr: {result['stderr']}, stdout length: {len(result['stdout'])}")
        return f"Docker image scan failed: {error_msg}"


@mcp.tool()
async def scan_filesystem(
    path: str,
    output_file: str,
    format: str = "table",
    exclude: Optional[str] = None,
    only_fixed: bool = False,
    fail_on: Optional[str] = None,
) -> str:
    """
    Scan a local filesystem path for vulnerabilities.

    Args:
        path: Path to scan (directory or file)
        output_file: Path to save scan results
        format: Output format (table, json, cyclonedx, cyclonedx-json, sarif, template)
        exclude: Comma-separated list of glob patterns to exclude from scanning
        only_fixed: Only show vulnerabilities with known fixes
        fail_on: Set exit code to 1 if vulnerability >= severity (negligible, low, medium, high, critical)
    """
    debug_log(f"scan_filesystem called: path={path}, output_file={output_file}")
    debug_log(f"Options: format={format}, exclude={exclude}, only_fixed={only_fixed}, fail_on={fail_on}")
    
    # Strip any Grype prefix for path validation
    actual_path = path
    if path.startswith(('dir:', 'file:')):
        actual_path = path.split(':', 1)[1]
        debug_log(f"Stripped prefix from path: {path} -> {actual_path}")
    
    # Check if path exists
    if not Path(actual_path).exists():
        error_msg = f"Path does not exist: {actual_path}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Log path info
    path_obj = Path(actual_path)
    if path_obj.is_dir():
        debug_log(f"Scanning directory: {actual_path} (contains {len(list(path_obj.iterdir()))} items)")
    else:
        debug_log(f"Scanning file: {actual_path} ({path_obj.stat().st_size} bytes)")
    
    # Build full grype command with dir: prefix
    # Check if path already has a Grype prefix
    if path.startswith(('dir:', 'file:', 'registry:', 'docker:', 'docker-archive:', 'oci-archive:', 'oci-dir:', 'singularity:')):
        # Path already has a prefix, use as-is
        args = ["grype", path]
        debug_log(f"Using path with existing prefix: {path}")
    else:
        # Add dir: prefix for filesystem paths
        args = ["grype", f"dir:{path}"]
        debug_log(f"Added dir: prefix to path: dir:{path}")
    
    # Add output format
    if format:
        args.extend(["-o", format])
    
    # Add output file flag
    if output_file:
        args.extend(["--file", output_file])
    
    # Add exclude patterns if specified
    if exclude:
        for pattern in exclude.split(","):
            pattern = pattern.strip()
            # Grype requires exclusion patterns to start with ./, */, or **/
            if not pattern.startswith(('./', '*/', '**/')):
                if '/' not in pattern:
                    # It's a filename pattern, make it recursive
                    pattern = f"**/{pattern}"
                else:
                    # It's a path, make it relative
                    pattern = f"./{pattern}"
            args.extend(["--exclude", pattern])
    
    # Add fail-on severity if specified
    if fail_on:
        args.extend(["--fail-on", fail_on])
    
    # Add only-fixed flag if requested
    if only_fixed:
        args.append("--only-fixed")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan with increased timeout for container environments
    result = await run_grype_command(args, output_file, timeout=300)

    if result["success"]:
        # Check if output was written
        if output_file and Path(output_file).exists():
            file_size = Path(output_file).stat().st_size
            return f"Filesystem scan completed successfully. Results saved to: {output_file} ({file_size} bytes)"
        else:
            return f"Filesystem scan completed but no output file was created"
    else:
        error_msg = result['stderr'] if result['stderr'] else f"Command failed with exit code {result['returncode']}"
        debug_log(f"Scan failed - return code: {result['returncode']}, stderr: {result['stderr']}, stdout length: {len(result['stdout'])}")
        return f"Filesystem scan failed: {error_msg}"


@mcp.tool()
async def scan_sbom(
    sbom_file: str,
    output_file: str,
    format: str = "table",
    only_fixed: bool = False,
    fail_on: Optional[str] = None,
) -> str:
    """
    Scan an SBOM (Software Bill of Materials) file for vulnerabilities.

    Args:
        sbom_file: Path to SBOM file (supports Syft, SPDX, and CycloneDX formats)
        output_file: Path to save scan results
        format: Output format (table, json, cyclonedx, cyclonedx-json, sarif, template)
        only_fixed: Only show vulnerabilities with known fixes
        fail_on: Set exit code to 1 if vulnerability >= severity (negligible, low, medium, high, critical)
    """
    debug_log(f"scan_sbom called: sbom_file={sbom_file}, output_file={output_file}")
    debug_log(f"Options: format={format}, only_fixed={only_fixed}, fail_on={fail_on}")
    
    # Strip any Grype prefix for path validation
    actual_sbom_file = sbom_file
    if sbom_file.startswith('sbom:'):
        actual_sbom_file = sbom_file.split(':', 1)[1]
        debug_log(f"Stripped prefix from SBOM path: {sbom_file} -> {actual_sbom_file}")
    
    # Check if SBOM file exists
    if not Path(actual_sbom_file).exists():
        error_msg = f"SBOM file does not exist: {actual_sbom_file}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Log SBOM file info
    sbom_path = Path(actual_sbom_file)
    debug_log(f"SBOM file size: {sbom_path.stat().st_size} bytes")
    
    # Build full grype command with sbom: prefix
    # Check if path already has a Grype prefix
    if sbom_file.startswith(('sbom:', 'dir:', 'file:', 'registry:', 'docker:')):
        # Path already has a prefix, use as-is
        args = ["grype", sbom_file]
        debug_log(f"Using SBOM path with existing prefix: {sbom_file}")
    else:
        # Add sbom: prefix
        args = ["grype", f"sbom:{sbom_file}"]
        debug_log(f"Added sbom: prefix to path: sbom:{sbom_file}")
    
    # Add output format
    if format:
        args.extend(["-o", format])
    
    # Add output file flag
    if output_file:
        args.extend(["--file", output_file])
    
    # Add fail-on severity if specified
    if fail_on:
        args.extend(["--fail-on", fail_on])
    
    # Add only-fixed flag if requested
    if only_fixed:
        args.append("--only-fixed")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan with increased timeout for container environments
    result = await run_grype_command(args, output_file, timeout=300)

    if result["success"]:
        # Check if output was written
        if output_file and Path(output_file).exists():
            file_size = Path(output_file).stat().st_size
            return f"SBOM scan completed successfully. Results saved to: {output_file} ({file_size} bytes)"
        else:
            return f"SBOM scan completed but no output file was created"
    else:
        error_msg = result['stderr'] if result['stderr'] else f"Command failed with exit code {result['returncode']}"
        debug_log(f"Scan failed - return code: {result['returncode']}, stderr: {result['stderr']}, stdout length: {len(result['stdout'])}")
        return f"SBOM scan failed: {error_msg}"



@mcp.tool()
async def update_database() -> str:
    """
    Update Grype's vulnerability database.
    """
    debug_log("update_database called")
    
    # Build command to update database
    args = ["grype", "db", "update"]
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the update
    result = await run_grype_command(args, timeout=300)

    if result["success"]:
        return f"Grype database updated successfully:\n{result['stdout']}"
    else:
        return f"Database update failed: {result['stderr']}"


@mcp.tool()
async def check_database_status() -> str:
    """
    Check Grype's vulnerability database status.
    """
    debug_log("check_database_status called")
    
    # Build command to check database status
    args = ["grype", "db", "status"]
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the check
    result = await run_grype_command(args, timeout=30)

    if result["success"]:
        return f"Grype database status:\n{result['stdout']}"
    else:
        return f"Database status check failed: {result['stderr']}"


@mcp.tool()
async def test_simple_scan() -> str:
    """
    Test a simple Grype scan with minimal parameters.
    """
    debug_log("test_simple_scan called")
    
    # Build minimal command
    args = ["grype", "alpine:latest"]
    
    debug_log(f"Running test command: {' '.join(args)}")
    
    try:
        # Run the command with shell=True for better container compatibility
        cmd_str = ' '.join(args)
        result = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ
        )
        debug_log(f"Process started with PID: {result.pid}")
        
        try:
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=120
            )
            debug_log(f"Command completed")
        except asyncio.TimeoutError:
            debug_log(f"Command timed out")
            result.terminate()
            await result.wait()
            return "Test scan timed out after 120 seconds"

        # Decode output
        stdout_text = stdout.decode("utf-8")
        stderr_text = stderr.decode("utf-8")
        
        debug_log(f"Return code: {result.returncode}")
        debug_log(f"Stdout length: {len(stdout_text)} chars")
        debug_log(f"Stderr length: {len(stderr_text)} chars")
        
        if result.returncode == 0:
            # Count vulnerabilities
            lines = stdout_text.strip().split('\n')
            vuln_count = max(0, len(lines) - 1)  # Subtract header
            return f"Test scan succeeded! Found approximately {vuln_count} vulnerability entries."
        else:
            return f"Test scan failed with return code {result.returncode}: {stderr_text[:500]}"
            
    except Exception as e:
        debug_log(f"ERROR: Exception during test scan: {type(e).__name__}: {str(e)}")
        return f"Test scan error: {type(e).__name__}: {str(e)}"


@mcp.tool()
async def check_grype_status() -> str:
    """
    Check Grype installation status and version.
    """
    debug_log("check_grype_status called")
    try:
        # Use shell command for better container compatibility
        result = await asyncio.create_subprocess_shell(
            "grype --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            version_info = stdout.decode("utf-8").strip()
            debug_log(f"Grype version: {version_info}")
            return f"Grype is installed and working:\n{version_info}"
        else:
            error_msg = stderr.decode('utf-8')
            debug_log(f"Grype check failed: {error_msg}")
            return f"Grype check failed: {error_msg}"
    except FileNotFoundError:
        debug_log("ERROR: Grype not found")
        return "Grype is not installed or not in PATH"
    except Exception as e:
        debug_log(f"ERROR: Exception checking Grype: {str(e)}")
        return f"Error checking Grype status: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    import sys

    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
