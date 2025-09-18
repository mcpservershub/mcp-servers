"""
Spec-Kit MCP Server

A Model Context Protocol server for spec-kit, providing programmatic access
to Spec-Driven Development workflows.
"""

__version__ = "0.1.0"
__author__ = "Spec-Kit MCP Team"

from .server import mcp

__all__ = ["mcp", "__version__"]