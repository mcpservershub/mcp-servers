"""
Pydantic models for type validation in the MultilsPy MCP Server.
"""

from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVA = "java"
    RUST = "rust"
    CSHARP = "csharp"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUBY = "ruby"
    DART = "dart"
    KOTLIN = "kotlin"
    CPP = "cpp"
    COBOL = "cobol"


class Position(BaseModel):
    """Position in a text document."""
    line: int = Field(..., ge=0, description="Line position (0-indexed)")
    character: int = Field(..., ge=0, description="Character position (0-indexed)")


class Range(BaseModel):
    """Range in a text document."""
    start: Position
    end: Position


class Location(BaseModel):
    """Location in a file."""
    uri: str = Field(..., description="File URI")
    range: Range
    absolute_path: Optional[str] = Field(None, description="Absolute file path")
    relative_path: Optional[str] = Field(None, description="Relative file path")


class CompletionItemKind(int, Enum):
    """Completion item kinds."""
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUM_MEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25


class CompletionItem(BaseModel):
    """Completion item."""
    completion_text: str = Field(..., description="Text to insert")
    kind: CompletionItemKind = Field(..., description="Completion item kind")
    detail: Optional[str] = Field(None, description="Additional details")
    documentation: Optional[str] = Field(None, description="Documentation")
    sort_text: Optional[str] = Field(None, description="Sort text")
    filter_text: Optional[str] = Field(None, description="Filter text")
    insert_text: Optional[str] = Field(None, description="Text to insert")
    label: Optional[str] = Field(None, description="Label")


class SymbolKind(int, Enum):
    """Symbol kinds."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


class SymbolInformation(BaseModel):
    """Symbol information."""
    name: str = Field(..., description="Symbol name")
    kind: SymbolKind = Field(..., description="Symbol kind")
    location: Optional[Location] = Field(None, description="Symbol location")
    container_name: Optional[str] = Field(None, description="Container name")
    deprecated: Optional[bool] = Field(False, description="Is deprecated")
    detail: Optional[str] = Field(None, description="Additional details")
    range: Optional[Range] = Field(None, description="Symbol range")
    selection_range: Optional[Range] = Field(None, description="Selection range")
    children: Optional[List['SymbolInformation']] = Field(None, description="Child symbols")


class Hover(BaseModel):
    """Hover information."""
    contents: Union[str, List[str], Dict[str, Any]] = Field(..., description="Hover contents")
    range: Optional[Range] = Field(None, description="Hover range")


class WorkspaceConfig(BaseModel):
    """Workspace configuration."""
    root_path: str = Field(..., description="Workspace root path")
    language: Language = Field(..., description="Primary language")
    initialization_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="LSP initialization options")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="LSP settings")
    
    model_config = ConfigDict(use_enum_values=True)


class SessionState(BaseModel):
    """Session state for persistence."""
    session_id: str = Field(..., description="Session ID")
    workspace_config: WorkspaceConfig
    open_files: List[str] = Field(default_factory=list, description="List of open files")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="Negotiated capabilities")
    diagnostics_cache: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cached diagnostics")
    symbol_cache: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cached symbols")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


# Request Models for MCP Tools

class NavigationRequest(BaseModel):
    """Request for navigation (definition/references)."""
    file_path: str = Field(..., description="Relative file path")
    line: int = Field(..., ge=0, description="Line number (0-indexed)")
    column: int = Field(..., ge=0, description="Column number (0-indexed)")
    language: Optional[Language] = Field(None, description="Language hint")


class CompletionRequest(BaseModel):
    """Request for code completions."""
    file_path: str = Field(..., description="Relative file path")
    line: int = Field(..., ge=0, description="Line number (0-indexed)")
    column: int = Field(..., ge=0, description="Column number (0-indexed)")
    language: Optional[Language] = Field(None, description="Language hint")
    allow_incomplete: bool = Field(False, description="Allow incomplete results")
    trigger_character: Optional[str] = Field(None, description="Trigger character")


class DocumentSymbolRequest(BaseModel):
    """Request for document symbols."""
    file_path: str = Field(..., description="Relative file path")
    language: Optional[Language] = Field(None, description="Language hint")


class HoverRequest(BaseModel):
    """Request for hover information."""
    file_path: str = Field(..., description="Relative file path")
    line: int = Field(..., ge=0, description="Line number (0-indexed)")
    column: int = Field(..., ge=0, description="Column number (0-indexed)")
    language: Optional[Language] = Field(None, description="Language hint")


class WorkspaceSymbolRequest(BaseModel):
    """Request for workspace symbols."""
    query: str = Field(..., description="Search query")
    language: Optional[Language] = Field(None, description="Language hint")
    limit: Optional[int] = Field(100, description="Maximum results")


class TextEdit(BaseModel):
    """Text edit operation."""
    range: Range
    new_text: str = Field(..., description="New text to insert")


class FileOperation(BaseModel):
    """File operation."""
    operation: Literal["open", "close", "change", "save"] = Field(..., description="Operation type")
    file_path: str = Field(..., description="File path")
    content: Optional[str] = Field(None, description="File content")
    changes: Optional[List[TextEdit]] = Field(None, description="Text changes")
    version: Optional[int] = Field(None, description="Document version")


# Response Models

class NavigationResponse(BaseModel):
    """Response for navigation requests."""
    locations: List[Location] = Field(default_factory=list, description="Found locations")
    success: bool = Field(True, description="Request success")
    error: Optional[str] = Field(None, description="Error message if failed")


class CompletionResponse(BaseModel):
    """Response for completion requests."""
    completions: List[CompletionItem] = Field(default_factory=list, description="Completion items")
    is_incomplete: bool = Field(False, description="Whether results are incomplete")
    success: bool = Field(True, description="Request success")
    error: Optional[str] = Field(None, description="Error message if failed")


class DocumentSymbolResponse(BaseModel):
    """Response for document symbol requests."""
    symbols: List[SymbolInformation] = Field(default_factory=list, description="Document symbols")
    tree: Optional[List[Dict[str, Any]]] = Field(None, description="Symbol tree structure")
    success: bool = Field(True, description="Request success")
    error: Optional[str] = Field(None, description="Error message if failed")


class HoverResponse(BaseModel):
    """Response for hover requests."""
    hover: Optional[Hover] = Field(None, description="Hover information")
    success: bool = Field(True, description="Request success")
    error: Optional[str] = Field(None, description="Error message if failed")


class WorkspaceSymbolResponse(BaseModel):
    """Response for workspace symbol requests."""
    symbols: List[SymbolInformation] = Field(default_factory=list, description="Workspace symbols")
    success: bool = Field(True, description="Request success")
    error: Optional[str] = Field(None, description="Error message if failed")


# Enable forward references
SymbolInformation.model_rebuild()