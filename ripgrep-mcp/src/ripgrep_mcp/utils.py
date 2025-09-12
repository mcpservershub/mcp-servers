"""Utility functions for ripgrep MCP server."""

import asyncio
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_ripgrep_binary() -> str:
    """Get the path to ripgrep binary."""
    # First check environment variable
    rg_path = os.environ.get("RG_BINARY_PATH")
    if rg_path and os.path.exists(rg_path) and os.access(rg_path, os.X_OK):
        return rg_path
    
    # Check standard locations
    for path in ["/usr/bin/rg", "/usr/local/bin/rg", shutil.which("rg")]:
        if path and os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    raise RuntimeError("ripgrep (rg) binary not found. Please install ripgrep.")


async def run_ripgrep(args: List[str], timeout: int = 30) -> Tuple[str, str, int]:
    """
    Run ripgrep command asynchronously.
    
    Args:
        args: Command arguments
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    rg_binary = get_ripgrep_binary()
    cmd = [rg_binary] + args
    
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024 * 10  # 10MB buffer
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"ripgrep command timed out after {timeout} seconds")
        
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            process.returncode or 0
        )
    except Exception as e:
        logger.error(f"Error running ripgrep: {e}")
        raise


def parse_ripgrep_output(output: str, include_line_numbers: bool = True) -> List[Dict[str, Any]]:
    """
    Parse ripgrep output into structured results.
    
    Args:
        output: Raw ripgrep output
        include_line_numbers: Whether line numbers are included
        
    Returns:
        List of parsed results
    """
    results = []
    lines = output.strip().split("\n") if output.strip() else []
    
    for line in lines:
        if not line:
            continue
            
        if include_line_numbers:
            # Format: file:line:column:match or file:line:match
            parts = line.split(":", 3)
            if len(parts) >= 3:
                result = {
                    "file_path": parts[0],
                    "line_number": int(parts[1]) if parts[1].isdigit() else None,
                    "match_text": parts[-1]
                }
                if len(parts) == 4 and parts[2].isdigit():
                    result["column"] = int(parts[2])
                results.append(result)
        else:
            # Format: file:match
            parts = line.split(":", 1)
            if len(parts) == 2:
                results.append({
                    "file_path": parts[0],
                    "match_text": parts[1]
                })
    
    return results


def parse_context_output(output: str) -> List[Dict[str, Any]]:
    """
    Parse ripgrep output with context lines.
    
    Args:
        output: Raw ripgrep output with context
        
    Returns:
        List of parsed results with context
    """
    results = []
    lines = output.strip().split("\n") if output.strip() else []
    
    current_file = None
    current_match = None
    context_before = []
    context_after = []
    in_context_after = False
    
    for line in lines:
        if not line:
            continue
        
        # File separator
        if line == "--":
            if current_match:
                current_match["context_after"] = context_after.copy()
                results.append(current_match)
                current_match = None
                context_before = []
                context_after = []
                in_context_after = False
            continue
        
        # Check if it's a file header
        if ":" in line:
            parts = line.split(":", 3)
            if len(parts) >= 3:
                if parts[1].isdigit():  # It's a match line
                    if current_match:
                        current_match["context_after"] = context_after.copy()
                        results.append(current_match)
                    
                    current_match = {
                        "file_path": parts[0],
                        "line_number": int(parts[1]),
                        "match_text": parts[-1],
                        "context_before": context_before.copy()
                    }
                    context_before = []
                    context_after = []
                    in_context_after = True
                elif parts[1] == "-":  # Context line
                    if in_context_after:
                        context_after.append(parts[-1])
                    else:
                        context_before.append(parts[-1])
    
    # Add last match if exists
    if current_match:
        current_match["context_after"] = context_after.copy()
        results.append(current_match)
    
    return results


def format_file_type_arg(file_type: str) -> List[str]:
    """
    Format file type argument for ripgrep.
    
    Args:
        file_type: File type identifier
        
    Returns:
        List of ripgrep arguments
    """
    # Map common extensions to ripgrep types
    type_map = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "rust": "rust",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "go": "go",
        "ruby": "ruby",
        "php": "php",
        "swift": "swift",
        "kotlin": "kotlin",
        "scala": "scala",
        "haskell": "haskell",
        "erlang": "erlang",
        "elixir": "elixir",
        "clojure": "clojure",
        "perl": "perl",
        "lua": "lua",
        "r": "r",
        "matlab": "matlab",
        "julia": "julia",
        "fortran": "fortran",
        "html": "html",
        "css": "css",
        "xml": "xml",
        "json": "json",
        "yaml": "yaml",
        "toml": "toml",
        "markdown": "md",
        "tex": "tex",
        "sql": "sql",
        "sh": "sh",
        "docker": "docker",
        "make": "make",
        "cmake": "cmake",
    }
    
    rg_type = type_map.get(file_type.lower(), file_type.lower())
    return ["--type", rg_type]


def sanitize_path(path: Optional[str]) -> Optional[str]:
    """
    Sanitize and validate file path.
    
    Args:
        path: File path to sanitize
        
    Returns:
        Sanitized path or None
    """
    if not path:
        return None
    
    # Resolve to absolute path and check for path traversal
    try:
        resolved = Path(path).resolve()
        
        # Get workspace directory from environment or use current directory
        workspace = Path(os.environ.get("RG_DEFAULT_PATH", os.getcwd())).resolve()
        
        # Ensure the path is within the workspace (unless explicitly allowed)
        if os.environ.get("RG_ALLOW_OUTSIDE_WORKSPACE", "false").lower() != "true":
            try:
                resolved.relative_to(workspace)
            except ValueError:
                raise ValueError(f"Path {path} is outside the allowed workspace")
        
        return str(resolved)
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise ValueError(f"Invalid path: {path}")


def get_max_results() -> int:
    """Get maximum number of results from environment."""
    try:
        return int(os.environ.get("RG_MAX_RESULTS", "1000"))
    except ValueError:
        return 1000


def get_timeout() -> int:
    """Get command timeout from environment."""
    try:
        return int(os.environ.get("RG_TIMEOUT", "30"))
    except ValueError:
        return 30