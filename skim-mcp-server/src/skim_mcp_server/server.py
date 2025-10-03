#!/usr/bin/env python3
"""
Skim MCP Server

MCP server providing fuzzy finding capabilities through the skim (sk) CLI tool.
"""

import json
import subprocess
import shutil
from typing import Any
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
app = FastMCP("skim-mcp-server")


def check_sk_installed() -> bool:
    """Check if sk (skim) is installed and available in PATH."""
    return shutil.which("sk") is not None


def run_sk_command(
    input_data: str | None = None,
    query: str = "",
    multi: bool = False,
    preview: str | None = None,
    preview_window: str | None = None,
    ansi: bool = False,
    regex: bool = False,
    exact: bool = False,
    case_sensitive: bool = False,
    delimiter: str | None = None,
    nth: str | None = None,
    with_nth: str | None = None,
    tiebreak: str | None = None,
    bind: str | None = None,
    height: str | None = None,
    min_height: int | None = None,
    reverse: bool = False,
    no_sort: bool = False,
    additional_args: list[str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Run sk command with specified options.

    Args:
        input_data: Input data to pass to sk via stdin
        query: Initial query string
        multi: Enable multi-selection mode
        preview: Preview command
        preview_window: Preview window configuration
        ansi: Parse ANSI color codes
        regex: Use regex mode
        exact: Enable exact match mode
        case_sensitive: Case-sensitive matching
        delimiter: Field delimiter
        nth: Select fields to search
        with_nth: Select fields to display
        tiebreak: Tiebreak criteria
        bind: Key bindings
        height: Height of skim window
        min_height: Minimum height
        reverse: Reverse layout
        no_sort: Disable sorting
        additional_args: Additional command-line arguments
        timeout: Command timeout in seconds

    Returns:
        Dictionary with 'success', 'selections', 'query', 'exit_code', and 'error' keys
    """
    if not check_sk_installed():
        return {
            "success": False,
            "selections": [],
            "query": query,
            "exit_code": -1,
            "error": "sk (skim) is not installed or not available in PATH"
        }

    # Build command
    cmd = ["sk", "--no-mouse"]

    if query:
        cmd.extend(["--query", query])
    if multi:
        cmd.append("--multi")
    if preview:
        cmd.extend(["--preview", preview])
    if preview_window:
        cmd.extend(["--preview-window", preview_window])
    if ansi:
        cmd.append("--ansi")
    if regex:
        cmd.append("--regex")
    if exact:
        cmd.append("--exact")
    if case_sensitive:
        cmd.append("--case-sensitive")
    if delimiter:
        cmd.extend(["--delimiter", delimiter])
    if nth:
        cmd.extend(["--nth", nth])
    if with_nth:
        cmd.extend(["--with-nth", with_nth])
    if tiebreak:
        cmd.extend(["--tiebreak", tiebreak])
    if bind:
        cmd.extend(["--bind", bind])
    if height:
        cmd.extend(["--height", height])
    if min_height is not None:
        cmd.extend(["--min-height", str(min_height)])
    if reverse:
        cmd.append("--reverse")
    if no_sort:
        cmd.append("--no-sort")
    if additional_args:
        cmd.extend(additional_args)

    try:
        # Run sk command
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        # Parse output
        selections = []
        if result.returncode == 0:
            selections = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

        return {
            "success": result.returncode == 0,
            "selections": selections,
            "query": query,
            "exit_code": result.returncode,
            "error": result.stderr if result.returncode != 0 and result.returncode != 130 else None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "selections": [],
            "query": query,
            "exit_code": -1,
            "error": f"Command timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "selections": [],
            "query": query,
            "exit_code": -1,
            "error": str(e)
        }


@app.tool()
def fuzzy_find_files(
    directory: str = ".",
    query: str = "",
    multi: bool = True,
    preview: bool = True,
    file_types: str | None = None,
    exclude_patterns: str | None = None,
    max_depth: int | None = None,
    follow_symlinks: bool = False,
    hidden: bool = False,
) -> dict[str, Any]:
    """
    Fuzzy find files in a directory using fd and sk.

    This tool uses fd (if available) to generate file listings and sk for fuzzy finding.
    It's particularly useful for finding files in large codebases.

    Args:
        directory: Directory to search in (default: current directory)
        query: Initial search query
        multi: Enable multi-selection (default: True)
        preview: Show file preview (default: True)
        file_types: Comma-separated file extensions (e.g., "py,js,rs")
        exclude_patterns: Comma-separated patterns to exclude
        max_depth: Maximum directory depth to search
        follow_symlinks: Follow symbolic links
        hidden: Include hidden files

    Returns:
        Dictionary with selected file paths and metadata
    """
    # Build fd command if available, otherwise use find
    if shutil.which("fd"):
        fd_cmd = ["fd", "--type", "f", "--color", "always"]

        if hidden:
            fd_cmd.append("--hidden")
        if follow_symlinks:
            fd_cmd.append("--follow")
        if max_depth is not None:
            fd_cmd.extend(["--max-depth", str(max_depth)])
        if exclude_patterns:
            for pattern in exclude_patterns.split(","):
                fd_cmd.extend(["--exclude", pattern.strip()])
        if file_types:
            for ext in file_types.split(","):
                fd_cmd.extend(["--extension", ext.strip()])

        fd_cmd.append(".")
        fd_cmd.append(directory)

        try:
            fd_result = subprocess.run(
                fd_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            input_data = fd_result.stdout
        except Exception as e:
            return {
                "success": False,
                "selections": [],
                "error": f"Failed to run fd: {str(e)}"
            }
    else:
        # Fallback to find
        find_cmd = ["find", directory, "-type", "f"]

        if max_depth is not None:
            find_cmd.extend(["-maxdepth", str(max_depth)])
        if not hidden:
            find_cmd.extend(["-not", "-path", "*/.*"])

        try:
            find_result = subprocess.run(
                find_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            input_data = find_result.stdout
        except Exception as e:
            return {
                "success": False,
                "selections": [],
                "error": f"Failed to run find: {str(e)}"
            }

    # Configure preview
    preview_cmd = None
    preview_window = None
    if preview:
        if shutil.which("bat"):
            preview_cmd = "bat --color=always --style=numbers --line-range=:500 {}"
        else:
            preview_cmd = "cat {}"
        preview_window = "right:50%:wrap"

    # Run sk
    result = run_sk_command(
        input_data=input_data,
        query=query,
        multi=multi,
        preview=preview_cmd,
        preview_window=preview_window,
        ansi=True,
    )

    return result


@app.tool()
def fuzzy_search_content(
    directory: str = ".",
    query: str = "",
    multi: bool = True,
    preview: bool = True,
    file_types: str | None = None,
    case_sensitive: bool = False,
    fixed_strings: bool = False,
    context_lines: int = 2,
) -> dict[str, Any]:
    """
    Fuzzy search within file contents using ripgrep/ag/grep and sk.

    This tool searches for text within files and provides fuzzy filtering of results.
    Perfect for finding specific code patterns or text across a codebase.

    Args:
        directory: Directory to search in (default: current directory)
        query: Initial search query
        multi: Enable multi-selection (default: True)
        preview: Show file preview with context (default: True)
        file_types: Comma-separated file extensions (e.g., "py,js,rs")
        case_sensitive: Case-sensitive search
        fixed_strings: Treat query as literal string, not regex
        context_lines: Number of context lines to show (default: 2)

    Returns:
        Dictionary with selected matches (format: filename:line:column:content)
    """
    # Choose grep tool (prefer rg > ag > grep)
    grep_cmd = []

    if shutil.which("rg"):
        grep_cmd = [
            "rg",
            "--color=always",
            "--line-number",
            "--column",
            "--no-heading",
            f"--context={context_lines}",
        ]
        if not case_sensitive:
            grep_cmd.append("--ignore-case")
        if fixed_strings:
            grep_cmd.append("--fixed-strings")
        if file_types:
            for ext in file_types.split(","):
                grep_cmd.extend(["--type-add", f"custom:*.{ext.strip()}"])
            grep_cmd.extend(["--type", "custom"])

        # Use empty pattern to match all lines initially
        grep_cmd.extend([".", directory])

    elif shutil.which("ag"):
        grep_cmd = [
            "ag",
            "--color",
            "--numbers",
            "--column",
            f"--context={context_lines}",
        ]
        if not case_sensitive:
            grep_cmd.append("--ignore-case")
        if fixed_strings:
            grep_cmd.append("--literal")
        if file_types:
            for ext in file_types.split(","):
                grep_cmd.append(f"--{ext.strip()}")

        grep_cmd.extend([".", directory])

    else:
        # Fallback to grep
        grep_cmd = [
            "grep",
            "-r",
            "-n",
            "-H",
            f"-C{context_lines}",
        ]
        if not case_sensitive:
            grep_cmd.append("-i")
        if fixed_strings:
            grep_cmd.append("-F")

        grep_cmd.extend([".", directory])

    try:
        grep_result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        input_data = grep_result.stdout

        if not input_data:
            return {
                "success": False,
                "selections": [],
                "error": "No matches found"
            }
    except Exception as e:
        return {
            "success": False,
            "selections": [],
            "error": f"Failed to run grep: {str(e)}"
        }

    # Configure preview
    preview_cmd = None
    preview_window = None
    if preview:
        # Extract filename and line number for preview
        if shutil.which("bat"):
            preview_cmd = "echo {} | cut -d: -f1,2 | xargs -I % sh -c 'FILE=$(echo % | cut -d: -f1); LINE=$(echo % | cut -d: -f2); bat --color=always --style=numbers --highlight-line=$LINE --line-range=$(($LINE-20)):$(($LINE+20)) $FILE'"
        else:
            preview_cmd = "echo {} | cut -d: -f1 | xargs cat"
        preview_window = "right:50%:wrap"

    # Run sk with ANSI color support
    result = run_sk_command(
        input_data=input_data,
        query=query,
        multi=multi,
        preview=preview_cmd,
        preview_window=preview_window,
        ansi=True,
        delimiter=":",
        nth="1..",  # Search all fields except filename
    )

    return result


@app.tool()
def fuzzy_filter_lines(
    input_text: str,
    query: str = "",
    multi: bool = True,
    exact: bool = False,
    regex: bool = False,
    case_sensitive: bool = False,
    delimiter: str | None = None,
    nth: str | None = None,
) -> dict[str, Any]:
    """
    Fuzzy filter lines from input text.

    Generic fuzzy filtering tool that can filter any line-based text input.
    Useful for filtering command outputs, logs, or any structured text data.

    Args:
        input_text: Text input to filter (newline-separated)
        query: Initial search query
        multi: Enable multi-selection (default: True)
        exact: Use exact matching instead of fuzzy
        regex: Use regex matching mode
        case_sensitive: Case-sensitive matching
        delimiter: Field delimiter for structured data
        nth: Select specific fields to search (e.g., "1,3" or "2..")

    Returns:
        Dictionary with selected lines
    """
    if not input_text:
        return {
            "success": False,
            "selections": [],
            "error": "No input text provided"
        }

    result = run_sk_command(
        input_data=input_text,
        query=query,
        multi=multi,
        exact=exact,
        regex=regex,
        case_sensitive=case_sensitive,
        delimiter=delimiter,
        nth=nth,
    )

    return result


@app.tool()
def fuzzy_select_git_files(
    query: str = "",
    multi: bool = True,
    preview: bool = True,
    untracked: bool = False,
    ignored: bool = False,
) -> dict[str, Any]:
    """
    Fuzzy select Git-tracked files.

    Specialized tool for finding files within a Git repository.
    Faster than general file search for Git repositories.

    Args:
        query: Initial search query
        multi: Enable multi-selection (default: True)
        preview: Show file preview (default: True)
        untracked: Include untracked files
        ignored: Include ignored files

    Returns:
        Dictionary with selected Git file paths
    """
    if not shutil.which("git"):
        return {
            "success": False,
            "selections": [],
            "error": "git is not installed or not available in PATH"
        }

    # Build git ls-files command
    git_cmd = ["git", "ls-files"]

    if untracked:
        git_cmd.extend(["--others", "--exclude-standard"])
    if ignored:
        git_cmd.append("--ignored")

    try:
        git_result = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )

        if git_result.returncode != 0:
            return {
                "success": False,
                "selections": [],
                "error": "Not a git repository or git command failed"
            }

        input_data = git_result.stdout

    except Exception as e:
        return {
            "success": False,
            "selections": [],
            "error": f"Failed to run git: {str(e)}"
        }

    # Configure preview
    preview_cmd = None
    preview_window = None
    if preview:
        if shutil.which("bat"):
            preview_cmd = "bat --color=always --style=numbers --line-range=:500 {}"
        else:
            preview_cmd = "cat {}"
        preview_window = "right:50%:wrap"

    # Run sk
    result = run_sk_command(
        input_data=input_data,
        query=query,
        multi=multi,
        preview=preview_cmd,
        preview_window=preview_window,
        ansi=True,
    )

    return result


@app.tool()
def interactive_search(
    command: str,
    query: str = "",
    multi: bool = True,
    preview: str | None = None,
    preview_window: str = "right:50%:wrap",
    ansi: bool = True,
) -> dict[str, Any]:
    """
    Interactive search mode - run command dynamically based on query.

    Advanced tool that allows running a command where {} is replaced with the current query.
    The command is re-executed as the user types, enabling interactive searching.

    Args:
        command: Command to execute (use {} as placeholder for query)
        query: Initial search query
        multi: Enable multi-selection (default: True)
        preview: Preview command
        preview_window: Preview window configuration
        ansi: Parse ANSI color codes (default: True)

    Returns:
        Dictionary with selected items and final query

    Example:
        command: "rg --color=always --line-number '{}' ."
        This will search for the query pattern in real-time using ripgrep
    """
    if not check_sk_installed():
        return {
            "success": False,
            "selections": [],
            "error": "sk (skim) is not installed or not available in PATH"
        }

    # Build sk command with interactive mode
    cmd = ["sk", "--no-mouse", "-i", "-c", command]

    if query:
        cmd.extend(["--query", query])
    if multi:
        cmd.append("--multi")
    if preview:
        cmd.extend(["--preview", preview])
    if preview_window:
        cmd.extend(["--preview-window", preview_window])
    if ansi:
        cmd.append("--ansi")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # Longer timeout for interactive mode
            check=False
        )

        selections = []
        if result.returncode == 0:
            selections = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

        return {
            "success": result.returncode == 0,
            "selections": selections,
            "query": query,
            "exit_code": result.returncode,
            "error": result.stderr if result.returncode != 0 and result.returncode != 130 else None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "selections": [],
            "query": query,
            "exit_code": -1,
            "error": "Command timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "selections": [],
            "query": query,
            "exit_code": -1,
            "error": str(e)
        }


def main():
    """Run the MCP server."""
    # Check if sk is installed
    if not check_sk_installed():
        print("WARNING: sk (skim) is not installed or not in PATH")
        print("Please install skim: https://github.com/skim-rs/skim")

    app.run()


if __name__ == "__main__":
    main()
