"""HTTPie MCP Server - FastMCP-based server exposing HTTPie CLI as MCP tools."""

import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .httpie_client import HTTPieClient, HTTPieClientError, HTTPieNotFoundError
from .schemas import (
    AuthType,
    ExtractorType,
    HttpDownloadInput,
    HttpMethod,
    HttpRequestInput,
    OutputFormat,
    SessionRequestInput,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],  # Log to stderr to avoid interfering with STDIO
)
logger = logging.getLogger(__name__)

# Initialize FastMCP application
app = FastMCP("httpie-mcp-server")

# Global HTTPie client instance
httpie_client: Optional[HTTPieClient] = None


def get_httpie_client() -> HTTPieClient:
    """
    Get or create HTTPie client instance.

    Returns:
        HTTPie client instance

    Raises:
        HTTPieNotFoundError: If HTTPie is not installed
    """
    global httpie_client
    if httpie_client is None:
        try:
            httpie_client = HTTPieClient(verify_installation=True)
            logger.info("HTTPie client initialized successfully")
        except HTTPieNotFoundError as e:
            logger.error(f"HTTPie not found: {e}")
            raise
    return httpie_client


@app.tool()
def http_request(
    url: str,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    raw_data: Optional[str] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    follow_redirects: bool = False,
    verify_ssl: bool = True,
    proxy: Optional[str] = None,
    session: Optional[str] = None,
    output_headers: bool = True,
    output_body: bool = True,
    output_metadata: bool = False,
    verbose: bool = False,
    pretty_print: str = "all",
    cert: Optional[str] = None,
    cert_key: Optional[str] = None,
    download: bool = False,
    output_file: Optional[str] = None,
    max_redirects: Optional[int] = None,
    offline: bool = False,
) -> Dict[str, Any]:
    """
    Make an HTTP request using HTTPie CLI.

    This tool provides a comprehensive interface to HTTPie's functionality, allowing you to:
    - Make HTTP requests with any method (GET, POST, PUT, DELETE, etc.)
    - Send JSON or form data
    - Set custom headers and query parameters
    - Use authentication (Basic, Bearer, Digest)
    - Configure SSL/TLS options
    - Control output formatting and verbosity
    - Use sessions for persistent state
    - Work with proxies and redirects

    Args:
        url: Target URL (e.g., 'https://api.example.com/users' or ':3000' for localhost:3000)
        method: HTTP method (GET, POST, PUT, DELETE, etc.). Auto-detected if omitted
        headers: Custom HTTP headers as key-value pairs (e.g., {"Authorization": "Bearer token"})
        query_params: URL query parameters (e.g., {"page": "1", "limit": "10"})
        json_data: JSON data to send in request body (e.g., {"name": "John", "age": 30})
        form_data: Form data (sets Content-Type to application/x-www-form-urlencoded)
        raw_data: Raw request body data for non-JSON/form content
        auth: Authentication credentials ('username:password' or 'token')
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        timeout: Request timeout in seconds (0 = no timeout)
        follow_redirects: Follow 3xx redirects automatically
        verify_ssl: Verify SSL certificates (set False to skip verification)
        proxy: Proxy URL (e.g., 'http://proxy.example.com:8080')
        session: Session name for persistent cookies/auth/headers
        output_headers: Include response headers in output
        output_body: Include response body in output
        output_metadata: Include response metadata in output
        verbose: Enable verbose output (shows full request and response)
        pretty_print: Output formatting ('all', 'colors', 'format', 'none')
        cert: Path to client SSL certificate file
        cert_key: Path to client SSL certificate private key
        download: Download response to file instead of returning in output
        output_file: File path to save output (alternative to download)
        max_redirects: Maximum number of redirects to follow (default: 30)
        offline: Build and print request without sending it (dry-run mode)

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded
        - status_code (int): HTTP status code
        - headers (str): Response headers (if output_headers=True)
        - body (str): Response body (if output_body=True)
        - metadata (str): Response metadata (if output_metadata=True)
        - error (str): Error message if request failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Simple GET request
        http_request(url="https://httpbin.org/get")

        # POST JSON data
        http_request(
            url="https://httpbin.org/post",
            method="POST",
            json_data={"name": "Alice", "active": True}
        )

        # GET with authentication and headers
        http_request(
            url="https://api.github.com/user",
            auth="username:token",
            auth_type="basic",
            headers={"Accept": "application/vnd.github.v3+json"}
        )

        # POST form data with file download
        http_request(
            url="https://httpbin.org/post",
            method="POST",
            form_data={"field1": "value1"},
            download=True,
            output_file="/tmp/response.json"
        )
    """
    try:
        # Get HTTPie client
        client = get_httpie_client()

        # Build request input
        request_input = HttpRequestInput(
            url=url,
            method=HttpMethod(method) if method else None,
            headers=headers,
            query_params=query_params,
            json_data=json_data,
            form_data=form_data,
            raw_data=raw_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            proxy=proxy,
            session=session,
            output_headers=output_headers,
            output_body=output_body,
            output_metadata=output_metadata,
            verbose=verbose,
            pretty_print=OutputFormat(pretty_print),
            cert=cert,
            cert_key=cert_key,
            download=download,
            output_file=output_file,
            max_redirects=max_redirects,
            offline=offline,
        )

        # Execute request
        response = client.make_request(request_input)

        # Return as dict for MCP
        return response.model_dump()

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_request tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_download(
    url: str,
    output_file: Optional[str] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    resume: bool = False,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Download a file from a URL using HTTPie.

    This tool is optimized for file downloads and provides:
    - Automatic filename detection from URL or Content-Disposition header
    - Resume capability for interrupted downloads
    - Progress tracking and proper handling of large files
    - Authentication support
    - Custom headers for specialized download scenarios

    Args:
        url: URL of the file to download
        output_file: Output file path (auto-detected from URL if not specified)
        auth: Authentication credentials ('username:password' or 'token')
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        resume: Resume an interrupted download (requires output_file to be specified)
        timeout: Download timeout in seconds
        verify_ssl: Verify SSL certificates
        headers: Custom HTTP headers (e.g., {"Range": "bytes=0-1023"})

    Returns:
        Dictionary containing:
        - success (bool): Whether the download succeeded
        - status_code (int): HTTP status code
        - body (str): Download progress/status information
        - error (str): Error message if download failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Simple download
        http_download(url="https://example.com/file.zip")

        # Download to specific location
        http_download(
            url="https://example.com/file.zip",
            output_file="/tmp/myfile.zip"
        )

        # Download with authentication
        http_download(
            url="https://example.com/private/file.pdf",
            auth="user:pass",
            output_file="/tmp/document.pdf"
        )

        # Resume interrupted download
        http_download(
            url="https://example.com/largefile.iso",
            output_file="/tmp/largefile.iso",
            resume=True
        )
    """
    try:
        # Get HTTPie client
        client = get_httpie_client()

        # Build download input
        download_input = HttpDownloadInput(
            url=url,
            output_file=output_file,
            auth=auth,
            auth_type=AuthType(auth_type),
            resume=resume,
            timeout=timeout,
            verify_ssl=verify_ssl,
            headers=headers,
        )

        # Execute download
        response = client.download_file(download_input)

        # Return as dict for MCP
        return response.model_dump()

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_download tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_session_request(
    session_name: str,
    url: str,
    method: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    read_only: bool = False,
    follow_redirects: bool = False,
    verify_ssl: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Make an HTTP request using HTTPie sessions for state persistence.

    Sessions allow you to persist certain request elements (cookies, custom headers,
    authentication) across multiple requests. This is useful for:
    - Maintaining login state across API calls
    - Reusing authentication credentials
    - Preserving custom headers for multiple requests
    - Working with cookie-based sessions

    Session data is stored in HTTPie's config directory and can be shared across
    multiple MCP tool invocations.

    Args:
        session_name: Name of the session to use/create (e.g., 'github-api', 'test-session')
        url: Target URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Custom HTTP headers (persisted in session unless read_only=True)
        json_data: JSON data to send in request body
        form_data: Form data to send
        auth: Authentication credentials (persisted in session unless read_only=True)
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        read_only: Read session without updating it from request/response
        follow_redirects: Follow 3xx redirects
        verify_ssl: Verify SSL certificates
        verbose: Enable verbose output

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded
        - status_code (int): HTTP status code
        - headers (str): Response headers
        - body (str): Response body
        - error (str): Error message if request failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Create session with authentication
        http_session_request(
            session_name="my-api",
            url="https://api.example.com/login",
            method="POST",
            json_data={"username": "user", "password": "pass"}
        )

        # Reuse session for subsequent requests
        http_session_request(
            session_name="my-api",
            url="https://api.example.com/user/profile"
        )

        # Read session without updating it
        http_session_request(
            session_name="my-api",
            url="https://api.example.com/data",
            read_only=True
        )
    """
    try:
        # Get HTTPie client
        client = get_httpie_client()

        # Build session request input
        session_input = SessionRequestInput(
            session_name=session_name,
            url=url,
            method=HttpMethod(method) if method else None,
            headers=headers,
            json_data=json_data,
            form_data=form_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            read_only=read_only,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            verbose=verbose,
        )

        # Execute session request
        response = client.session_request(session_input)

        # Return as dict for MCP
        return response.model_dump()

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_session_request tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_multipart_upload(
    url: str,
    files: Dict[str, str],
    form_data: Optional[Dict[str, str]] = None,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    boundary: Optional[str] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Upload files using multipart/form-data encoding.

    This tool is specifically designed for file uploads and supports:
    - Single or multiple file uploads
    - Mixed file and form data in the same request
    - Custom multipart boundaries
    - Authentication for protected endpoints
    - Progress tracking with verbose mode

    Args:
        url: Target URL for the upload
        files: Files to upload as field_name:file_path mapping (e.g., {"avatar": "/tmp/photo.jpg"})
        form_data: Additional form fields to include with the upload
        method: HTTP method (typically POST or PUT)
        headers: Custom HTTP headers
        auth: Authentication credentials ('username:password' or 'token')
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        boundary: Custom boundary string for multipart/form-data
        timeout: Upload timeout in seconds
        verify_ssl: Verify SSL certificates
        verbose: Enable verbose output for progress tracking

    Returns:
        Dictionary containing:
        - success (bool): Whether the upload succeeded
        - status_code (int): HTTP status code
        - body (str): Response body
        - error (str): Error message if upload failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Upload single file
        http_multipart_upload(
            url="https://api.example.com/upload",
            files={"document": "/tmp/report.pdf"}
        )

        # Upload with form data
        http_multipart_upload(
            url="https://api.example.com/profile",
            files={"avatar": "/tmp/photo.jpg"},
            form_data={"name": "John Doe", "bio": "Developer"}
        )

        # Upload to authenticated endpoint
        http_multipart_upload(
            url="https://api.example.com/upload",
            files={"file": "/tmp/data.csv"},
            auth="user:token",
            verbose=True
        )
    """
    try:
        from .schemas import HttpMultipartUploadInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build upload input
        upload_input = HttpMultipartUploadInput(
            url=url,
            files=files,
            form_data=form_data,
            method=HttpMethod(method),
            headers=headers,
            auth=auth,
            auth_type=AuthType(auth_type),
            boundary=boundary,
            timeout=timeout,
            verify_ssl=verify_ssl,
            verbose=verbose,
        )

        # Execute upload
        response = client.multipart_upload(upload_input)

        # Return as dict for MCP
        return response.model_dump()

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_multipart_upload tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_check_status(
    url: str,
    expected_status: List[int] = [200],
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    follow_redirects: bool = False,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    Make an HTTP request and validate the status code matches expected values.

    This tool is ideal for:
    - API health checks and monitoring
    - Smoke tests in CI/CD pipelines
    - Quick validation without parsing full responses
    - Testing redirect configurations
    - Rate limit detection

    Args:
        url: Target URL to check
        expected_status: List of acceptable HTTP status codes (default: [200])
        method: HTTP method to use
        headers: Custom HTTP headers
        json_data: JSON data to send in request body
        form_data: Form data to send
        auth: Authentication credentials
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        timeout: Request timeout in seconds
        follow_redirects: Follow 3xx redirects
        verify_ssl: Verify SSL certificates

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded AND status matched
        - status_code (int): Actual HTTP status code
        - status_check (str): 'passed' or 'failed'
        - expected (list): Expected status codes
        - actual (int): Actual status code
        - response_time_ms (int): Response time in milliseconds
        - error (str): Error message if request failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Simple health check
        http_check_status(url="https://api.example.com/health")

        # Check redirect setup
        http_check_status(
            url="http://example.com/old-url",
            expected_status=[301, 302],
            follow_redirects=False
        )

        # Check API with timeout
        http_check_status(
            url="https://api.example.com/status",
            expected_status=[200, 204],
            timeout=5
        )
    """
    try:
        from .schemas import HttpCheckStatusInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build check input
        check_input = HttpCheckStatusInput(
            url=url,
            method=HttpMethod(method),
            expected_status=expected_status,
            headers=headers,
            json_data=json_data,
            form_data=form_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
        )

        # Execute status check
        response = client.check_status(check_input)

        # Return as dict for MCP
        result: Dict[str, Any] = response.model_dump()
        return result

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_check_status tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_stream(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    max_lines: Optional[int] = None,
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    Stream HTTP response line by line (for SSE, streaming APIs, logs).

    This tool is essential for:
    - Server-Sent Events (SSE)
    - Streaming APIs (OpenAI, Claude, etc.)
    - Real-time log monitoring
    - Long-lived connections
    - Progressive data feeds

    Args:
        url: Target URL to stream from
        method: HTTP method (typically GET or POST)
        headers: Custom HTTP headers
        json_data: JSON data to send (for POST streaming requests)
        auth: Authentication credentials
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        max_lines: Maximum number of lines to capture (None = unlimited)
        timeout: Stream timeout in seconds
        verify_ssl: Verify SSL certificates

    Returns:
        Dictionary containing:
        - success (bool): Whether the streaming succeeded
        - body (str): Streamed content (limited by max_lines if specified)
        - error (str): Error message if streaming failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Stream server logs
        http_stream(
            url="https://api.example.com/logs/stream",
            max_lines=100
        )

        # Stream OpenAI completion
        http_stream(
            url="https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={"Authorization": "Bearer sk-..."},
            json_data={"model": "gpt-4", "stream": True, "messages": [...]},
            max_lines=50
        )

        # Monitor real-time events
        http_stream(
            url="https://api.example.com/events",
            timeout=30,
            max_lines=20
        )
    """
    try:
        from .schemas import HttpStreamInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build stream input
        stream_input = HttpStreamInput(
            url=url,
            method=HttpMethod(method),
            headers=headers,
            json_data=json_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            max_lines=max_lines,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        # Execute streaming
        response = client.stream_response(stream_input)

        # Return as dict for MCP
        return response.model_dump()

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_stream tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_validate_json_schema(
    url: str,
    json_schema: Dict[str, Any],
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    Make an HTTP request and validate the response against a JSON schema.

    This tool is perfect for:
    - API contract testing
    - Response structure validation
    - Integration testing
    - Regression testing for API changes
    - Schema compliance verification

    Args:
        url: Target URL
        json_schema: JSON schema to validate response against
        method: HTTP method
        headers: Custom HTTP headers
        json_data: JSON data to send in request
        auth: Authentication credentials
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded
        - validation_passed (bool): Whether schema validation passed
        - validation_errors (list): List of validation errors (if any)
        - status_code (int): HTTP status code
        - body (str): Response body
        - error (str): Error message if request failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Validate user API response
        http_validate_json_schema(
            url="https://api.example.com/users/123",
            json_schema={
                "type": "object",
                "required": ["id", "name", "email"],
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                }
            }
        )

        # Validate list response
        http_validate_json_schema(
            url="https://api.example.com/posts",
            json_schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "title"],
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"}
                    }
                }
            }
        )
    """
    try:
        from .schemas import HttpValidateJsonSchemaInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build validation input
        validate_input = HttpValidateJsonSchemaInput(
            url=url,
            json_schema=json_schema,
            method=HttpMethod(method),
            headers=headers,
            json_data=json_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        # Execute validation
        response = client.validate_json_schema(validate_input)

        # Return as dict for MCP
        result: Dict[str, Any] = response.model_dump()
        return result

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_validate_json_schema tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_retry(
    url: str,
    method: str = "GET",
    max_retries: int = 3,
    retry_delay_ms: int = 1000,
    retry_on_status: List[int] = [500, 502, 503, 504],
    exponential_backoff: bool = True,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, str]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    Make an HTTP request with automatic retry logic for resilience.

    This tool handles:
    - Transient server errors (5xx)
    - Network timeouts and failures
    - Rate limiting (429)
    - Exponential backoff strategies
    - Custom retry conditions

    Args:
        url: Target URL
        method: HTTP method
        max_retries: Maximum number of retry attempts (0-10)
        retry_delay_ms: Initial delay between retries in milliseconds
        retry_on_status: HTTP status codes that trigger a retry
        exponential_backoff: Use exponential backoff (delay doubles each retry)
        headers: Custom HTTP headers
        json_data: JSON data to send
        form_data: Form data to send
        auth: Authentication credentials
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates

    Returns:
        Dictionary containing:
        - success (bool): Whether a request eventually succeeded
        - status_code (int): Final HTTP status code
        - attempts (int): Total number of attempts made
        - retry_history (list): History of all retry attempts with delays
        - body (str): Response body (from successful attempt)
        - error (str): Error message if all retries failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Retry on server errors
        http_retry(
            url="https://api.example.com/data",
            max_retries=5,
            retry_delay_ms=1000,
            exponential_backoff=True
        )

        # Retry with rate limit handling
        http_retry(
            url="https://api.example.com/resource",
            max_retries=3,
            retry_on_status=[429, 500, 502, 503, 504],
            retry_delay_ms=2000
        )

        # POST with retry
        http_retry(
            url="https://api.example.com/submit",
            method="POST",
            json_data={"data": "value"},
            max_retries=3
        )
    """
    try:
        from .schemas import HttpRetryInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build retry input
        retry_input = HttpRetryInput(
            url=url,
            method=HttpMethod(method),
            max_retries=max_retries,
            retry_delay_ms=retry_delay_ms,
            retry_on_status=retry_on_status,
            exponential_backoff=exponential_backoff,
            headers=headers,
            json_data=json_data,
            form_data=form_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        # Execute with retry
        response = client.retry_request(retry_input)

        # Return as dict for MCP
        result: Dict[str, Any] = response.model_dump()
        return result

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_retry tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


@app.tool()
def http_response_extract(
    url: str,
    expressions: Dict[str, str],
    extractor: str = "jsonpath",
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    auth: Optional[str] = None,
    auth_type: str = "basic",
    timeout: Optional[int] = None,
    verify_ssl: bool = True,
) -> Dict[str, Any]:
    """
    Make an HTTP request and extract specific data from the response.

    This tool supports:
    - JSONPath expressions for JSON responses
    - Regular expressions for text responses
    - Multiple field extraction in one request
    - Data transformation and parsing

    Args:
        url: Target URL
        expressions: Expressions to extract data as field_name:expression mapping
        extractor: Extraction method ('jsonpath', 'regex', or 'xpath')
        method: HTTP method
        headers: Custom HTTP headers
        json_data: JSON data to send
        auth: Authentication credentials
        auth_type: Authentication type ('basic', 'bearer', or 'digest')
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded
        - extracted_data (dict): Extracted data as field_name:value mapping
        - extraction_errors (dict): Errors during extraction (if any)
        - status_code (int): HTTP status code
        - error (str): Error message if request failed
        - command (str): The HTTPie command that was executed

    Examples:
        # Extract user data with JSONPath
        http_response_extract(
            url="https://api.example.com/user/123",
            extractor="jsonpath",
            expressions={
                "user_id": "$.id",
                "email": "$.email",
                "name": "$.profile.full_name"
            }
        )

        # Extract with regex
        http_response_extract(
            url="https://example.com/page",
            extractor="regex",
            expressions={
                "title": r"<title>(.*?)</title>",
                "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
            }
        )

        # Chain extraction from API
        http_response_extract(
            url="https://api.example.com/auth/login",
            method="POST",
            json_data={"user": "test", "pass": "test123"},
            expressions={
                "token": "$.data.token",
                "user_id": "$.data.user.id",
                "expires": "$.data.expires_at"
            }
        )
    """
    try:
        from .schemas import HttpResponseExtractInput

        # Get HTTPie client
        client = get_httpie_client()

        # Build extract input
        extract_input = HttpResponseExtractInput(
            url=url,
            extractor=ExtractorType(extractor),
            expressions=expressions,
            method=HttpMethod(method),
            headers=headers,
            json_data=json_data,
            auth=auth,
            auth_type=AuthType(auth_type),
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        # Execute extraction
        response = client.extract_response(extract_input)

        # Return as dict for MCP
        result: Dict[str, Any] = response.model_dump()
        return result

    except HTTPieNotFoundError as e:
        logger.error(f"HTTPie not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": "N/A - HTTPie not found",
        }
    except HTTPieClientError as e:
        logger.error(f"HTTPie client error: {e}")
        return {
            "success": False,
            "error": f"HTTPie execution error: {str(e)}",
            "command": "N/A - Error before execution",
        }
    except Exception as e:
        logger.error(f"Unexpected error in http_response_extract tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": "N/A - Unexpected error",
        }


def main() -> None:
    """
    Main entry point for the HTTPie MCP Server.

    Starts the FastMCP server in STDIO mode for MCP client communication.
    """
    try:
        logger.info("Starting HTTPie MCP Server...")
        logger.info("Server will communicate via STDIO for MCP protocol")

        # Verify HTTPie is available before starting server
        try:
            get_httpie_client()
        except HTTPieNotFoundError as e:
            logger.warning(
                f"HTTPie not found during startup: {e}. "
                "Server will start but tools will return errors until HTTPie is installed."
            )

        # Start the FastMCP server
        app.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error starting server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
