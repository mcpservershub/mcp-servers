"""
MultilsPy MCP Server - Language Server Protocol integration for MCP.

This package provides a Model Context Protocol (MCP) server that wraps MultilsPy
to expose Language Server Protocol (LSP) capabilities through MCP tools.
"""

__version__ = "0.1.0"
__author__ = "MCP LSP Team"
__email__ = "mcp-lsp@example.com"

# Import main components for easier access
from .models import (
    # Enums
    Language,
    CompletionItemKind,
    SymbolKind,
    
    # Base models
    Position,
    Range,
    Location,
    CompletionItem,
    SymbolInformation,
    Hover,
    TextEdit,
    
    # Request models
    NavigationRequest,
    NavigationResponse,
    CompletionRequest,
    CompletionResponse,
    DocumentSymbolRequest,
    DocumentSymbolResponse,
    HoverRequest,
    HoverResponse,
    WorkspaceSymbolRequest,
    WorkspaceSymbolResponse,
    
    # Configuration
    WorkspaceConfig,
    SessionState,
)

from .lsp_manager import LSPManager

from .server import (
    mcp,
    initialize_workspace,
    navigate_to_definition,
    find_references,
    get_completions,
    get_hover_info,
    get_document_symbols,
    search_workspace_symbols,
    detect_file_language,
    save_session,
    load_session,
    main,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    
    # Models
    "Language",
    "CompletionItemKind",
    "SymbolKind",
    "Position",
    "Range",
    "Location",
    "CompletionItem",
    "SymbolInformation",
    "Hover",
    "TextEdit",
    "NavigationRequest",
    "NavigationResponse",
    "CompletionRequest",
    "CompletionResponse",
    "DocumentSymbolRequest",
    "DocumentSymbolResponse",
    "HoverRequest",
    "HoverResponse",
    "WorkspaceSymbolRequest",
    "WorkspaceSymbolResponse",
    "WorkspaceConfig",
    "SessionState",
    
    # Core classes
    "LSPManager",
    
    # MCP server and tools
    "mcp",
    "initialize_workspace",
    "navigate_to_definition",
    "find_references",
    "get_completions",
    "get_hover_info",
    "get_document_symbols",
    "search_workspace_symbols",
    "detect_file_language",
    "save_session",
    "load_session",
    "main",
]