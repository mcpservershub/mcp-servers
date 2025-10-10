#!/usr/bin/env python3
"""Cosign MCP Server - A Model Context Protocol server for interacting with Cosign CLI."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP

# Initialize FastMCP server
mcp = FastMCP("cosign-mcp")


async def _run_cosign_verify(cmd: List[str], output_file: str, description: str) -> str:
    """Execute cosign verify command and write JSON output to file."""
    try:
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        # Prepare output based on return code
        if result.returncode == 0:
            # Success case - parse the JSON output from stdout
            # Remove any non-JSON content before the JSON array
            stdout_str = stdout.decode('utf-8', errors='replace')
            # Find the start of JSON array
            json_start = stdout_str.find('[')
            if json_start != -1:
                json_str = stdout_str[json_start:]
                try:
                    verification_bundle = json.loads(json_str)
                    output_json = {
                        "verified": True,
                        "verificationBundle": verification_bundle
                    }
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    output_json = {
                        "verified": False,
                        "error": "Failed to parse cosign output as JSON"
                    }
            else:
                output_json = {
                    "verified": False,
                    "error": "No JSON output found in cosign response"
                }
        else:
            # Failure case - extract error message from stderr
            error_msg = stderr.decode('utf-8', errors='replace').strip()
            # Find the actual error message (skip TUF messages)
            error_lines = error_msg.split('\n')
            actual_error = None
            for line in error_lines:
                if line.strip() and not line.startswith('setting TUF'):
                    if line.startswith('Error: '):
                        actual_error = line[7:]
                        break
                    elif 'error during command execution:' in line:
                        # Skip this line, it's redundant
                        continue
                    else:
                        # This might be the actual error
                        if actual_error is None:
                            actual_error = line
            
            output_json = {
                "verified": False,
                "error": actual_error or error_msg
            }
        
        # Write JSON to output file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_json, f, indent=2)
        
        # Print verification status to stdout
        verified_status = output_json.get('verified', False)
        print(f"verified: {str(verified_status).lower()}")
        
        return f"Verification completed. Output written to: {output_file}\nVerified: {verified_status}"
        
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        
        # Write error JSON to output file
        output_json = {
            "verified": False,
            "error": error_msg
        }
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_json, f, indent=2)
        
        # Print verification status to stdout
        print(f"verified: false")
        
        return f"Error: {error_msg}\nError details written to: {output_file}"


@mcp.tool()
async def verify_image(
    image_name: str,
    output_file: str,
    certificate_identity_regexp: str = ".@intelops.dev",
    certificate_oidc_issuer_regexp: str = "."
) -> str:
    """
    Verify a container image signature using Cosign.
    
    Args:
        image_name: Container image to verify (e.g., docker.io/example/image:tag)
        output_file: Path to write verification output
        certificate_identity_regexp: Regular expression for certificate identity (default: .@intelops.dev)
        certificate_oidc_issuer_regexp: Regular expression for OIDC issuer (default: .)
    
    Returns:
        Status message with output file location
    """
    cmd = [
        "cosign", "verify", image_name,
        f"--certificate-identity-regexp={certificate_identity_regexp}",
        f"--certificate-oidc-issuer-regexp={certificate_oidc_issuer_regexp}"
    ]
    
    return await _run_cosign_verify(cmd, output_file, f"Verifying image: {image_name}")


@mcp.tool()
async def verify_artifact(
    artifact_name: str,
    output_file: str,
    certificate_identity_regexp: str = ".@intelops.dev",
    certificate_oidc_issuer_regexp: str = "."
) -> str:
    """
    Verify an artifact signature using Cosign.
    
    Args:
        artifact_name: Artifact to verify (file path or URL)
        output_file: Path to write verification output
        certificate_identity_regexp: Regular expression for certificate identity (default: .@intelops.dev)
        certificate_oidc_issuer_regexp: Regular expression for OIDC issuer (default: .)
    
    Returns:
        Status message with output file location
    """
    cmd = [
        "cosign", "verify", artifact_name,
        f"--certificate-identity-regexp={certificate_identity_regexp}",
        f"--certificate-oidc-issuer-regexp={certificate_oidc_issuer_regexp}"
    ]
    
    return await _run_cosign_verify(cmd, output_file, f"Verifying artifact: {artifact_name}")


@mcp.tool()
async def check_version(output_file: str) -> str:
    """
    Check the installed Cosign version.
    
    Args:
        output_file: Path to write version output
    
    Returns:
        Status message with output file location
    """
    cmd = ["cosign", "version"]
    
    try:
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        output = f"Checking Cosign version\n"
        output += f"Command: {' '.join(cmd)}\n"
        output += f"Return code: {result.returncode}\n\n"
        
        if stdout:
            output += "STDOUT:\n"
            output += stdout.decode('utf-8', errors='replace')
            output += "\n"
        
        if stderr:
            output += "STDERR:\n"
            output += stderr.decode('utf-8', errors='replace')
            output += "\n"
        
        # Write to output file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(output)
        
        return f"Command executed. Output written to: {output_file}\nReturn code: {result.returncode}"
        
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        
        # Write error to output file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(f"Checking Cosign version\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Error: {error_msg}\n")
        
        return f"Error: {error_msg}\nError details written to: {output_file}"


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()