"""MCP Server for fd CLI tool.

This server provides tools to interact with the fd command-line utility,
enabling fast file and directory searches with various filters.
"""

import asyncio
import json
import shutil
import subprocess
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
app = FastMCP("fd-mcp-server")


def check_fd_installed() -> bool:
    """Check if fd is installed on the system."""
    return shutil.which("fd") is not None or shutil.which("fdfind") is not None


def get_fd_command() -> str:
    """Get the fd command name (fd or fdfind)."""
    if shutil.which("fd"):
        return "fd"
    elif shutil.which("fdfind"):
        return "fdfind"
    else:
        raise RuntimeError("fd is not installed on the system")


async def run_fd_command(args: list[str]) -> dict[str, Any]:
    """
    Run fd command with given arguments and return structured results.

    Args:
        args: List of command-line arguments for fd

    Returns:
        Dictionary containing results, error, and metadata
    """
    try:
        fd_cmd = get_fd_command()
        cmd = [fd_cmd] + args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        return {
            "success": process.returncode == 0,
            "return_code": process.returncode,
            "results": stdout.decode("utf-8").strip().split("\n") if stdout else [],
            "error": stderr.decode("utf-8").strip() if stderr else None,
            "command": " ".join(cmd),
        }
    except Exception as e:
        return {
            "success": False,
            "return_code": -1,
            "results": [],
            "error": str(e),
            "command": " ".join([get_fd_command()] + args),
        }


