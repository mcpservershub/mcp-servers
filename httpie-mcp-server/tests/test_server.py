"""
Comprehensive test suite for HTTPie MCP Server.

Tests cover:
- Schema validation
- HTTPie client wrapper functionality
- MCP tool endpoints
- Error handling and edge cases
"""

import json
import subprocess
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from httpie_mcp.httpie_client import (
    HTTPieClient,
    HTTPieClientError,
    HTTPieExecutionError,
    HTTPieNotFoundError,
)
from httpie_mcp.schemas import (
    AuthType,
    ExtractorType,
    HttpCheckStatusResponse,
    HttpDownloadInput,
    HttpExtractResponse,
    HttpMethod,
    HttpRequestInput,
    HttpResponse,
    HttpRetryResponse,
    HttpValidateJsonSchemaResponse,
    OutputFormat,
    SessionRequestInput,
)
from httpie_mcp.server import (
    http_check_status,
    http_download,
    http_multipart_upload,
    http_request,
    http_response_extract,
    http_retry,
    http_session_request,
    http_stream,
    http_validate_json_schema,
)


class TestSchemas:
    """Test Pydantic schema validation."""

    def test_http_request_input_valid(self):
        """Test valid HTTP request input."""
        data = HttpRequestInput(
            url="https://api.example.com/users",
            method=HttpMethod.GET,
            headers={"Authorization": "Bearer token123"},
            query_params={"page": "1", "limit": "10"},
        )
        assert data.url == "https://api.example.com/users"
        assert data.method == HttpMethod.GET
        assert data.headers == {"Authorization": "Bearer token123"}
        assert data.query_params == {"page": "1", "limit": "10"}

    def test_http_request_input_url_normalization(self):
        """Test URL normalization (adding http:// scheme)."""
        data = HttpRequestInput(url="example.com")
        assert data.url == "http://example.com"

    def test_http_request_input_localhost_shorthand(self):
        """Test localhost shorthand notation."""
        data = HttpRequestInput(url=":3000")
        assert data.url == ":3000"

    def test_http_request_input_invalid_url(self):
        """Test that empty URL raises validation error."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            HttpRequestInput(url="")

    def test_http_download_input_valid(self):
        """Test valid HTTP download input."""
        data = HttpDownloadInput(
            url="https://example.com/file.zip", output_file="/tmp/file.zip", resume=True
        )
        assert data.url == "https://example.com/file.zip"
        assert data.output_file == "/tmp/file.zip"
        assert data.resume is True

    def test_session_request_input_valid(self):
        """Test valid session request input."""
        data = SessionRequestInput(
            session_name="my-session",
            url="https://api.example.com/data",
            method=HttpMethod.POST,
            json_data={"key": "value"},
            read_only=False,
        )
        assert data.session_name == "my-session"
        assert data.url == "https://api.example.com/data"
        assert data.method == HttpMethod.POST
        assert data.json_data == {"key": "value"}
        assert data.read_only is False

    def test_session_request_input_invalid_session_name(self):
        """Test that empty session name raises validation error."""
        with pytest.raises(ValueError, match="Session name cannot be empty"):
            SessionRequestInput(session_name="", url="https://example.com")

    def test_http_response_model(self):
        """Test HTTP response model."""
        response = HttpResponse(
            success=True,
            status_code=200,
            headers="HTTP/1.1 200 OK\nContent-Type: application/json",
            body='{"message": "success"}',
            error=None,
            command="http GET https://example.com",
        )
        assert response.success is True
        assert response.status_code == 200
        assert "Content-Type: application/json" in response.headers
        assert response.body == '{"message": "success"}'
        assert response.error is None


class TestHTTPieClient:
    """Test HTTPie client wrapper."""

    @patch("subprocess.run")
    def test_verify_httpie_installed_success(self, mock_run):
        """Test successful HTTPie installation verification."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="HTTPie 3.2.2", stderr=""
        )

        client = HTTPieClient(verify_installation=True)
        assert client is not None

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["http", "--version"]

    @patch("subprocess.run")
    def test_verify_httpie_not_installed(self, mock_run):
        """Test HTTPie not installed scenario."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(HTTPieNotFoundError, match="HTTPie executable 'http' not found"):
            HTTPieClient(verify_installation=True)

    @patch("subprocess.run")
    def test_make_request_simple_get(self, mock_run):
        """Test simple GET request."""
        mock_run.side_effect = [
            # First call: version check
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            # Second call: actual request
            MagicMock(
                returncode=0,
                stdout="HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\"status\":\"ok\"}",
                stderr="",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(url="https://httpbin.org/get", method=HttpMethod.GET)
        response = client.make_request(request)

        assert response.success is True
        assert response.status_code == 200
        assert "application/json" in response.headers
        assert '{"status":"ok"}' in response.body

    @patch("subprocess.run")
    def test_make_request_post_json(self, mock_run):
        """Test POST request with JSON data."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=0,
                stdout="HTTP/1.1 201 Created\n\n{\"id\":123}",
                stderr="",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(
            url="https://httpbin.org/post",
            method=HttpMethod.POST,
            json_data={"name": "test", "value": 42},
        )
        response = client.make_request(request)

        assert response.success is True
        assert response.status_code == 201

    @patch("subprocess.run")
    def test_make_request_with_auth(self, mock_run):
        """Test request with authentication."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=0, stdout="HTTP/1.1 200 OK\n\n{\"authenticated\":true}", stderr=""
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(
            url="https://api.example.com/protected",
            auth="user:pass",
            auth_type=AuthType.BASIC,
        )
        response = client.make_request(request)

        assert response.success is True
        # Verify auth was added to command
        call_args = mock_run.call_args_list[1][0][0]
        assert "--auth" in call_args
        assert "user:pass" in call_args

    @patch("subprocess.run")
    def test_make_request_with_headers(self, mock_run):
        """Test request with custom headers."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(returncode=0, stdout="HTTP/1.1 200 OK\n\n{}", stderr=""),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(
            url="https://api.example.com/data",
            headers={"X-Custom-Header": "CustomValue", "Authorization": "Bearer token"},
        )
        response = client.make_request(request)

        assert response.success is True
        # Verify headers were added to command
        call_args = mock_run.call_args_list[1][0][0]
        assert "X-Custom-Header:CustomValue" in call_args
        assert "Authorization:Bearer token" in call_args

    @patch("subprocess.run")
    def test_make_request_timeout(self, mock_run):
        """Test request timeout handling."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            subprocess.TimeoutExpired(cmd=["http"], timeout=5),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(url="https://httpbin.org/delay/10", timeout=5)

        with pytest.raises(HTTPieExecutionError, match="timed out"):
            client.make_request(request)

    @patch("subprocess.run")
    def test_make_request_error_response(self, mock_run):
        """Test handling of HTTP error responses."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=4,  # HTTPie returns 4 for 4xx errors with --check-status
                stdout="HTTP/1.1 404 Not Found\n\n{\"error\":\"Not found\"}",
                stderr="http: error: HTTP 404 Not Found",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(url="https://httpbin.org/status/404")
        response = client.make_request(request)

        assert response.success is False
        assert response.status_code == 404
        assert response.error is not None

    @patch("subprocess.run")
    def test_sanitize_header_value(self, mock_run):
        """Test header value sanitization."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(returncode=0, stdout="HTTP/1.1 200 OK\n\n{}", stderr=""),
        ]

        client = HTTPieClient(verify_installation=True)

        # Test with potentially dangerous characters
        dangerous_value = 'test\nInjection\rAttempt"value'
        sanitized = client._sanitize_header_value(dangerous_value)

        # Should remove newlines and escape quotes
        assert "\n" not in sanitized
        assert "\r" not in sanitized
        assert '\\"' in sanitized  # Quotes should be escaped

    @patch("subprocess.run")
    def test_download_file(self, mock_run):
        """Test file download."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=0,
                stdout="Downloading to file.zip\nDone. 1.5 MB in 2.3s",
                stderr="",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        download = HttpDownloadInput(
            url="https://example.com/file.zip", output_file="/tmp/file.zip"
        )
        response = client.download_file(download)

        assert response.success is True
        # Verify download flag was added
        call_args = mock_run.call_args_list[1][0][0]
        assert "--download" in call_args
        assert "--output" in call_args
        assert "/tmp/file.zip" in call_args

    @patch("subprocess.run")
    def test_session_request(self, mock_run):
        """Test session request."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=0,
                stdout="HTTP/1.1 200 OK\nSet-Cookie: session=abc123\n\n{}",
                stderr="",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        session_req = SessionRequestInput(
            session_name="test-session",
            url="https://api.example.com/login",
            method=HttpMethod.POST,
            json_data={"username": "user"},
        )
        response = client.session_request(session_req)

        assert response.success is True
        # Verify session flag was added
        call_args = mock_run.call_args_list[1][0][0]
        assert "--session" in call_args
        assert "test-session" in call_args


class TestMCPTools:
    """Test MCP tool endpoints."""

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_request_tool_success(self, mock_get_client):
        """Test http_request tool with successful request."""
        mock_client = MagicMock()
        mock_client.make_request.return_value = HttpResponse(
            success=True,
            status_code=200,
            headers="HTTP/1.1 200 OK",
            body='{"result": "ok"}',
            error=None,
            command="http GET https://example.com",
        )
        mock_get_client.return_value = mock_client

        result = http_request(url="https://example.com")

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["body"] == '{"result": "ok"}'
        assert result["error"] is None

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_request_tool_with_params(self, mock_get_client):
        """Test http_request tool with various parameters."""
        mock_client = MagicMock()
        mock_client.make_request.return_value = HttpResponse(
            success=True,
            status_code=201,
            headers="HTTP/1.1 201 Created",
            body='{"id": 123}',
            error=None,
            command="http POST https://example.com/api",
        )
        mock_get_client.return_value = mock_client

        result = http_request(
            url="https://example.com/api",
            method="POST",
            json_data={"name": "test"},
            headers={"Authorization": "Bearer token"},
            timeout=30,
            follow_redirects=True,
        )

        assert result["success"] is True
        assert result["status_code"] == 201
        mock_client.make_request.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_request_tool_httpie_not_found(self, mock_get_client):
        """Test http_request tool when HTTPie is not installed."""
        mock_get_client.side_effect = HTTPieNotFoundError("HTTPie not found")

        result = http_request(url="https://example.com")

        assert result["success"] is False
        assert "HTTPie not found" in result["error"]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_download_tool_success(self, mock_get_client):
        """Test http_download tool with successful download."""
        mock_client = MagicMock()
        mock_client.download_file.return_value = HttpResponse(
            success=True,
            status_code=200,
            body="Downloaded successfully",
            error=None,
            command="http --download https://example.com/file.zip",
        )
        mock_get_client.return_value = mock_client

        result = http_download(
            url="https://example.com/file.zip", output_file="/tmp/file.zip"
        )

        assert result["success"] is True
        assert "Downloaded successfully" in result["body"]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_session_request_tool_success(self, mock_get_client):
        """Test http_session_request tool with successful request."""
        mock_client = MagicMock()
        mock_client.session_request.return_value = HttpResponse(
            success=True,
            status_code=200,
            headers="HTTP/1.1 200 OK\nSet-Cookie: session=xyz",
            body='{"authenticated": true}',
            error=None,
            command="http --session my-session https://example.com",
        )
        mock_get_client.return_value = mock_client

        result = http_session_request(
            session_name="my-session",
            url="https://example.com/login",
            json_data={"username": "user"},
        )

        assert result["success"] is True
        assert result["status_code"] == 200
        assert "authenticated" in result["body"]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_session_request_tool_read_only(self, mock_get_client):
        """Test http_session_request tool with read-only session."""
        mock_client = MagicMock()
        mock_client.session_request.return_value = HttpResponse(
            success=True,
            status_code=200,
            body='{"data": "value"}',
            error=None,
            command="http --session-read-only my-session https://example.com",
        )
        mock_get_client.return_value = mock_client

        result = http_session_request(
            session_name="my-session", url="https://example.com/data", read_only=True
        )

        assert result["success"] is True
        # Verify read_only parameter was passed
        call_kwargs = mock_client.session_request.call_args[0][0]
        assert call_kwargs.read_only is True


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @patch("subprocess.run")
    def test_client_with_custom_binary_paths(self, mock_run):
        """Test client with custom HTTPie binary paths."""
        mock_run.return_value = MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr="")

        client = HTTPieClient(
            httpie_binary="/custom/path/http",
            https_binary="/custom/path/https",
            verify_installation=True,
        )

        assert client.httpie_binary == "/custom/path/http"
        assert client.https_binary == "/custom/path/https"

    @patch("subprocess.run")
    def test_request_with_offline_mode(self, mock_run):
        """Test request in offline mode (dry-run)."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HTTPie 3.2.2", stderr=""),
            MagicMock(
                returncode=0,
                stdout="POST /api HTTP/1.1\nHost: example.com\n\n{\"data\":\"value\"}",
                stderr="",
            ),
        ]

        client = HTTPieClient(verify_installation=True)
        request = HttpRequestInput(
            url="https://example.com/api",
            method=HttpMethod.POST,
            json_data={"data": "value"},
            offline=True,
        )
        response = client.make_request(request)

        assert response.success is True
        # Verify offline flag was added
        call_args = mock_run.call_args_list[1][0][0]
        assert "--offline" in call_args

    def test_multiple_auth_types(self):
        """Test different authentication types."""
        # Basic auth
        request_basic = HttpRequestInput(
            url="https://example.com", auth="user:pass", auth_type=AuthType.BASIC
        )
        assert request_basic.auth_type == AuthType.BASIC

        # Bearer auth
        request_bearer = HttpRequestInput(
            url="https://example.com", auth="token123", auth_type=AuthType.BEARER
        )
        assert request_bearer.auth_type == AuthType.BEARER

        # Digest auth
        request_digest = HttpRequestInput(
            url="https://example.com", auth="user:pass", auth_type=AuthType.DIGEST
        )
        assert request_digest.auth_type == AuthType.DIGEST


