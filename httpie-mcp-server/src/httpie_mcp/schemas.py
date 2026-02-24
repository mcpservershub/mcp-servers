"""Pydantic schemas for HTTPie MCP Server request validation and response modeling."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class HttpMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class AuthType(str, Enum):
    """Supported authentication types."""

    BASIC = "basic"
    BEARER = "bearer"
    DIGEST = "digest"


class OutputFormat(str, Enum):
    """Output format options."""

    ALL = "all"
    COLORS = "colors"
    FORMAT = "format"
    NONE = "none"


class RequestItem(BaseModel):
    """A single request item (header, query param, or data field)."""

    key: str = Field(..., description="The key name")
    value: str = Field(..., description="The value")
    separator: str = Field(
        "=",
        description="Separator type: ':' for headers, '==' for query params, '=' for data fields, ':=' for JSON data",
    )

    @field_validator("separator")
    @classmethod
    def validate_separator(cls, v: str) -> str:
        """Validate separator type."""
        valid_separators = [":", "==", "=", ":=", "@", "=@", ":=@"]
        if v not in valid_separators:
            raise ValueError(
                f"Invalid separator '{v}'. Must be one of: {', '.join(valid_separators)}"
            )
        return v


class HttpRequestInput(BaseModel):
    """Input schema for making HTTP requests."""

    url: str = Field(..., description="The target URL (e.g., 'https://api.example.com/users')")
    method: Optional[HttpMethod] = Field(
        None, description="HTTP method. If omitted, GET is used by default (POST if data is sent)"
    )
    headers: Optional[Dict[str, str]] = Field(
        None, description="Custom HTTP headers as key-value pairs"
    )
    query_params: Optional[Dict[str, str]] = Field(
        None, description="URL query parameters as key-value pairs"
    )
    json_data: Optional[Dict[str, Any]] = Field(
        None, description="JSON data to send in request body (sets Content-Type to application/json)"
    )
    form_data: Optional[Dict[str, str]] = Field(
        None,
        description="Form data to send (sets Content-Type to application/x-www-form-urlencoded)",
    )
    raw_data: Optional[str] = Field(
        None, description="Raw request body data (use for non-JSON/form content)"
    )
    auth: Optional[str] = Field(
        None, description="Authentication credentials in format 'username:password' or 'token'"
    )
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    timeout: Optional[int] = Field(
        None, description="Request timeout in seconds (0 means no timeout)"
    )
    follow_redirects: bool = Field(False, description="Follow 3xx redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    proxy: Optional[str] = Field(
        None, description="Proxy URL in format 'protocol:proxy_url' (e.g., 'http://proxy.example.com:8080')"
    )
    session: Optional[str] = Field(
        None, description="Session name for persistent session (reuses cookies, auth, headers)"
    )
    output_headers: bool = Field(True, description="Include response headers in output")
    output_body: bool = Field(True, description="Include response body in output")
    output_metadata: bool = Field(False, description="Include response metadata in output")
    verbose: bool = Field(False, description="Enable verbose output (shows request and response)")
    pretty_print: Optional[OutputFormat] = Field(
        OutputFormat.ALL, description="Pretty print output format"
    )
    cert: Optional[str] = Field(None, description="Path to client certificate file")
    cert_key: Optional[str] = Field(None, description="Path to client certificate private key")
    download: bool = Field(
        False, description="Download response body to a file instead of printing to stdout"
    )
    output_file: Optional[str] = Field(
        None, description="Save output to this file path instead of stdout"
    )
    max_redirects: Optional[int] = Field(
        None, description="Maximum number of redirects to follow (default: 30)"
    )
    offline: bool = Field(
        False, description="Build and print the request without actually sending it"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate and normalize URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        # Allow shorthand localhost notation (:3000, :/path)
        if v.startswith(":"):
            return v
        # Ensure URL has a scheme or will default to http://
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v


class HttpDownloadInput(BaseModel):
    """Input schema for downloading files via HTTP."""

    url: str = Field(..., description="The URL of the file to download")
    output_file: Optional[str] = Field(
        None,
        description="Output file path. If not specified, filename will be inferred from URL",
    )
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    resume: bool = Field(False, description="Resume an interrupted download")
    timeout: Optional[int] = Field(None, description="Download timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://")):
            return f"http://{v}"
        return v


class HttpResponse(BaseModel):
    """HTTP response model."""

    success: bool = Field(..., description="Whether the request was successful")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    headers: Optional[str] = Field(None, description="Response headers")
    body: Optional[str] = Field(None, description="Response body")
    metadata: Optional[str] = Field(None, description="Response metadata")
    error: Optional[str] = Field(None, description="Error message if request failed")
    command: str = Field(..., description="The HTTPie command that was executed")


class SessionRequestInput(BaseModel):
    """Input schema for session-based HTTP requests."""

    session_name: str = Field(..., description="Name of the session to use or create")
    url: str = Field(..., description="The target URL")
    method: Optional[HttpMethod] = Field(None, description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    form_data: Optional[Dict[str, str]] = Field(None, description="Form data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    read_only: bool = Field(
        False, description="Read session without updating it from request/response"
    )
    follow_redirects: bool = Field(False, description="Follow 3xx redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    verbose: bool = Field(False, description="Enable verbose output")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("session_name")
    @classmethod
    def validate_session_name(cls, v: str) -> str:
        """Validate session name."""
        if not v or not v.strip():
            raise ValueError("Session name cannot be empty")
        return v.strip()


# ============================================================================
# New Tool Schemas
# ============================================================================


class HttpMultipartUploadInput(BaseModel):
    """Input schema for multipart file uploads."""

    url: str = Field(..., description="The target URL")
    files: Dict[str, str] = Field(
        ..., description="Files to upload as field_name:file_path mapping"
    )
    form_data: Optional[Dict[str, str]] = Field(
        None, description="Additional form fields to include"
    )
    method: Optional[HttpMethod] = Field(HttpMethod.POST, description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    boundary: Optional[str] = Field(
        None, description="Custom boundary string for multipart/form-data"
    )
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    verbose: bool = Field(False, description="Enable verbose output")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate files dictionary."""
        if not v:
            raise ValueError("At least one file must be specified")
        return v


