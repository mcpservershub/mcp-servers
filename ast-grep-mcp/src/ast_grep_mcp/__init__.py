"""
ast-grep MCP Server

A Model Context Protocol server for ast-grep CLI tool integration.
Provides search and search_replace functionality for code analysis and transformation.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .server import mcp, search, search_replace

__all__ = ["mcp", "search", "search_replace"]