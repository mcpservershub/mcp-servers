"""Ripgrep MCP Server implementation using FastMCP."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from . import tools, validators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ripgrep-mcp")


# Register tools with FastMCP
@mcp.tool(
    name="search",
    description="Search for patterns in files recursively using ripgrep"
)
async def search_tool(
    pattern: str = Field(..., description="Regex pattern to search"),
    path: Optional[str] = Field(None, description="Directory or file to search in"),
    case_sensitive: bool = Field(True, description="Whether search is case sensitive"),
    whole_word: bool = Field(False, description="Match whole words only"),
    line_numbers: bool = Field(True, description="Include line numbers in results"),
    max_results: Optional[int] = Field(100, description="Maximum number of results")
) -> Dict[str, Any]:
    """Search for patterns in files."""
    try:
        results = await tools.search(
            pattern=pattern,
            path=path,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            line_numbers=line_numbers,
            max_results=max_results
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@mcp.tool(
    name="search_by_type",
    description="Search within specific file types"
)
async def search_by_type_tool(
    pattern: str = Field(..., description="Regex pattern to search"),
    file_type: str = Field(..., description="File type to search (e.g., 'python', 'rust', 'js')"),
    path: Optional[str] = Field(None, description="Directory to search in"),
    exclude_type: Optional[str] = Field(None, description="File types to exclude")
) -> Dict[str, Any]:
    """Search within specific file types."""
    try:
        results = await tools.search_by_type(
            pattern=pattern,
            file_type=file_type,
            path=path,
            exclude_type=exclude_type
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search by type error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@mcp.tool(
    name="search_with_context",
    description="Search with surrounding context lines"
)
async def search_with_context_tool(
    pattern: str = Field(..., description="Search pattern"),
    before_context: int = Field(2, description="Number of lines before match"),
    after_context: int = Field(2, description="Number of lines after match"),
    path: Optional[str] = Field(None, description="Search path")
) -> Dict[str, Any]:
    """Get search results with context lines."""
    try:
        results = await tools.search_with_context(
            pattern=pattern,
            before_context=before_context,
            after_context=after_context,
            path=path
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search with context error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@mcp.tool(
    name="replace",
    description="Find and replace patterns in files (preview mode)"
)
async def replace_tool(
    pattern: str = Field(..., description="Pattern to find"),
    replacement: str = Field(..., description="Replacement text"),
    path: Optional[str] = Field(None, description="Target path"),
    dry_run: bool = Field(True, description="Preview changes without applying")
) -> Dict[str, Any]:
    """Find patterns and suggest replacements."""
    try:
        results = await tools.replace(
            pattern=pattern,
            replacement=replacement,
            path=path,
            dry_run=dry_run
        )
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "dry_run": dry_run
        }
    except Exception as e:
        logger.error(f"Replace error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@mcp.tool(
    name="list_files",
    description="List files matching specified criteria"
)
async def list_files_tool(
    pattern: Optional[str] = Field(None, description="Filter by file name pattern"),
    file_type: Optional[str] = Field(None, description="Filter by file type"),
    path: Optional[str] = Field(None, description="Search directory"),
    include_hidden: bool = Field(False, description="Include hidden files")
) -> Dict[str, Any]:
    """List files matching criteria."""
    try:
        files = await tools.list_files(
            pattern=pattern,
            file_type=file_type,
            path=path,
            include_hidden=include_hidden
        )
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"List files error: {e}")
        return {
            "success": False,
            "error": str(e),
            "files": []
        }


@mcp.tool(
    name="search_multiline",
    description="Search for patterns spanning multiple lines"
)
async def search_multiline_tool(
    pattern: str = Field(..., description="Multiline regex pattern"),
    path: Optional[str] = Field(None, description="Search path"),
    pcre2: bool = Field(False, description="Use PCRE2 engine for advanced patterns")
) -> Dict[str, Any]:
    """Search for multiline patterns."""
    try:
        results = await tools.search_multiline(
            pattern=pattern,
            path=path,
            pcre2=pcre2
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Multiline search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@mcp.tool(
    name="stats",
    description="Get statistics about search operations"
)
async def stats_tool(
    pattern: str = Field(..., description="Pattern to analyze"),
    path: Optional[str] = Field(None, description="Target path")
) -> Dict[str, Any]:
    """Get search statistics."""
    try:
        stats = await tools.stats(
            pattern=pattern,
            path=path
        )
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "success": False,
            "error": str(e),
            "stats": {}
        }


@mcp.tool(
    name="search_binary",
    description="Search in binary files"
)
async def search_binary_tool(
    pattern: str = Field(..., description="Pattern to search"),
    path: Optional[str] = Field(None, description="Target path"),
    encoding: str = Field("utf-8", description="File encoding")
) -> Dict[str, Any]:
    """Search in binary files."""
    try:
        results = await tools.search_binary(
            pattern=pattern,
            path=path,
            encoding=encoding
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Binary search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


# Health check tool
@mcp.tool(
    name="health_check",
    description="Check if ripgrep is available and working"
)
async def health_check_tool() -> Dict[str, Any]:
    """Check ripgrep availability."""
    try:
        is_available = await tools.validate_ripgrep()
        return {
            "success": True,
            "ripgrep_available": is_available,
            "message": "Ripgrep is available" if is_available else "Ripgrep not found"
        }
    except Exception as e:
        return {
            "success": False,
            "ripgrep_available": False,
            "error": str(e)
        }


def main():
    """Main entry point for the MCP server."""
    # Validate ripgrep is available
    if not validators.validate_ripgrep_available():
        logger.error("ripgrep (rg) is not installed or not in PATH")
        sys.exit(1)
    
    logger.info("Starting Ripgrep MCP Server...")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()