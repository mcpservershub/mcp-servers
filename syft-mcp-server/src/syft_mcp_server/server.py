#!/usr/bin/env python3
"""MCP Server for Syft SBOM generator by Anchore."""

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
mcp = FastMCP("syft-mcp-server")

# Debug flag - set via environment variable
DEBUG = os.environ.get("SYFT_MCP_DEBUG", "").lower() == "true"

def debug_log(message: str):
    """Log debug messages to stderr."""
    if DEBUG:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}", file=sys.stderr, flush=True)


async def run_syft_command(
    args: List[str], output_file: Optional[str] = None, timeout: int = 300
) -> Dict[str, Any]:
    """Run a Syft command and return the result.
    
    Args:
        args: Command arguments (should include the full command like ["syft", "alpine:latest"])
        output_file: Path to save output
        timeout: Command timeout in seconds (default: 300s)
    """
    start_time = time.time()
    debug_log(f"Running command: {' '.join(args)}")
    debug_log(f"Timeout: {timeout}s")
    debug_log(f"Output file: {output_file}")
    
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
        debug_log("ERROR: Syft not found in PATH")
        return {
            "success": False,
            "stdout": "",
            "stderr": "Syft not found. Please install Syft first.",
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
async def generate_sbom_from_image(
    image: str,
    output_file: str,
    format: Optional[str] = "spdx-json",
    scope: Optional[str] = "squashed",
) -> str:
    """
    Generate SBOM from a Docker/OCI container image.

    Args:
        image: Container image name (e.g., alpine:latest, ubuntu:22.04)
        output_file: Path to save SBOM
        format: SBOM format (spdx-json, spdx-tag-value, cyclonedx-json, cyclonedx-xml, syft-json, syft-table, syft-text)
        scope: Scope of image layers to catalog (squashed or all-layers)
    """
    debug_log(f"generate_sbom_from_image called: image={image}, output_file={output_file}")
    debug_log(f"Options: format={format}, scope={scope}")
    
    # Build full syft command
    args = ["syft", "scan", image]
    
    # Add output format
    args.extend(["-o", format])
    
    # Add quiet flag to reduce noise
    args.append("-q")
    
    # Add scope flag
    args.extend(["--scope", scope])
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan
    result = await run_syft_command(args, output_file, timeout=180)

    if result["success"]:
        return f"SBOM generated successfully from image. Results saved to: {output_file}"
    else:
        return f"SBOM generation failed: {result['stderr']}"


@mcp.tool()
async def generate_sbom_from_filesystem(
    path: str,
    output_file: str,
    format: Optional[str] = "spdx-json",
    exclude: Optional[str] = None,
) -> str:
    """
    Generate SBOM from a filesystem path (directory or file).

    Args:
        path: Path to scan (directory or file)
        output_file: Path to save SBOM
        format: SBOM format (spdx-json, spdx-tag-value, cyclonedx-json, cyclonedx-xml, syft-json, syft-table, syft-text)
        exclude: Comma-separated list of globs to exclude from scanning
    """
    debug_log(f"generate_sbom_from_filesystem called: path={path}, output_file={output_file}")
    debug_log(f"Options: format={format}, exclude={exclude}")
    
    # Check if path exists
    if not Path(path).exists():
        error_msg = f"Path does not exist: {path}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Build full syft command with dir: prefix
    # Always use dir: prefix for filesystem paths
    args = ["syft", "scan", f"dir:{path}"]
    
    # Add output format
    args.extend(["-o", format])
    
    # Add quiet flag
    args.append("-q")
    
    # Add exclude patterns if specified
    if exclude:
        for pattern in exclude.split(","):
            args.extend(["--exclude", pattern.strip()])
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan
    result = await run_syft_command(args, output_file, timeout=120)

    if result["success"]:
        return f"SBOM generated successfully from filesystem. Results saved to: {output_file}"
    else:
        return f"SBOM generation failed: {result['stderr']}"


@mcp.tool()
async def generate_sbom_from_archive(
    archive_path: str,
    output_file: str,
    format: Optional[str] = "spdx-json",
) -> str:
    """
    Generate SBOM from an archive file (tar, zip, etc.).

    Args:
        archive_path: Path to archive file
        output_file: Path to save SBOM
        format: SBOM format (spdx-json, spdx-tag-value, cyclonedx-json, cyclonedx-xml, syft-json, syft-table, syft-text)
    """
    debug_log(f"generate_sbom_from_archive called: archive_path={archive_path}, output_file={output_file}")
    debug_log(f"Options: format={format}")
    
    # Check if archive exists
    if not Path(archive_path).exists():
        error_msg = f"Archive file does not exist: {archive_path}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Build full syft command
    args = ["syft", "scan", archive_path]
    
    # Add output format
    args.extend(["-o", format])
    
    # Add quiet flag
    args.append("-q")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan
    result = await run_syft_command(args, output_file, timeout=120)

    if result["success"]:
        return f"SBOM generated successfully from archive. Results saved to: {output_file}"
    else:
        return f"SBOM generation failed: {result['stderr']}"


@mcp.tool()
async def convert_sbom(
    input_file: str,
    output_file: str,
    output_format: str,
) -> str:
    """
    Convert between SBOM formats.

    Args:
        input_file: Path to input SBOM file
        output_file: Path to save converted SBOM
        output_format: Target format (spdx-json, spdx-tag-value, cyclonedx-json, cyclonedx-xml, syft-json)
    """
    debug_log(f"convert_sbom called: input_file={input_file}, output_file={output_file}")
    debug_log(f"Options: output_format={output_format}")
    
    # Check if input file exists
    if not Path(input_file).exists():
        error_msg = f"Input SBOM file does not exist: {input_file}"
        debug_log(f"ERROR: {error_msg}")
        return error_msg
    
    # Build full syft command for conversion
    args = ["syft", "convert", input_file]
    
    # Add output format
    args.extend(["-o", output_format])
    
    # Add quiet flag
    args.append("-q")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the conversion
    result = await run_syft_command(args, output_file, timeout=60)

    if result["success"]:
        return f"SBOM converted successfully. Results saved to: {output_file}"
    else:
        return f"SBOM conversion failed: {result['stderr']}"


@mcp.tool()
async def list_packages(
    target: str,
    output_file: str,
    format: Optional[str] = "syft-table",
) -> str:
    """
    List all packages found in a target (simpler output than full SBOM).

    Args:
        target: Target to scan (image, directory, file, or archive)
        output_file: Path to save package list
        format: Output format (syft-table, syft-text, syft-json)
    """
    debug_log(f"list_packages called: target={target}, output_file={output_file}")
    debug_log(f"Options: format={format}")
    
    # Build full syft command with appropriate prefix
    # Determine if target is a path, image, or archive
    if Path(target).exists():
        if Path(target).is_dir():
            target = f"dir:{target}"
        else:
            # Could be a file or archive - Syft will auto-detect
            target = f"file:{target}"
    # Otherwise assume it's an image name
    
    args = ["syft", "scan", target]
    
    # Add output format (table format for simple package listing)
    args.extend(["-o", format])
    
    # Add quiet flag
    args.append("-q")
    
    debug_log(f"Final command: {' '.join(args)}")

    # Run the scan
    result = await run_syft_command(args, output_file, timeout=120)

    if result["success"]:
        return f"Package list generated successfully. Results saved to: {output_file}"
    else:
        return f"Package listing failed: {result['stderr']}"


@mcp.tool()
async def check_syft_status() -> str:
    """
    Check Syft installation status and version.
    """
    try:
        # Use shell command for better container compatibility
        result = await asyncio.create_subprocess_shell(
            "syft --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            version_info = stdout.decode("utf-8").strip()
            return f"Syft is installed and working:\n{version_info}"
        else:
            return f"Syft check failed: {stderr.decode('utf-8')}"
    except FileNotFoundError:
        return "Syft is not installed or not in PATH"
    except Exception as e:
        return f"Error checking Syft status: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    import sys

    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()