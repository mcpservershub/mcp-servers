"""
MCP Server for OpenGrep (with pre-flight FS checks)
Installable via uvx: `uvx install mcp-opengrep`
"""

import logging
import subprocess
import shutil
import os
from pathlib import Path
from typing import Sequence, Optional
from enum import Enum

from pydantic import BaseModel
from mcp.server import Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    ClientCapabilities,
    RootsCapability,
    Tool,
    TextContent,
    ListRootsResult,
)
import argparse
import sys


class ValidateRules(BaseModel):
    """Validate a rules file or directory with OpenGrep"""

    rules_path: str


class ScanCode(BaseModel):
    """Scan code with OpenGrep, emit SARIF output, and optionally apply a config"""

    rules_path: str
    code_path: str
    sarif_output: Optional[str] = "results.sarif"
    config: Optional[str] = None  # e.g. 'p/python'


class OpenGrepTools(str, Enum):
    VALIDATE = "opengrep_validate"
    SCAN = "opengrep_scan"


def expand_path(path_str: str) -> Path:
    """Expand environment variables and user home directory in path"""
    # First expand environment variables
    expanded = os.path.expandvars(path_str)
    # Then expand user home directory (~)
    expanded = os.path.expanduser(expanded)
    return Path(expanded).resolve()


def check_opengrep_installed() -> None:
    """Ensure `opengrep` is available on PATH"""
    if shutil.which("opengrep") is None:
        raise RuntimeError(
            "opengrep CLI not found. Please install it from https://github.com/semgrep/opengrep and ensure it's on your PATH."
        )


def validate_rules(rules_path: str) -> str:
    """Run `opengrep validate` on the given path with existence check"""
    rp = expand_path(rules_path)
    if not rp.exists():
        raise RuntimeError(f"Rules path does not exist: {rp} (original: {rules_path})")

    cmd = ["opengrep", "validate", str(rp)]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            error_msg = (
                proc.stderr.strip() if proc.stderr else "Unknown validation error"
            )
            raise RuntimeError(f"OpenGrep validation failed:\n{error_msg}")
        return proc.stdout.strip() or "Validation succeeded"
    except subprocess.TimeoutExpired:
        raise RuntimeError("OpenGrep validation timed out after 60 seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to run OpenGrep validation: {e}")


def scan_code(
    rules_path: str,
    code_path: str,
    sarif_output: str = "results.sarif",
    config: Optional[str] = None,
) -> str:
    """Run `opengrep scan` with optional SARIF output and config, with FS pre-checks"""
    # Expand and resolve all paths
    rp = expand_path(rules_path)
    cp = expand_path(code_path)
    op = expand_path(sarif_output)

    # Pre-flight checks
    if not rp.exists():
        raise RuntimeError(f"Rules path does not exist: {rp} (original: {rules_path})")
    if not cp.exists():
        raise RuntimeError(f"Code path does not exist: {cp} (original: {code_path})")

    # Ensure output directory is writable
    out_dir = op.parent
    if not out_dir.exists():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Cannot create output directory {out_dir}: {e}")
    if not os.access(out_dir, os.W_OK):
        raise RuntimeError(f"Output directory is not writable: {out_dir}")

    # Build command following the CLI workflow: opengrep scan -f <rules> <code> --sarif-output <output>
    cmd = ["opengrep", "scan", "-f", str(rp), str(cp), "--sarif-output", str(op)]

    # Add config if provided (note: removing this as per your requirement that it's not needed)
    if config:
        cmd.extend(["--config", config])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # OpenGrep scan might return non-zero even on successful scans with findings
        # Check if SARIF file was created as indicator of success
        if op.exists():
            result_msg = f"SARIF results written to {op}"
            if proc.stdout.strip():
                result_msg += f"\n\nOutput:\n{proc.stdout.strip()}"
            return result_msg
        else:
            error_msg = proc.stderr.strip() if proc.stderr else "Unknown scan error"
            if proc.stdout.strip():
                error_msg += f"\nOutput: {proc.stdout.strip()}"
            raise RuntimeError(
                f"OpenGrep scan failed (no SARIF output created):\n{error_msg}"
            )

    except subprocess.TimeoutExpired:
        raise RuntimeError("OpenGrep scan timed out after 5 minutes")
    except Exception as e:
        raise RuntimeError(f"Failed to run OpenGrep scan: {e}")


async def serve(repository: Path) -> None:
    logger = logging.getLogger(__name__)

    # Ensure OpenGrep CLI is installed
    check_opengrep_installed()

    server = Server("mcp-opengrep")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=OpenGrepTools.VALIDATE,
                description="Validate an OpenGrep rules file or directory",
                inputSchema=ValidateRules.model_json_schema(),
            ),
            Tool(
                name=OpenGrepTools.SCAN,
                description="Scan code using OpenGrep rules with SARIF output. Format: rules_path, code_path, sarif_output",
                inputSchema=ScanCode.model_json_schema(),
            ),
        ]

    async def list_repos() -> Sequence[str]:
        def from_cmd() -> Sequence[str]:
            return [str(repository)]

        async def from_roots() -> Sequence[str]:
            if not isinstance(server.request_context.session, ServerSession):
                return []
            if not server.request_context.session.check_client_capability(
                ClientCapabilities(roots=RootsCapability())
            ):
                return []
            roots: ListRootsResult = await server.request_context.session.list_roots()
            paths = []
            for r in roots.roots:
                p = Path(r.uri.path)
                if p.exists():
                    paths.append(str(p))
            return paths

        roots = await from_roots()
        return roots + from_cmd()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == OpenGrepTools.VALIDATE:
                rules_path = arguments.get("rules_path")
                if not rules_path:
                    raise ValueError("rules_path is required")
                out = validate_rules(rules_path)
                return [TextContent(type="text", text=out)]

            if name == OpenGrepTools.SCAN:
                rules_path = arguments.get("rules_path")
                code_path = arguments.get("code_path")
                sarif_output = arguments.get("sarif_output", "results.sarif")
                config = arguments.get("config")

                if not rules_path:
                    raise ValueError("rules_path is required")
                if not code_path:
                    raise ValueError("code_path is required")

                out = scan_code(rules_path, code_path, sarif_output, config)
                return [TextContent(type="text", text=out)]

            raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


def main():
    """Entry point for console_scripts"""
    parser = argparse.ArgumentParser(
        description="Start MCP OpenGrep server with a repository path."
    )
    parser.add_argument(
        "repository",
        nargs="?",
        default=".",
        type=str,
        help="Path to the repository (CWD if omitted)",
    )
    args = parser.parse_args()

    repo_arg = Path(args.repository)
    if not repo_arg.exists():
        print(f"Error: repository path '{repo_arg}' does not exist.")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)
    try:
        import asyncio

        asyncio.run(serve(repo_arg))
    except RuntimeError as e:
        print(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
