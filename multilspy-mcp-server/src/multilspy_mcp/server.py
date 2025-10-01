"""
MultilsPy MCP Server - Main server implementation using FastMCP.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .models import (
    NavigationRequest, NavigationResponse,
    CompletionRequest, CompletionResponse,
    DocumentSymbolRequest, DocumentSymbolResponse,
    HoverRequest, HoverResponse,
    WorkspaceSymbolRequest, WorkspaceSymbolResponse,
    Language
)
from .lsp_manager import LSPManager

# Initialize FastMCP server
mcp = FastMCP("multilspy-mcp-server")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global LSP manager instance
lsp_manager: Optional[LSPManager] = None


def initialize_lsp_manager(workspace_root: Optional[str] = None) -> LSPManager:
    """
    Initialize the global LSP manager.
    
    Args:
        workspace_root: Root directory of the workspace
        
    Returns:
        Initialized LSPManager instance
    """
    global lsp_manager
    
    if workspace_root is None:
        workspace_root = os.environ.get("WORKSPACE_ROOT", os.getcwd())
    
    cache_dir = os.environ.get("MCP_LSP_CACHE_DIR", "~/.mcp-lsp/cache")
    
    lsp_manager = LSPManager(workspace_root, cache_dir)
    logger.info(f"Initialized LSP manager for workspace: {workspace_root}")
    
    return lsp_manager


@mcp.tool(
    name="code_navigate_definition",
    description="Navigate to the definition of a symbol at the given position"
)
def navigate_to_definition(
    file_path: str = Field(..., description="Relative path to the file"),
    line: int = Field(..., ge=0, description="Line number (0-indexed)"),
    column: int = Field(..., ge=0, description="Column number (0-indexed)"),
    language: Optional[str] = Field(None, description="Programming language hint")
) -> NavigationResponse:
    """
    Navigate to the definition of a symbol.
    
    This tool uses the textDocument/definition LSP request to find where
    a symbol is defined. Useful for jumping to function, class, or variable
    definitions.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        locations = lsp_manager.request_definition(file_path, line, column, lang)
        
        return NavigationResponse(
            locations=locations,
            success=True
        )
    except Exception as e:
        logger.error(f"Error in navigate_to_definition: {str(e)}")
        return NavigationResponse(
            locations=[],
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="code_find_references",
    description="Find all references to a symbol at the given position"
)
def find_references(
    file_path: str = Field(..., description="Relative path to the file"),
    line: int = Field(..., ge=0, description="Line number (0-indexed)"),
    column: int = Field(..., ge=0, description="Column number (0-indexed)"),
    language: Optional[str] = Field(None, description="Programming language hint")
) -> NavigationResponse:
    """
    Find all references to a symbol.
    
    This tool uses the textDocument/references LSP request to find all
    locations where a symbol is referenced. Useful for understanding
    how a function, class, or variable is used throughout the codebase.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        locations = lsp_manager.request_references(file_path, line, column, lang)
        
        return NavigationResponse(
            locations=locations,
            success=True
        )
    except Exception as e:
        logger.error(f"Error in find_references: {str(e)}")
        return NavigationResponse(
            locations=[],
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="code_complete",
    description="Get code completion suggestions at the given position"
)
def get_completions(
    file_path: str = Field(..., description="Relative path to the file"),
    line: int = Field(..., ge=0, description="Line number (0-indexed)"),
    column: int = Field(..., ge=0, description="Column number (0-indexed)"),
    language: Optional[str] = Field(None, description="Programming language hint"),
    allow_incomplete: bool = Field(False, description="Allow incomplete results"),
    trigger_character: Optional[str] = Field(None, description="Trigger character if any")
) -> CompletionResponse:
    """
    Get code completion suggestions.
    
    This tool uses the textDocument/completion LSP request to provide
    context-aware code completions. Returns a list of completion items
    that can be inserted at the cursor position.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        completions = lsp_manager.request_completions(
            file_path, line, column, lang, allow_incomplete
        )
        
        return CompletionResponse(
            completions=completions,
            is_incomplete=allow_incomplete and len(completions) > 0,
            success=True
        )
    except Exception as e:
        logger.error(f"Error in get_completions: {str(e)}")
        return CompletionResponse(
            completions=[],
            is_incomplete=False,
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="code_get_hover",
    description="Get hover information for a symbol at the given position"
)
def get_hover_info(
    file_path: str = Field(..., description="Relative path to the file"),
    line: int = Field(..., ge=0, description="Line number (0-indexed)"),
    column: int = Field(..., ge=0, description="Column number (0-indexed)"),
    language: Optional[str] = Field(None, description="Programming language hint")
) -> HoverResponse:
    """
    Get hover information for a symbol.
    
    This tool uses the textDocument/hover LSP request to get detailed
    information about a symbol, including its type signature, documentation,
    and other relevant details that would typically appear in an IDE tooltip.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        hover = lsp_manager.request_hover(file_path, line, column, lang)
        
        return HoverResponse(
            hover=hover,
            success=True
        )
    except Exception as e:
        logger.error(f"Error in get_hover_info: {str(e)}")
        return HoverResponse(
            hover=None,
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="code_document_symbols",
    description="Get all symbols defined in a document"
)
def get_document_symbols(
    file_path: str = Field(..., description="Relative path to the file"),
    language: Optional[str] = Field(None, description="Programming language hint")
) -> DocumentSymbolResponse:
    """
    Get all symbols in a document.
    
    This tool uses the textDocument/documentSymbol LSP request to retrieve
    a hierarchical list of all symbols (classes, functions, variables, etc.)
    defined in the specified file.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        symbols = lsp_manager.request_document_symbols(file_path, lang)
        
        return DocumentSymbolResponse(
            symbols=symbols,
            tree=None,  # Tree structure can be added later
            success=True
        )
    except Exception as e:
        logger.error(f"Error in get_document_symbols: {str(e)}")
        return DocumentSymbolResponse(
            symbols=[],
            tree=None,
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="code_search_workspace",
    description="Search for symbols across the entire workspace"
)
def search_workspace_symbols(
    query: str = Field(..., description="Search query string"),
    language: Optional[str] = Field(None, description="Programming language to search in"),
    limit: int = Field(100, description="Maximum number of results to return")
) -> WorkspaceSymbolResponse:
    """
    Search for symbols across the workspace.
    
    This tool uses the workspace/symbol LSP request to search for symbols
    matching the query across all files in the workspace. Useful for finding
    classes, functions, or variables by name pattern.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lang = Language(language) if language else None
        symbols = lsp_manager.request_workspace_symbol(query, lang)
        
        # Apply limit
        if limit and len(symbols) > limit:
            symbols = symbols[:limit]
        
        return WorkspaceSymbolResponse(
            symbols=symbols,
            success=True
        )
    except Exception as e:
        logger.error(f"Error in search_workspace_symbols: {str(e)}")
        return WorkspaceSymbolResponse(
            symbols=[],
            success=False,
            error=str(e)
        )


@mcp.tool(
    name="lsp_initialize",
    description="Initialize the LSP manager with a specific workspace"
)
def initialize_workspace(
    workspace_root: str,
    cache_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize the LSP manager for a specific workspace.
    
    This should be called before using any other LSP tools to set up
    the workspace context. It initializes the LSP manager and prepares
    it for handling requests.
    """
    try:
        global lsp_manager
        
        if cache_dir:
            os.environ["MCP_LSP_CACHE_DIR"] = cache_dir
        
        lsp_manager = initialize_lsp_manager(workspace_root)
        
        return {
            "success": True,
            "workspace_root": str(lsp_manager.workspace_root),
            "cache_dir": str(lsp_manager.cache_dir),
            "session_id": lsp_manager.session_id,
            "message": "LSP manager initialized successfully"
        }
    except Exception as e:
        logger.error(f"Error initializing workspace: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to initialize LSP manager"
        }


