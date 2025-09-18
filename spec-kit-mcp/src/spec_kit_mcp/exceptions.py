"""Custom exceptions for spec-kit MCP server."""

from typing import Optional, Dict, Any, List


class SpecKitError(Exception):
    """Base exception for spec-kit MCP server."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.details = details or {}
        self.suggestions = suggestions or []


class ConfigurationError(SpecKitError):
    """Configuration-related errors."""
    pass


class ValidationError(SpecKitError):
    """Input validation errors."""
    pass


class GitOperationError(SpecKitError):
    """Git operation failures."""
    pass


class ScriptExecutionError(SpecKitError):
    """Script execution failures."""
    pass


class TemplateProcessingError(SpecKitError):
    """Template processing errors."""
    pass


class NetworkError(SpecKitError):
    """Network-related errors (GitHub API, etc.)."""
    pass


class FileSystemError(SpecKitError):
    """File system operation errors."""
    pass


class FeatureNotFoundError(SpecKitError):
    """Feature branch or specification not found."""
    pass


class ConstitutionViolationError(SpecKitError):
    """Constitutional requirement violation."""
    pass