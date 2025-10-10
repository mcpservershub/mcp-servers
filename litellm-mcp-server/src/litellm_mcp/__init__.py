"""LiteLLM MCP Server - Unified interface for 100+ LLM providers."""

__version__ = "0.1.0"

from .server import create_server

__all__ = ["create_server"]