"""Input and output validators for ripgrep MCP tools."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SearchParams(BaseModel):
    """Parameters for basic search operation."""

    pattern: str = Field(..., min_length=1, description="Regex pattern to search")
    path: Optional[str] = Field(None, description="Directory or file to search in")
    case_sensitive: bool = Field(True, description="Case sensitivity")
    whole_word: bool = Field(False, description="Match whole words only")
    line_numbers: bool = Field(True, description="Include line numbers")
    max_results: Optional[int] = Field(100, ge=1, le=10000, description="Maximum results")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        if path.is_symlink():
            raise ValueError(f"Symbolic links not allowed: {v}")
        return str(path)

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v


class SearchByTypeParams(BaseModel):
    """Parameters for file type specific search."""

    pattern: str = Field(..., min_length=1, description="Regex pattern to search")
    file_type: str = Field(..., description="File type to search")
    path: Optional[str] = Field(None, description="Directory to search in")
    exclude_type: Optional[str] = Field(None, description="File types to exclude")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)

    @field_validator("file_type", "exclude_type")
    @classmethod
    def validate_file_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = {
            "python", "py", "rust", "rs", "javascript", "js", "typescript", "ts",
            "java", "cpp", "c", "go", "ruby", "rb", "php", "swift", "kotlin",
            "scala", "haskell", "hs", "erlang", "elixir", "clojure", "lisp",
            "perl", "lua", "r", "matlab", "julia", "fortran", "pascal", "ada",
            "html", "css", "xml", "json", "yaml", "toml", "ini", "markdown", "md",
            "tex", "latex", "rst", "asciidoc", "org", "sql", "sh", "bash", "zsh",
            "fish", "powershell", "ps1", "bat", "cmd", "make", "cmake", "docker",
            "dockerfile", "k8s", "kubernetes", "terraform", "tf", "ansible"
        }
        if v.lower() not in valid_types:
            valid_types_str = ", ".join(sorted(valid_types))
            raise ValueError(f"Unknown file type: {v}. Valid types: {valid_types_str}")
        return v.lower()


class SearchWithContextParams(BaseModel):
    """Parameters for search with context."""

    pattern: str = Field(..., min_length=1, description="Search pattern")
    before_context: int = Field(2, ge=0, le=10, description="Lines before match")
    after_context: int = Field(2, ge=0, le=10, description="Lines after match")
    path: Optional[str] = Field(None, description="Search path")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)


class ReplaceParams(BaseModel):
    """Parameters for find and replace."""

    pattern: str = Field(..., min_length=1, description="Pattern to find")
    replacement: str = Field(..., description="Replacement text")
    path: Optional[str] = Field(None, description="Target path")
    dry_run: bool = Field(True, description="Preview changes without applying")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)


class ListFilesParams(BaseModel):
    """Parameters for file listing."""

    pattern: Optional[str] = Field(None, description="Filter by file name pattern")
    file_type: Optional[str] = Field(None, description="Filter by file type")
    path: Optional[str] = Field(None, description="Search directory")
    include_hidden: bool = Field(False, description="Include hidden files")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Path must be a directory: {v}")
        return str(path)


class SearchMultilineParams(BaseModel):
    """Parameters for multiline search."""

    pattern: str = Field(..., min_length=1, description="Multiline regex pattern")
    path: Optional[str] = Field(None, description="Search path")
    pcre2: bool = Field(False, description="Use PCRE2 engine")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)


class StatsParams(BaseModel):
    """Parameters for search statistics."""

    pattern: str = Field(..., min_length=1, description="Pattern to analyze")
    path: Optional[str] = Field(None, description="Target path")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)


class SearchBinaryParams(BaseModel):
    """Parameters for binary file search."""

    pattern: str = Field(..., min_length=1, description="Pattern to search")
    path: Optional[str] = Field(None, description="Target path")
    encoding: str = Field("utf-8", description="File encoding")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        return str(path)

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        valid_encodings = {"utf-8", "utf-16", "utf-16le", "utf-16be", "ascii", "latin-1", "iso-8859-1"}
        if v.lower() not in valid_encodings:
            raise ValueError(f"Unsupported encoding: {v}")
        return v.lower()


class SearchResult(BaseModel):
    """Search result model."""

    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    match_text: str
    context_before: Optional[List[str]] = None
    context_after: Optional[List[str]] = None


class ReplaceResult(BaseModel):
    """Replace result model."""

    file_path: str
    line_number: int
    original: str
    replacement: str
    applied: bool = False


class StatsResult(BaseModel):
    """Statistics result model."""

    total_matches: int
    files_searched: int
    files_with_matches: int
    time_taken_ms: float
    pattern: str


def validate_ripgrep_available() -> bool:
    """Check if ripgrep is available in the system."""
    import shutil
    
    rg_path = shutil.which("rg")
    if not rg_path:
        # Check common locations
        common_paths = ["/usr/bin/rg", "/usr/local/bin/rg", "/opt/homebrew/bin/rg"]
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return True
        return False
    return True