@app.tool()
async def fd_search(
    pattern: Optional[str] = None,
    path: Optional[str] = None,
    hidden: bool = False,
    no_ignore: bool = False,
    case_sensitive: bool = False,
    ignore_case: bool = False,
    glob: bool = False,
    absolute_path: bool = False,
    follow_symlinks: bool = False,
    full_path: bool = False,
    max_depth: Optional[int] = None,
    type_filter: Optional[str] = None,
    extension: Optional[str] = None,
    size: Optional[str] = None,
    max_results: Optional[int] = None,
) -> str:
    """
    Search for files and directories using fd.

    This is the main search tool that provides flexible file/directory searching
    with regex or glob patterns.

    Args:
        pattern: Search pattern (regex by default, glob if glob=True)
        path: Root directory for search (default: current directory)
        hidden: Include hidden files and directories
        no_ignore: Don't respect .gitignore and other ignore files
        case_sensitive: Force case-sensitive search
        ignore_case: Force case-insensitive search
        glob: Use glob-based search instead of regex
        absolute_path: Show absolute paths
        follow_symlinks: Follow symbolic links
        full_path: Match pattern against full path
        max_depth: Maximum search depth
        type_filter: Filter by type (f/file, d/dir, l/symlink, x/executable, e/empty)
        extension: Filter by file extension (e.g., 'py', 'txt')
        size: Filter by size (e.g., '+10k', '-1m')
        max_results: Limit number of results

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = []

    # Add flags
    if hidden:
        args.append("--hidden")
    if no_ignore:
        args.append("--no-ignore")
    if case_sensitive:
        args.append("--case-sensitive")
    if ignore_case:
        args.append("--ignore-case")
    if glob:
        args.append("--glob")
    if absolute_path:
        args.append("--absolute-path")
    if follow_symlinks:
        args.append("--follow")
    if full_path:
        args.append("--full-path")

    # Add options with values
    if max_depth is not None:
        args.extend(["--max-depth", str(max_depth)])
    if type_filter:
        args.extend(["--type", type_filter])
    if extension:
        args.extend(["--extension", extension])
    if size:
        args.extend(["--size", size])
    if max_results is not None:
        args.extend(["--max-results", str(max_results)])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_search_by_extension(
    extension: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    hidden: bool = False,
    no_ignore: bool = False,
) -> str:
    """
    Search for files by extension.

    A simplified tool for finding files with specific extensions.

    Args:
        extension: File extension to search for (e.g., 'py', 'md', 'txt')
        path: Root directory for search (default: current directory)
        pattern: Optional pattern to match within files of this extension
        hidden: Include hidden files
        no_ignore: Don't respect .gitignore files

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = ["--extension", extension]

    if hidden:
        args.append("--hidden")
    if no_ignore:
        args.append("--no-ignore")

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_search_by_type(
    type_filter: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    hidden: bool = False,
    max_depth: Optional[int] = None,
) -> str:
    """
    Search for entries by type.

    Filter search results by file type (file, directory, symlink, etc.).

    Args:
        type_filter: Type to search for:
                    - 'f' or 'file': regular files
                    - 'd' or 'dir': directories
                    - 'l' or 'symlink': symbolic links
                    - 'x' or 'executable': executable files
                    - 'e' or 'empty': empty files or directories
        path: Root directory for search
        pattern: Optional search pattern
        hidden: Include hidden files and directories
        max_depth: Maximum search depth

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = ["--type", type_filter]

    if hidden:
        args.append("--hidden")
    if max_depth is not None:
        args.extend(["--max-depth", str(max_depth)])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_list_all(
    path: Optional[str] = None,
    hidden: bool = False,
    no_ignore: bool = False,
    max_depth: Optional[int] = None,
    type_filter: Optional[str] = None,
) -> str:
    """
    List all files and directories recursively.

    Similar to 'ls -R' but respects ignore files by default.

    Args:
        path: Root directory to list (default: current directory)
        hidden: Include hidden files and directories
        no_ignore: Don't respect .gitignore files
        max_depth: Maximum depth to traverse
        type_filter: Filter by type (f/file, d/dir, etc.)

    Returns:
        JSON string with all entries
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = []

    if hidden:
        args.append("--hidden")
    if no_ignore:
        args.append("--no-ignore")
    if max_depth is not None:
        args.extend(["--max-depth", str(max_depth)])
    if type_filter:
        args.extend(["--type", type_filter])

    # Add match-all pattern and path if path is given
    if path:
        args.append(".")
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_exclude_pattern(
    pattern: Optional[str] = None,
    exclude: list[str] = [],
    path: Optional[str] = None,
    hidden: bool = False,
) -> str:
    """
    Search with exclusion patterns.

    Find files while excluding specific patterns (useful for ignoring directories
    like node_modules, .git, etc.).

    Args:
        pattern: Search pattern
        exclude: List of glob patterns to exclude (e.g., ['*.pyc', 'node_modules'])
        path: Root directory for search
        hidden: Include hidden files

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = []

    for exc in exclude:
        args.extend(["--exclude", exc])

    if hidden:
        args.append("--hidden")

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_changed_within(
    duration: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> str:
    """
    Find files modified within a time period.

    Search for files that have been modified within the specified duration.

    Args:
        duration: Time duration (e.g., '10min', '2h', '1d', '3weeks')
        path: Root directory for search
        pattern: Optional search pattern
        type_filter: Filter by type (f/file, d/dir, etc.)

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = ["--changed-within", duration]

    if type_filter:
        args.extend(["--type", type_filter])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_changed_before(
    duration: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> str:
    """
    Find files modified before a time period.

    Search for files that have been modified before the specified duration.

    Args:
        duration: Time duration (e.g., '10min', '2h', '1d', '3weeks')
        path: Root directory for search
        pattern: Optional search pattern
        type_filter: Filter by type (f/file, d/dir, etc.)

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = ["--changed-before", duration]

    if type_filter:
        args.extend(["--type", type_filter])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_size_filter(
    size: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    extension: Optional[str] = None,
) -> str:
    """
    Find files by size.

    Search for files matching size criteria.

    Args:
        size: Size filter (e.g., '+10k', '-1m', '500b')
              Prefix: '+' (larger), '-' (smaller), none (exact)
              Units: b (bytes), k (KB), m (MB), g (GB), t (TB)
                     ki (KiB), mi (MiB), gi (GiB), ti (TiB)
        path: Root directory for search
        pattern: Optional search pattern
        extension: Optional file extension filter

    Returns:
        JSON string with search results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = ["--size", size]

    if extension:
        args.extend(["--extension", extension])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


@app.tool()
async def fd_exec_command(
    command: str,
    pattern: Optional[str] = None,
    path: Optional[str] = None,
    extension: Optional[str] = None,
    type_filter: Optional[str] = None,
    batch_mode: bool = False,
) -> str:
    """
    Execute command for search results.

    Run a command for each found file (parallel) or with all files (batch).

    Args:
        command: Command to execute (use {} for file placeholder)
        pattern: Search pattern
        path: Root directory for search
        extension: Filter by file extension
        type_filter: Filter by type
        batch_mode: If True, use --exec-batch (single command with all results)
                   If False, use --exec (command for each result in parallel)

    Returns:
        JSON string with execution results
    """
    if not check_fd_installed():
        return json.dumps({
            "success": False,
            "error": "fd is not installed. Please install fd-find.",
            "results": [],
        })

    args = []

    if extension:
        args.extend(["--extension", extension])
    if type_filter:
        args.extend(["--type", type_filter])

    # Add pattern and path (pattern must come before path)
    if pattern:
        args.append(pattern)
    elif path:
        # If no pattern but path is given, use match-all pattern
        args.append(".")

    if path:
        args.append(path)

    # Add exec command
    if batch_mode:
        args.extend(["--exec-batch"] + command.split())
    else:
        args.extend(["--exec"] + command.split())

    result = await run_fd_command(args)
    return json.dumps(result, indent=2)


def main():
    """Run the MCP server."""
    app.run()


if __name__ == "__main__":
    main()