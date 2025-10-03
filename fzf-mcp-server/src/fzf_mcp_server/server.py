"""MCP Server for fzf - A command-line fuzzy finder."""

import asyncio
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app = FastMCP("fzf-mcp-server")


def check_fzf_installed() -> bool:
    """Check if fzf is installed on the system."""
    return shutil.which("fzf") is not None


def validate_path(path: str, must_exist: bool = True) -> Path:
    """
    Validate and resolve a path.

    Args:
        path: Path string to validate
        must_exist: If True, raise error if path doesn't exist

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid or doesn't exist when required
    """
    try:
        resolved_path = Path(path).expanduser().resolve()
        if must_exist and not resolved_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        return resolved_path
    except Exception as e:
        raise ValueError(f"Invalid path '{path}': {str(e)}")


async def run_fzf_command(
    input_items: list[str],
    query: str = "",
    multi: bool = False,
    exact: bool = False,
    case_sensitive: bool = False,
    preview: Optional[str] = None,
    height: str = "40%",
    layout: str = "reverse",
    border: str = "rounded",
    prompt: str = "> ",
    additional_args: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Run fzf command with given parameters.

    Args:
        input_items: List of items to search through
        query: Initial search query
        multi: Enable multi-select mode
        exact: Enable exact match mode
        case_sensitive: Enable case-sensitive matching
        preview: Preview command
        height: Display height
        layout: Layout mode
        border: Border style
        prompt: Input prompt
        additional_args: Additional fzf arguments

    Returns:
        Dictionary with selected items and metadata

    Raises:
        RuntimeError: If fzf is not installed or command fails
    """
    if not check_fzf_installed():
        raise RuntimeError("fzf is not installed. Please install fzf to use this server.")

    # Build fzf command
    cmd = ["fzf", "--filter", query or ""]

    if multi:
        cmd.append("--multi")
    if exact:
        cmd.append("--exact")
    if case_sensitive:
        cmd.append("+i")
    if preview:
        cmd.extend(["--preview", preview])
    if height:
        cmd.extend(["--height", height])
    if layout:
        cmd.extend(["--layout", layout])
    if border:
        cmd.extend(["--border", border])
    if prompt:
        cmd.extend(["--prompt", prompt])

    # Add any additional arguments
    if additional_args:
        cmd.extend(additional_args)

    try:
        # Prepare input
        input_text = "\n".join(input_items)

        # Run fzf command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate(input=input_text.encode())

        # Parse output
        selected = []
        if stdout:
            selected = stdout.decode().strip().split("\n")
            selected = [item for item in selected if item]  # Remove empty strings

        return {
            "selected": selected,
            "count": len(selected),
            "query": query,
            "status": "success" if process.returncode == 0 else "no_match",
        }
    except Exception as e:
        logger.error(f"Error running fzf command: {e}")
        raise RuntimeError(f"Failed to execute fzf: {str(e)}")


@app.tool()
async def fuzzy_filter(
    items: list[str],
    query: str = "",
    exact: bool = False,
    case_sensitive: bool = False,
) -> str:
    """
    Filter a list of items using fzf's fuzzy matching algorithm.

    This tool uses fzf in filter mode to match items against a query string.
    It's perfect for finding items in a list when you don't remember the exact name.

    Args:
        items: List of items to filter (e.g., file names, function names, any text)
        query: Search query to filter items (supports fuzzy matching)
        exact: If True, only exact matches are returned
        case_sensitive: If True, matching is case-sensitive

    Returns:
        JSON string with filtered results including selected items and count
    """
    if not items:
        return json.dumps({"error": "No items provided", "selected": [], "count": 0})

    try:
        result = await run_fzf_command(
            input_items=items,
            query=query,
            exact=exact,
            case_sensitive=case_sensitive,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in fuzzy_filter: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


@app.tool()
async def fuzzy_find_files(
    directory: str = ".",
    query: str = "",
    file_type: str = "all",
    hidden: bool = False,
    follow_symlinks: bool = True,
    max_depth: Optional[int] = None,
    exact: bool = False,
) -> str:
    """
    Find files in a directory using fuzzy matching.

    This tool searches for files in a directory and filters them using fzf.
    It's useful for finding files when you only remember part of the filename.

    Args:
        directory: Directory to search in (default: current directory)
        query: Fuzzy search query for filenames
        file_type: Type of files to find - "all", "file", "dir"
        hidden: Include hidden files
        follow_symlinks: Follow symbolic links
        max_depth: Maximum directory depth to search
        exact: If True, only exact matches are returned

    Returns:
        JSON string with matched files and metadata
    """
    try:
        # Validate directory
        dir_path = validate_path(directory)

        # Build find command to get file list
        # Use -L or -H for symlink following (BusyBox compatible)
        if follow_symlinks:
            find_cmd = ["find", "-L", str(dir_path)]
        else:
            find_cmd = ["find", str(dir_path)]

        if max_depth is not None:
            find_cmd.extend(["-maxdepth", str(max_depth)])

        if file_type == "file":
            find_cmd.extend(["-type", "f"])
        elif file_type == "dir":
            find_cmd.extend(["-type", "d"])

        if not hidden:
            find_cmd.extend(["!", "-path", "*/.*"])

        # Execute find command
        process = await asyncio.create_subprocess_exec(
            *find_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            return json.dumps({"error": f"Find command failed: {error_msg}", "selected": [], "count": 0})

        # Parse file list
        files = stdout.decode().strip().split("\n")
        files = [f for f in files if f]  # Remove empty strings

        if not files:
            return json.dumps({"selected": [], "count": 0, "message": "No files found"})

        # Filter with fzf
        result = await run_fzf_command(
            input_items=files,
            query=query,
            exact=exact,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in fuzzy_find_files: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


@app.tool()
async def fuzzy_search_content(
    directory: str = ".",
    search_pattern: str = "",
    file_pattern: str = "*",
    query: str = "",
    case_sensitive: bool = False,
    max_results: int = 1000,
) -> str:
    """
    Search for content within files and filter results with fuzzy matching.

    This tool uses grep to search file contents and fzf to filter results.
    Perfect for finding where specific code or text appears in a codebase.

    Args:
        directory: Directory to search in
        search_pattern: Pattern to search for in files (regex supported)
        file_pattern: File pattern to search (e.g., "*.py", "*.txt")
        query: Additional fuzzy query to filter grep results
        case_sensitive: Case-sensitive search
        max_results: Maximum number of results to return

    Returns:
        JSON string with matched lines, files, and line numbers
    """
    try:
        # Validate directory
        dir_path = validate_path(directory)

        if not search_pattern:
            return json.dumps({"error": "search_pattern is required", "selected": [], "count": 0})

        # Use find + grep for BusyBox compatibility (grep doesn't support --include)
        # First, find files matching the pattern
        find_cmd = ["find", str(dir_path), "-type", "f"]

        if file_pattern and file_pattern != "*":
            find_cmd.extend(["-name", file_pattern])

        # Get list of files
        find_process = await asyncio.create_subprocess_exec(
            *find_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        find_stdout, find_stderr = await find_process.communicate()

        if find_process.returncode != 0:
            error_msg = find_stderr.decode().strip()
            return json.dumps({"error": f"Find command failed: {error_msg}", "selected": [], "count": 0})

        files = find_stdout.decode().strip().split("\n")
        files = [f for f in files if f]

        if not files:
            return json.dumps({"selected": [], "count": 0, "message": "No files found matching pattern"})

        # Build grep command for the found files
        grep_cmd = ["grep", "-n"]
        if not case_sensitive:
            grep_cmd.append("-i")
        grep_cmd.append(search_pattern)
        grep_cmd.extend(files)

        # Execute grep command
        process = await asyncio.create_subprocess_exec(
            *grep_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        # Parse grep results (0 = found, 1 = not found, other = error)
        if process.returncode not in [0, 1]:
            error_msg = stderr.decode().strip()
            return json.dumps({"error": f"Grep command failed: {error_msg}", "selected": [], "count": 0})

        results = stdout.decode().strip().split("\n")
        results = [r for r in results if r][:max_results]  # Limit results

        if not results:
            return json.dumps({"selected": [], "count": 0, "message": "No matches found"})

        # Filter with fzf
        result = await run_fzf_command(
            input_items=results,
            query=query,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in fuzzy_search_content: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


@app.tool()
async def fuzzy_select_lines(
    file_path: str,
    query: str = "",
    line_range: Optional[str] = None,
    exact: bool = False,
) -> str:
    """
    Select lines from a file using fuzzy matching.

    This tool reads a file and allows fuzzy selection of specific lines.
    Useful for extracting specific content from log files or code.

    Args:
        file_path: Path to the file to read
        query: Fuzzy search query for filtering lines
        line_range: Line range to read (e.g., "1-100", "50-", "-100")
        exact: If True, only exact matches are returned

    Returns:
        JSON string with selected lines and metadata
    """
    try:
        # Validate file path
        file = validate_path(file_path)

        if not file.is_file():
            return json.dumps({"error": f"Not a file: {file_path}", "selected": [], "count": 0})

        # Read file
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Apply line range if specified
        if line_range:
            try:
                if "-" in line_range:
                    parts = line_range.split("-")
                    start = int(parts[0]) - 1 if parts[0] else 0
                    end = int(parts[1]) if parts[1] else len(lines)
                    lines = lines[start:end]
                else:
                    line_num = int(line_range) - 1
                    lines = [lines[line_num]] if 0 <= line_num < len(lines) else []
            except (ValueError, IndexError) as e:
                return json.dumps({"error": f"Invalid line range: {line_range}", "selected": [], "count": 0})

        # Remove trailing newlines
        lines = [line.rstrip("\n") for line in lines]

        if not lines:
            return json.dumps({"selected": [], "count": 0, "message": "No lines to filter"})

        # Filter with fzf
        result = await run_fzf_command(
            input_items=lines,
            query=query,
            exact=exact,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in fuzzy_select_lines: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


@app.tool()
async def fuzzy_git_files(
    repository: str = ".",
    query: str = "",
    staged_only: bool = False,
    modified_only: bool = False,
    untracked: bool = False,
) -> str:
    """
    Find and filter git repository files using fuzzy matching.

    This tool lists files in a git repository and filters them with fzf.
    Useful for working with version-controlled files.

    Args:
        repository: Path to git repository (default: current directory)
        query: Fuzzy search query for filenames
        staged_only: Only show staged files
        modified_only: Only show modified files
        untracked: Include untracked files

    Returns:
        JSON string with matched git files
    """
    try:
        # Validate repository
        repo_path = validate_path(repository)

        # Build git command
        git_cmd = ["git", "-C", str(repo_path)]

        if staged_only:
            git_cmd.extend(["diff", "--cached", "--name-only"])
        elif modified_only:
            git_cmd.extend(["diff", "--name-only"])
        elif untracked:
            git_cmd.extend(["ls-files", "--others", "--exclude-standard"])
        else:
            git_cmd.extend(["ls-files"])

        # Execute git command
        process = await asyncio.create_subprocess_exec(
            *git_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            return json.dumps({"error": f"Git command failed: {error_msg}", "selected": [], "count": 0})

        # Parse file list
        files = stdout.decode().strip().split("\n")
        files = [f for f in files if f]

        if not files:
            return json.dumps({"selected": [], "count": 0, "message": "No git files found"})

        # Filter with fzf
        result = await run_fzf_command(
            input_items=files,
            query=query,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in fuzzy_git_files: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


@app.tool()
async def fuzzy_directory_tree(
    directory: str = ".",
    query: str = "",
    max_depth: int = 3,
    show_hidden: bool = False,
) -> str:
    """
    Browse directory tree with fuzzy filtering.

    This tool generates a tree view of directories and filters with fzf.
    Great for exploring directory structures.

    Args:
        directory: Root directory to browse
        query: Fuzzy search query for filtering paths
        max_depth: Maximum depth of tree to display
        show_hidden: Include hidden files and directories

    Returns:
        JSON string with selected paths from directory tree
    """
    try:
        # Validate directory
        dir_path = validate_path(directory)

        if not dir_path.is_dir():
            return json.dumps({"error": f"Not a directory: {directory}", "selected": [], "count": 0})

        # Check if tree command is available
        has_tree = shutil.which("tree") is not None

        if has_tree:
            # Use tree command
            tree_cmd = ["tree", "-F", "-L", str(max_depth)]
            if show_hidden:
                tree_cmd.append("-a")
            tree_cmd.append(str(dir_path))

            process = await asyncio.create_subprocess_exec(
                *tree_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Fallback to find if tree fails
                has_tree = False
            else:
                lines = stdout.decode().strip().split("\n")

        if not has_tree:
            # Fallback: use find command
            find_cmd = ["find", str(dir_path), "-maxdepth", str(max_depth)]
            if not show_hidden:
                find_cmd.extend(["!", "-path", "*/.*"])

            process = await asyncio.create_subprocess_exec(
                *find_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                return json.dumps({"error": f"Failed to list directory: {error_msg}", "selected": [], "count": 0})

            lines = stdout.decode().strip().split("\n")

        lines = [line for line in lines if line]

        if not lines:
            return json.dumps({"selected": [], "count": 0, "message": "No items found"})

        # Filter with fzf
        result = await run_fzf_command(
            input_items=lines,
            query=query,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in fuzzy_directory_tree: {e}")
        return json.dumps({"error": str(e), "selected": [], "count": 0})


def main():
    """Main entry point for the MCP server."""
    # Check if fzf is installed
    if not check_fzf_installed():
        logger.error("fzf is not installed. Please install fzf before running this server.")
        logger.error("Installation instructions: https://github.com/junegunn/fzf#installation")
        raise RuntimeError("fzf is not installed")

    logger.info("Starting fzf MCP server...")
    logger.info("fzf is installed and ready")

    # Run the FastMCP server
    app.run()


if __name__ == "__main__":
    main()
