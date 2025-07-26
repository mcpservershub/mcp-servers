#!/usr/bin/env python3
"""MCP server for markdownlint - Markdown linting and fixing."""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP("markdownlint-mcp-server")

def setup_logging():
    """Configure logging based on environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

async def run_markdownlint(
    files: List[str],
    config: Optional[str] = None,
    ignore: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
    disable: Optional[List[str]] = None,
    output: Optional[str] = None,
) -> Dict[str, Any]:
    """Run markdownlint with specified options (always --fix), and write logs if requested."""
    # Build command
    cmd: List[str] = ["markdownlint", "--fix"]

    # Map optional arguments to CLI flags
    if config:
        cmd.extend(["--config", config])
    if ignore:
        for pattern in ignore:
            cmd.extend(["--ignore", pattern])
    if rules:
        for rule in rules:
            cmd.extend(["--rules", rule])
    if disable:
        cmd.append("--disable")
        cmd.extend(disable)
        cmd.append("--")

    # Add files (required)
    cmd.extend(files)

    cmd_str = " ".join(cmd)
    logger.info(f"Running markdownlint: {cmd_str}")
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8")
        stderr = stderr_bytes.decode("utf-8")

        result: Dict[str, Any] = {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": cmd_str,
        }

        # If an output path was provided, write stdout to it
        if output:
            try:
                # Ensure directory exists
                Path(output).parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w", encoding="utf-8") as f:
                    f.write(stdout)
                result["output"] = output
                result["output_created"] = True
                logger.info(f"Wrote lint log to {output}")
            except Exception as e:
                result["output"] = output
                result["output_created"] = False
                logger.warning(f"Failed to write lint log to {output}: {e}")

        return result

    except asyncio.TimeoutError:
        return {"success": False, "error": "Command timed out", "command": cmd_str}
    except Exception as e:
        return {"success": False, "error": str(e), "command": cmd_str}

@mcp.tool()
async def lint_files(
    files: List[str],
    config: Optional[str] = None,
    ignore: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
    disable: Optional[List[str]] = None,
    output: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lint markdown files using markdownlint with automatic fixing (always enabled).

    Args:
        files: List of files, directories, or globs to lint (required)
        config: Path to configuration file
        ignore: List of patterns to ignore
        rules: List of custom rule files to include
        disable: List of rules to disable
        output: Path to write lint logs to (optional)

    Returns:
        Dictionary with lint results
    """
    if not files:
        return {"success": False, "error": "No files specified to lint"}

    # Validate and normalize file paths or patterns
    existing: List[str] = []
    for f in files:
        path = Path(f)
        if "*" in f or "?" in f:
            existing.append(f)
        elif path.exists():
            existing.append(str(path.absolute()))
        else:
            logger.warning(f"File or pattern not found: {f}")

    if not existing:
        return {"success": False, "error": "No valid files found to lint"}

    # Delegate to the runner
    return await run_markdownlint(
        files=existing,
        config=config,
        ignore=ignore,
        rules=rules,
        disable=disable,
        output=output,
    )

@mcp.tool()
async def check_version() -> Dict[str, Any]:
    """
    Check the installed version of markdownlint-cli.

    Returns:
        Dictionary with version information
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            "markdownlint --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ,
        )
        stdout, stderr = await proc.communicate()
        return {
            "success": proc.returncode == 0,
            "version": stdout.decode("utf-8").strip(),
            "error": stderr.decode("utf-8").strip() or None,
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to check markdownlint version: {e}"}


def main():
    setup_logging()
    logger.info("Starting markdownlint MCP server")
    try:
        result = subprocess.run(
            "markdownlint --version",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"markdownlint-cli available: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        logger.error(
            "markdownlint-cli is not installed. "
            "Install it with: npm install -g markdownlint-cli"
        )
    mcp.run()

if __name__ == "__main__":
    main()