@mcp.tool(
    name="lsp_detect_language",
    description="Detect the programming language of a file"
)
def detect_file_language(
    file_path: str = Field(..., description="Path to the file")
) -> Dict[str, Any]:
    """
    Detect the programming language of a file.
    
    Uses file extension and workspace context to determine the
    programming language of the specified file.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        language = lsp_manager.detect_language(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "language": language.value if language else None,
            "detected": language is not None
        }
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e)
        }


@mcp.tool(
    name="lsp_save_session",
    description="Save the current LSP session state"
)
def save_session() -> Dict[str, Any]:
    """
    Save the current LSP session state to disk.
    
    This saves the current state including open files, cached symbols,
    and capabilities to allow for session restoration later.
    """
    try:
        if not lsp_manager:
            return {
                "success": False,
                "error": "LSP manager not initialized"
            }
        
        lsp_manager.save_session()
        
        return {
            "success": True,
            "session_file": str(lsp_manager.session_file),
            "message": "Session saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving session: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool(
    name="lsp_load_session",
    description="Load a previously saved LSP session"
)
def load_session(
    session_file: str = Field(..., description="Path to the session file")
) -> Dict[str, Any]:
    """
    Load a previously saved LSP session.
    
    Restores the session state including cached data and workspace configuration
    from a previously saved session file.
    """
    try:
        if not lsp_manager:
            initialize_lsp_manager()
        
        lsp_manager.load_session(session_file)
        
        return {
            "success": True,
            "session_id": lsp_manager.session_id,
            "workspace_root": str(lsp_manager.workspace_root),
            "message": "Session loaded successfully"
        }
    except Exception as e:
        logger.error(f"Error loading session: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Initialize on import if WORKSPACE_ROOT is set
if os.environ.get("WORKSPACE_ROOT"):
    try:
        initialize_lsp_manager(os.environ.get("WORKSPACE_ROOT"))
        logger.info(f"Auto-initialized with workspace: {os.environ.get('WORKSPACE_ROOT')}")
    except Exception as e:
        logger.warning(f"Failed to auto-initialize LSP manager: {e}")


def main():
    """Main function to run the MCP server."""
    import asyncio
    asyncio.run(mcp.run())


if __name__ == "__main__":
    main()