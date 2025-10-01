"""Data models for CTags MCP server."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class TagEntry(BaseModel):
    """Represents a single tag entry."""
    name: str
    file: str
    line: Optional[int] = None
    kind: Optional[str] = None
    pattern: Optional[str] = None
    scope: Optional[str] = None
    scope_kind: Optional[str] = None
    
    
class GenerateTagsRequest(BaseModel):
    """Request model for generate_tags tool."""
    path: str = Field(..., description="Directory or file path to index")
    recursive: bool = Field(True, description="Recursively index subdirectories")
    languages: Optional[List[str]] = Field(None, description="Specific languages to index")
    exclude_patterns: Optional[List[str]] = Field(None, description="Patterns to exclude")
    output_file: str = Field("tags", description="Output tags file path")
    extra_options: Optional[List[str]] = Field(None, description="Additional ctags options")


class SearchRequest(BaseModel):
    """Request model for search operations."""
    symbol_name: str = Field(..., description="Symbol name or pattern to search")
    tags_file: str = Field("tags", description="Path to tags file")
    match_type: Literal["exact", "partial", "regex"] = Field("exact", description="Type of matching")
    case_sensitive: bool = Field(True, description="Case-sensitive matching")
    limit: int = Field(50, description="Maximum results to return")


class OperationResult(BaseModel):
    """Standard result for operations."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None