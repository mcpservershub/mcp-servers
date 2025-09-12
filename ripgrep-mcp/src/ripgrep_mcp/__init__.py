"""Ripgrep MCP Server - Model Context Protocol server for ripgrep.

A powerful MCP server that provides programmatic access to ripgrep's
blazing-fast text search capabilities.
"""

from .server import mcp, main
from .tools import (
    search,
    search_by_type,
    search_with_context,
    replace,
    list_files,
    search_multiline,
    stats,
    search_binary,
    validate_ripgrep,
)
from .validators import (
    SearchParams,
    SearchByTypeParams,
    SearchWithContextParams,
    ReplaceParams,
    ListFilesParams,
    SearchMultilineParams,
    StatsParams,
    SearchBinaryParams,
    validate_ripgrep_available,
)

__version__ = "0.1.0"
__author__ = "capten.ai"
__license__ = "MIT"

__all__ = [
    # Main components
    "mcp",
    "main",
    "__version__",
    
    # Tools
    "search",
    "search_by_type",
    "search_with_context",
    "replace",
    "list_files",
    "search_multiline",
    "stats",
    "search_binary",
    "validate_ripgrep",
    
    # Validators
    "SearchParams",
    "SearchByTypeParams",
    "SearchWithContextParams",
    "ReplaceParams",
    "ListFilesParams",
    "SearchMultilineParams",
    "StatsParams",
    "SearchBinaryParams",
    "validate_ripgrep_available",
]