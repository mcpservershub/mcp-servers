#!/usr/bin/env python3.12
"""MCP Server for tree command with comprehensive functionality."""

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP

mcp = FastMCP("tree-mcp")


async def run_tree_command(
    args: List[str], 
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Execute tree command with given arguments."""
    if not shutil.which("tree"):
        return {
            "success": False,
            "error": "tree command not found. Please install tree on your system.",
            "stdout": "",
            "stderr": ""
        }
    
    cmd = ["tree"] + args
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        stdout, stderr = await proc.communicate()
        
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "returncode": proc.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": ""
        }


def validate_path(path: str) -> Optional[str]:
    """Validate and resolve path."""
    try:
        resolved = Path(path).resolve()
        if not resolved.exists():
            return f"Path does not exist: {path}"
        return None
    except Exception as e:
        return f"Invalid path: {e}"


async def write_output_if_specified(
    content: str, 
    output_file: Optional[str] = None
) -> Optional[str]:
    """Write content to file if output_file is specified."""
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            return f"Output written to: {output_path}"
        except Exception as e:
            return f"Failed to write output file: {e}"
    return None


@mcp.tool()
async def tree_basic(
    path: str = ".",
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display directory tree structure.
    
    Args:
        path: Directory path to display tree for (default: current directory)
        output_file: Optional file path to write output
    
    Returns:
        Tree structure output and operation status
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    result = await run_tree_command([path])
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_with_size(
    path: str = ".",
    human_readable: bool = True,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display directory tree with file sizes.
    
    Args:
        path: Directory path to display tree for
        human_readable: Show sizes in human-readable format (KB, MB, etc.)
        output_file: Optional file path to write output
    
    Returns:
        Tree structure with file sizes
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-s"]
    if human_readable:
        args.append("-h")
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_directories_only(
    path: str = ".",
    max_depth: Optional[int] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display only directories in tree structure.
    
    Args:
        path: Directory path to display tree for
        max_depth: Maximum depth to descend (optional)
        output_file: Optional file path to write output
    
    Returns:
        Tree structure showing only directories
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-d"]
    if max_depth is not None:
        if max_depth < 1:
            return {"success": False, "error": "max_depth must be at least 1"}
        args.extend(["-L", str(max_depth)])
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_with_permissions(
    path: str = ".",
    show_owner: bool = True,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree with file permissions and ownership.
    
    Args:
        path: Directory path to display tree for
        show_owner: Show file owner and group
        output_file: Optional file path to write output
    
    Returns:
        Tree structure with permissions info
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-p"]
    if show_owner:
        args.extend(["-u", "-g"])
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_with_pattern(
    path: str = ".",
    pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    case_insensitive: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree with pattern matching.
    
    Args:
        path: Directory path to display tree for
        pattern: Include only files matching pattern (e.g., "*.py")
        exclude_pattern: Exclude files matching pattern
        case_insensitive: Make pattern matching case-insensitive
        output_file: Optional file path to write output
    
    Returns:
        Filtered tree structure
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = []
    
    if pattern:
        if case_insensitive:
            args.extend(["--matchdirs", "--ignore-case", "-P", pattern])
        else:
            args.extend(["-P", pattern])
    
    if exclude_pattern:
        args.extend(["-I", exclude_pattern])
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_with_dates(
    path: str = ".",
    sort_by_time: bool = False,
    reverse_sort: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree with file modification dates.
    
    Args:
        path: Directory path to display tree for
        sort_by_time: Sort files by modification time
        reverse_sort: Reverse the sort order
        output_file: Optional file path to write output
    
    Returns:
        Tree structure with date information
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-D"]
    
    if sort_by_time:
        args.append("-t")
    
    if reverse_sort:
        args.append("-r")
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_full_paths(
    path: str = ".",
    max_depth: Optional[int] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree with full path prefix for each file.
    
    Args:
        path: Directory path to display tree for
        max_depth: Maximum depth to descend
        output_file: Optional file path to write output
    
    Returns:
        Tree structure with full paths
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-f"]
    
    if max_depth is not None:
        if max_depth < 1:
            return {"success": False, "error": "max_depth must be at least 1"}
        args.extend(["-L", str(max_depth)])
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_json_output(
    path: str = ".",
    max_depth: Optional[int] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree in JSON format.
    
    Args:
        path: Directory path to display tree for
        max_depth: Maximum depth to descend
        output_file: Optional file path to write output
    
    Returns:
        Tree structure in JSON format
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-J"]
    
    if max_depth is not None:
        if max_depth < 1:
            return {"success": False, "error": "max_depth must be at least 1"}
        args.extend(["-L", str(max_depth)])
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"]:
        try:
            result["json_data"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            result["json_parse_error"] = "Failed to parse JSON output"
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_xml_output(
    path: str = ".",
    max_depth: Optional[int] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree in XML/HTML format.
    
    Args:
        path: Directory path to display tree for
        max_depth: Maximum depth to descend
        output_file: Optional file path to write output
    
    Returns:
        Tree structure in XML/HTML format
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = ["-X"]
    
    if max_depth is not None:
        if max_depth < 1:
            return {"success": False, "error": "max_depth must be at least 1"}
        args.extend(["-L", str(max_depth)])
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_colorized(
    path: str = ".",
    force_colors: bool = True,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display colorized tree output.
    
    Args:
        path: Directory path to display tree for
        force_colors: Force colorization even when piping
        output_file: Optional file path to write output
    
    Returns:
        Colorized tree structure
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = []
    if force_colors:
        args.append("-C")
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_hidden_files(
    path: str = ".",
    show_hidden: bool = True,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display tree including hidden files.
    
    Args:
        path: Directory path to display tree for
        show_hidden: Include hidden files (starting with .)
        output_file: Optional file path to write output
    
    Returns:
        Tree structure including hidden files
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = []
    if show_hidden:
        args.append("-a")
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


@mcp.tool()
async def tree_advanced(
    path: str = ".",
    max_depth: Optional[int] = None,
    directories_only: bool = False,
    show_size: bool = False,
    human_readable: bool = False,
    show_permissions: bool = False,
    show_owner: bool = False,
    show_dates: bool = False,
    full_paths: bool = False,
    show_hidden: bool = False,
    pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    sort_by_time: bool = False,
    reverse_sort: bool = False,
    no_indent: bool = False,
    output_format: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advanced tree command with all options combined.
    
    Args:
        path: Directory path to display tree for
        max_depth: Maximum depth to descend
        directories_only: Show only directories
        show_size: Display file sizes
        human_readable: Human-readable sizes (requires show_size)
        show_permissions: Show file permissions
        show_owner: Show file owner and group
        show_dates: Show modification dates
        full_paths: Show full path prefix
        show_hidden: Include hidden files
        pattern: Include only files matching pattern
        exclude_pattern: Exclude files matching pattern
        sort_by_time: Sort by modification time
        reverse_sort: Reverse sort order
        no_indent: No indentation lines
        output_format: Output format ("json", "xml", or None for default)
        output_file: Optional file path to write output
    
    Returns:
        Customized tree output
    """
    if error := validate_path(path):
        return {"success": False, "error": error}
    
    args = []
    
    if max_depth is not None:
        if max_depth < 1:
            return {"success": False, "error": "max_depth must be at least 1"}
        args.extend(["-L", str(max_depth)])
    
    if directories_only:
        args.append("-d")
    
    if show_size:
        args.append("-s")
        if human_readable:
            args.append("-h")
    
    if show_permissions:
        args.append("-p")
    
    if show_owner:
        args.extend(["-u", "-g"])
    
    if show_dates:
        args.append("-D")
    
    if full_paths:
        args.append("-f")
    
    if show_hidden:
        args.append("-a")
    
    if pattern:
        args.extend(["-P", pattern])
    
    if exclude_pattern:
        args.extend(["-I", exclude_pattern])
    
    if sort_by_time:
        args.append("-t")
    
    if reverse_sort:
        args.append("-r")
    
    if no_indent:
        args.append("-i")
    
    if output_format:
        if output_format.lower() == "json":
            args.append("-J")
        elif output_format.lower() == "xml":
            args.append("-X")
        elif output_format.lower() != "text":
            return {"success": False, "error": f"Unknown output format: {output_format}"}
    
    args.append(path)
    
    result = await run_tree_command(args)
    
    if result["success"] and output_format == "json":
        try:
            result["json_data"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            result["json_parse_error"] = "Failed to parse JSON output"
    
    if result["success"] and output_file:
        if write_msg := await write_output_if_specified(result["stdout"], output_file):
            result["output_file_status"] = write_msg
    
    return result


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()