class TestNewMCPTools:
    """Test new MCP tool endpoints (multipart upload, status check, streaming, etc)."""

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_multipart_upload_tool_success(self, mock_get_client):
        """Test http_multipart_upload tool with successful file upload."""
        mock_client = MagicMock()
        mock_client.multipart_upload.return_value = HttpResponse(
            success=True,
            status_code=201,
            headers="HTTP/1.1 201 Created",
            body='{"uploaded": true, "file_id": "abc123"}',
            error=None,
            command="http --form POST https://example.com/upload",
        )
        mock_get_client.return_value = mock_client

        result = http_multipart_upload(
            url="https://example.com/upload",
            files={"document": "/tmp/test.pdf", "image": "/tmp/photo.jpg"},
            form_data={"title": "Test Upload"},
            method="POST",
        )

        assert result["success"] is True
        assert result["status_code"] == 201
        assert "uploaded" in result["body"]
        mock_client.multipart_upload.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_multipart_upload_tool_with_boundary(self, mock_get_client):
        """Test http_multipart_upload tool with custom boundary."""
        mock_client = MagicMock()
        mock_client.multipart_upload.return_value = HttpResponse(
            success=True,
            status_code=200,
            body='{"status": "uploaded"}',
            error=None,
            command="http --form --boundary custom https://example.com/upload",
        )
        mock_get_client.return_value = mock_client

        result = http_multipart_upload(
            url="https://example.com/upload",
            files={"file": "/tmp/document.pdf"},
            boundary="custom-boundary-123",
        )

        assert result["success"] is True
        mock_client.multipart_upload.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_check_status_tool_success(self, mock_get_client):
        """Test http_check_status tool with successful status validation."""
        mock_client = MagicMock()
        mock_client.check_status.return_value = HttpCheckStatusResponse(
            status_check="passed",
            expected=[200, 201],
            actual=200,
            response_time_ms=150,
        )
        mock_get_client.return_value = mock_client

        result = http_check_status(
            url="https://example.com/health", expected_status=[200, 201]
        )

        assert result["status_check"] == "passed"
        assert result["actual"] == 200
        assert result["response_time_ms"] == 150
        mock_client.check_status.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_check_status_tool_failure(self, mock_get_client):
        """Test http_check_status tool with failed status validation."""
        mock_client = MagicMock()
        mock_client.check_status.return_value = HttpCheckStatusResponse(
            status_check="failed",
            expected=[200],
            actual=503,
            response_time_ms=2000,
        )
        mock_get_client.return_value = mock_client

        result = http_check_status(url="https://example.com/api", expected_status=[200])

        assert result["status_check"] == "failed"
        assert result["actual"] == 503
        mock_client.check_status.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_stream_tool_success(self, mock_get_client):
        """Test http_stream tool with successful streaming response."""
        mock_client = MagicMock()
        mock_client.stream_response.return_value = HttpResponse(
            success=True,
            status_code=200,
            headers="HTTP/1.1 200 OK\nContent-Type: text/event-stream",
            body="data: event1\ndata: event2\ndata: event3\n",
            error=None,
            command="http --stream GET https://example.com/events",
        )
        mock_get_client.return_value = mock_client

        result = http_stream(url="https://example.com/events", max_lines=100)

        assert result["success"] is True
        assert result["status_code"] == 200
        assert "event1" in result["body"]
        mock_client.stream_response.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_stream_tool_with_line_limit(self, mock_get_client):
        """Test http_stream tool with max_lines limiting."""
        mock_client = MagicMock()
        mock_client.stream_response.return_value = HttpResponse(
            success=True,
            status_code=200,
            body="line1\nline2\nline3\n",
            error=None,
            command="http --stream GET https://example.com/logs",
        )
        mock_get_client.return_value = mock_client

        result = http_stream(url="https://example.com/logs", max_lines=3)

        assert result["success"] is True
        # Verify max_lines parameter was passed
        call_kwargs = mock_client.stream_response.call_args[0][0]
        assert call_kwargs.max_lines == 3

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_validate_json_schema_tool_success(self, mock_get_client):
        """Test http_validate_json_schema tool with valid JSON."""
        mock_client = MagicMock()
        mock_client.validate_json_schema.return_value = HttpValidateJsonSchemaResponse(
            validation_passed=True,
            validation_errors=[],
        )
        mock_get_client.return_value = mock_client

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }

        result = http_validate_json_schema(
            url="https://api.example.com/user/123", json_schema=schema
        )

        assert result["validation_passed"] is True
        assert len(result["validation_errors"]) == 0
        mock_client.validate_json_schema.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_validate_json_schema_tool_failure(self, mock_get_client):
        """Test http_validate_json_schema tool with invalid JSON."""
        mock_client = MagicMock()
        mock_client.validate_json_schema.return_value = HttpValidateJsonSchemaResponse(
            validation_passed=False,
            validation_errors=["'name' is a required property", "'age' is not of type 'number'"],
        )
        mock_get_client.return_value = mock_client

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name", "age"],
        }

        result = http_validate_json_schema(
            url="https://api.example.com/user/456", json_schema=schema
        )

        assert result["validation_passed"] is False
        assert len(result["validation_errors"]) == 2
        assert "required property" in result["validation_errors"][0]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_retry_tool_success_first_attempt(self, mock_get_client):
        """Test http_retry tool succeeding on first attempt."""
        mock_client = MagicMock()
        mock_client.retry_request.return_value = HttpRetryResponse(
            attempts=1,
            retry_history=[{"attempt": 1, "status_code": 200, "success": True, "delay_ms": 0}],
        )
        mock_get_client.return_value = mock_client

        result = http_retry(
            url="https://api.example.com/data", max_retries=3, retry_delay_ms=1000
        )

        assert result["attempts"] == 1
        assert len(result["retry_history"]) == 1
        assert result["retry_history"][0]["success"] is True
        mock_client.retry_request.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_retry_tool_success_after_retries(self, mock_get_client):
        """Test http_retry tool succeeding after retries."""
        mock_client = MagicMock()
        mock_client.retry_request.return_value = HttpRetryResponse(
            attempts=3,
            retry_history=[
                {"attempt": 1, "status_code": 503, "success": False, "delay_ms": 0},
                {"attempt": 2, "status_code": 502, "success": False, "delay_ms": 1000},
                {"attempt": 3, "status_code": 200, "success": True, "delay_ms": 2000},
            ],
        )
        mock_get_client.return_value = mock_client

        result = http_retry(
            url="https://api.example.com/unstable",
            max_retries=5,
            retry_delay_ms=1000,
            retry_on_status=[502, 503, 504],
            exponential_backoff=True,
        )

        assert result["attempts"] == 3
        assert len(result["retry_history"]) == 3
        assert result["retry_history"][-1]["success"] is True
        # Verify exponential backoff was used
        assert result["retry_history"][1]["delay_ms"] == 1000
        assert result["retry_history"][2]["delay_ms"] == 2000

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_retry_tool_max_retries_exceeded(self, mock_get_client):
        """Test http_retry tool exceeding max retries."""
        mock_client = MagicMock()
        mock_client.retry_request.return_value = HttpRetryResponse(
            attempts=4,
            retry_history=[
                {"attempt": 1, "status_code": 500, "success": False, "delay_ms": 0},
                {"attempt": 2, "status_code": 500, "success": False, "delay_ms": 1000},
                {"attempt": 3, "status_code": 500, "success": False, "delay_ms": 2000},
                {"attempt": 4, "status_code": 500, "success": False, "delay_ms": 4000},
            ],
        )
        mock_get_client.return_value = mock_client

        result = http_retry(
            url="https://api.example.com/broken", max_retries=3, retry_delay_ms=1000
        )

        assert result["attempts"] == 4
        assert all(not h["success"] for h in result["retry_history"])

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_response_extract_tool_jsonpath(self, mock_get_client):
        """Test http_response_extract tool with JSONPath extractor."""
        mock_client = MagicMock()
        mock_client.extract_response.return_value = HttpExtractResponse(
            extracted_data={"user_name": ["John Doe"], "user_id": [123]},
            extraction_errors={},
        )
        mock_get_client.return_value = mock_client

        result = http_response_extract(
            url="https://api.example.com/user/123",
            extractor="jsonpath",
            expressions={"user_name": "$.data.name", "user_id": "$.data.id"},
        )

        assert "user_name" in result["extracted_data"]
        assert "user_id" in result["extracted_data"]
        assert len(result["extraction_errors"]) == 0
        mock_client.extract_response.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_response_extract_tool_regex(self, mock_get_client):
        """Test http_response_extract tool with regex extractor."""
        mock_client = MagicMock()
        mock_client.extract_response.return_value = HttpExtractResponse(
            extracted_data={"emails": ["user@example.com", "admin@example.com"]},
            extraction_errors={},
        )
        mock_get_client.return_value = mock_client

        result = http_response_extract(
            url="https://example.com/contact",
            extractor="regex",
            expressions={"emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"},
        )

        assert "emails" in result["extracted_data"]
        assert len(result["extracted_data"]["emails"]) == 2
        mock_client.extract_response.assert_called_once()

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_response_extract_tool_with_errors(self, mock_get_client):
        """Test http_response_extract tool with extraction errors."""
        mock_client = MagicMock()
        mock_client.extract_response.return_value = HttpExtractResponse(
            extracted_data={"valid_field": ["value"]},
            extraction_errors={
                "invalid_field": "JSONPath expression failed: Invalid path syntax"
            },
        )
        mock_get_client.return_value = mock_client

        result = http_response_extract(
            url="https://api.example.com/data",
            extractor="jsonpath",
            expressions={"valid_field": "$.data.valid", "invalid_field": "$.[invalid"},
        )

        assert "valid_field" in result["extracted_data"]
        assert "invalid_field" in result["extraction_errors"]
        assert "failed" in result["extraction_errors"]["invalid_field"]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_multipart_upload_tool_error_handling(self, mock_get_client):
        """Test http_multipart_upload tool error handling."""
        mock_get_client.side_effect = HTTPieClientError("File not found: /tmp/missing.pdf")

        result = http_multipart_upload(
            url="https://example.com/upload", files={"file": "/tmp/missing.pdf"}
        )

        assert result["success"] is False
        assert "File not found" in result["error"]

    @patch("httpie_mcp.server.get_httpie_client")
    def test_http_validate_json_schema_tool_missing_dependency(self, mock_get_client):
        """Test http_validate_json_schema tool when jsonschema package is missing."""
        mock_client = MagicMock()
        mock_client.validate_json_schema.return_value = HttpValidateJsonSchemaResponse(
            validation_passed=False,
            validation_errors=["jsonschema package not installed. Install with: pip install jsonschema"],
        )
        mock_get_client.return_value = mock_client

        result = http_validate_json_schema(
            url="https://api.example.com/data",
            json_schema={"type": "object"},
        )

        assert result["validation_passed"] is False
        assert any("jsonschema package not installed" in err for err in result["validation_errors"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