class HttpCheckStatusInput(BaseModel):
    """Input schema for status code validation requests."""

    url: str = Field(..., description="The target URL")
    method: Optional[HttpMethod] = Field(HttpMethod.GET, description="HTTP method")
    expected_status: List[int] = Field(
        [200], description="Expected HTTP status code(s)"
    )
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    form_data: Optional[Dict[str, str]] = Field(None, description="Form data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    follow_redirects: bool = Field(False, description="Follow 3xx redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("expected_status")
    @classmethod
    def validate_expected_status(cls, v: List[int]) -> List[int]:
        """Validate expected status codes."""
        if not v:
            raise ValueError("At least one expected status code must be specified")
        for status in v:
            if status < 100 or status >= 600:
                raise ValueError(f"Invalid HTTP status code: {status}")
        return v


class HttpStreamInput(BaseModel):
    """Input schema for streaming HTTP responses."""

    url: str = Field(..., description="The target URL")
    method: Optional[HttpMethod] = Field(HttpMethod.GET, description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    max_lines: Optional[int] = Field(
        None, description="Maximum number of lines to capture (None = unlimited)"
    )
    timeout: Optional[int] = Field(None, description="Stream timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("max_lines")
    @classmethod
    def validate_max_lines(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_lines."""
        if v is not None and v < 1:
            raise ValueError("max_lines must be at least 1")
        return v


class HttpValidateJsonSchemaInput(BaseModel):
    """Input schema for JSON schema validation."""

    url: str = Field(..., description="The target URL")
    json_schema: Dict[str, Any] = Field(..., description="JSON schema to validate against")
    method: Optional[HttpMethod] = Field(HttpMethod.GET, description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("json_schema")
    @classmethod
    def validate_json_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON schema."""
        if not v:
            raise ValueError("JSON schema cannot be empty")
        # Basic validation that it looks like a JSON schema
        if "type" not in v and "$schema" not in v:
            raise ValueError(
                "JSON schema must contain at least 'type' or '$schema' property"
            )
        return v


class HttpRetryInput(BaseModel):
    """Input schema for requests with retry logic."""

    url: str = Field(..., description="The target URL")
    method: Optional[HttpMethod] = Field(HttpMethod.GET, description="HTTP method")
    max_retries: int = Field(3, description="Maximum number of retry attempts")
    retry_delay_ms: int = Field(1000, description="Delay between retries in milliseconds")
    retry_on_status: List[int] = Field(
        [500, 502, 503, 504],
        description="HTTP status codes that trigger a retry"
    )
    exponential_backoff: bool = Field(
        True, description="Use exponential backoff for retry delays"
    )
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    form_data: Optional[Dict[str, str]] = Field(None, description="Form data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max_retries."""
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        if v > 10:
            raise ValueError("max_retries cannot exceed 10")
        return v

    @field_validator("retry_delay_ms")
    @classmethod
    def validate_retry_delay(cls, v: int) -> int:
        """Validate retry_delay_ms."""
        if v < 0:
            raise ValueError("retry_delay_ms must be non-negative")
        return v


class ExtractorType(str, Enum):
    """Types of extractors for response parsing."""

    JSONPATH = "jsonpath"
    REGEX = "regex"
    XPATH = "xpath"


class HttpResponseExtractInput(BaseModel):
    """Input schema for extracting data from HTTP responses."""

    url: str = Field(..., description="The target URL")
    extractor: ExtractorType = Field(
        ExtractorType.JSONPATH, description="Extraction method to use"
    )
    expressions: Dict[str, str] = Field(
        ..., description="Expressions to extract data as field_name:expression mapping"
    )
    method: Optional[HttpMethod] = Field(HttpMethod.GET, description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data to send")
    auth: Optional[str] = Field(None, description="Authentication credentials")
    auth_type: Optional[AuthType] = Field(AuthType.BASIC, description="Authentication type")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL."""
        if not v:
            raise ValueError("URL cannot be empty")
        if not v.startswith(("http://", "https://", ":")):
            return f"http://{v}"
        return v

    @field_validator("expressions")
    @classmethod
    def validate_expressions(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate expressions dictionary."""
        if not v:
            raise ValueError("At least one expression must be specified")
        return v


# Additional response models for new tools


class HttpCheckStatusResponse(BaseModel):
    """Response model for status check requests."""

    success: bool = Field(..., description="Whether the request was successful")
    status_code: Optional[int] = Field(None, description="Actual HTTP status code")
    status_check: str = Field(..., description="Status check result (passed/failed)")
    expected: List[int] = Field(..., description="Expected status codes")
    actual: Optional[int] = Field(None, description="Actual status code")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if request failed")
    command: str = Field(..., description="The HTTPie command that was executed")


class HttpRetryResponse(BaseModel):
    """Response model for retry requests."""

    success: bool = Field(..., description="Whether the request eventually succeeded")
    status_code: Optional[int] = Field(None, description="Final HTTP status code")
    attempts: int = Field(..., description="Total number of attempts made")
    retry_history: List[Dict[str, Any]] = Field(
        ..., description="History of retry attempts"
    )
    body: Optional[str] = Field(None, description="Response body")
    error: Optional[str] = Field(None, description="Error message if all retries failed")
    command: str = Field(..., description="The HTTPie command that was executed")


class HttpExtractResponse(BaseModel):
    """Response model for extraction requests."""

    success: bool = Field(..., description="Whether the request was successful")
    extracted_data: Dict[str, Any] = Field(..., description="Extracted data")
    extraction_errors: Dict[str, str] = Field(
        default_factory=dict, description="Errors during extraction"
    )
    status_code: Optional[int] = Field(None, description="HTTP status code")
    error: Optional[str] = Field(None, description="Error message if request failed")
    command: str = Field(..., description="The HTTPie command that was executed")


class HttpValidateJsonSchemaResponse(BaseModel):
    """Response model for JSON schema validation."""

    success: bool = Field(..., description="Whether the request was successful")
    validation_passed: bool = Field(..., description="Whether schema validation passed")
    validation_errors: List[str] = Field(
        default_factory=list, description="Validation errors if any"
    )
    status_code: Optional[int] = Field(None, description="HTTP status code")
    body: Optional[str] = Field(None, description="Response body")
    error: Optional[str] = Field(None, description="Error message if request failed")
    command: str = Field(..., description="The HTTPie command that was executed")
