#!/usr/bin/env python3
"""
MCP Server for ast-grep CLI tool integration.

Provides search and search_replace functionality using ast-grep
for code analysis and transformation.
"""

import subprocess
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ast-grep")


def run_ast_grep_command(args: List[str]) -> Dict[str, Any]:
    """Run ast-grep command and return parsed result."""
    try:
        result = subprocess.run(
            ["ast-grep"] + args,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip() or "Command failed",
                "stdout": result.stdout.strip()
            }
        
        return {
            "success": True,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "ast-grep command not found. Please install ast-grep CLI tool."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@mcp.tool()
def search(project_path: str, pattern: str, language: str) -> str:
    """
    Search for code patterns using ast-grep.
    
    Args:
        project_path: Path to the project directory to search in
        pattern: AST pattern to search for
        language: Programming language (e.g., python, javascript, rust, etc.)
    
    Returns:
        Search results as formatted text
    """
    # Validate project path
    path = Path(project_path)
    if not path.exists():
        return f"Error: Project path '{project_path}' does not exist"
    
    if not path.is_dir():
        return f"Error: Project path '{project_path}' is not a directory"
    
    # Build ast-grep command
    args = [
        "run",
        "--pattern", pattern,
        "--lang", language,
        str(path)
    ]
    
    result = run_ast_grep_command(args)
    
    if not result["success"]:
        return f"Error: {result['error']}"
    
    output = result["stdout"]
    if not output:
        return f"No matches found for pattern '{pattern}' in {project_path}"
    
    return f"Search results for pattern '{pattern}' in {project_path}:\n\n{output}"


@mcp.tool()
def search_replace(project_path: str, pattern: str, language: str, new_pattern: str) -> str:
    """
    Search and replace code patterns using ast-grep.
    
    Args:
        project_path: Path to the project directory to modify
        pattern: AST pattern to search for and replace
        language: Programming language (e.g., python, javascript, rust, etc.)
        new_pattern: New pattern to replace the matched pattern with
    
    Returns:
        Results of the search and replace operation
    """
    # Validate project path
    path = Path(project_path)
    if not path.exists():
        return f"Error: Project path '{project_path}' does not exist"
    
    if not path.is_dir():
        return f"Error: Project path '{project_path}' is not a directory"
    
    # Build ast-grep command for search and replace
    args = [
        "run",
        "--pattern", pattern,
        "--rewrite", new_pattern,
        "--lang", language,
        "--update-all",
        str(path)
    ]
    
    result = run_ast_grep_command(args)
    
    if not result["success"]:
        return f"Error: {result['error']}"
    
    output = result["stdout"]
    if not output:
        return f"No matches found for pattern '{pattern}' in {project_path}. No replacements made."
    
    return f"Search and replace completed for pattern '{pattern}' -> '{new_pattern}' in {project_path}:\n\n{output}"


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()