"""HTTPie client wrapper module - handles subprocess invocation of HTTPie CLI tools."""

import json
import logging
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    AuthType,
    HttpDownloadInput,
    HttpMethod,
    HttpRequestInput,
    HttpResponse,
    OutputFormat,
    SessionRequestInput,
)

# Configure logging
logger = logging.getLogger(__name__)


class HTTPieClientError(Exception):
    """Base exception for HTTPie client errors."""

    pass


class HTTPieNotFoundError(HTTPieClientError):
    """Raised when HTTPie executable is not found."""

    pass


class HTTPieExecutionError(HTTPieClientError):
    """Raised when HTTPie command execution fails."""

    pass


class HTTPieClient:
    """
    HTTPie CLI wrapper that safely executes http/https commands as subprocesses.

    This client provides a Python interface to HTTPie while ensuring:
    - Input validation and sanitization
    - Secure subprocess execution
    - Comprehensive error handling
    - Detailed logging for debugging
    """

    def __init__(
        self,
        httpie_binary: str = "http",
        https_binary: str = "https",
        verify_installation: bool = True,
    ):
        """
        Initialize HTTPie client.

        Args:
            httpie_binary: Path to 'http' executable (default: 'http')
            https_binary: Path to 'https' executable (default: 'https')
            verify_installation: Whether to verify HTTPie is installed on init

        Raises:
            HTTPieNotFoundError: If HTTPie binaries not found and verify_installation=True
        """
        self.httpie_binary = httpie_binary
        self.https_binary = https_binary

        if verify_installation:
            self._verify_httpie_installed()

    def _verify_httpie_installed(self) -> None:
        """
        Verify HTTPie is installed and accessible.

        Raises:
            HTTPieNotFoundError: If HTTPie is not found in PATH
        """
        try:
            result = subprocess.run(
                [self.httpie_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                raise HTTPieNotFoundError(
                    f"HTTPie executable '{self.httpie_binary}' found but returned error: "
                    f"{result.stderr}"
                )
            logger.info(f"HTTPie version check successful: {result.stdout.strip()}")
        except FileNotFoundError as e:
            raise HTTPieNotFoundError(
                f"HTTPie executable '{self.httpie_binary}' not found. "
                f"Please install HTTPie: pip install httpie or use Docker container."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise HTTPieNotFoundError(
                f"HTTPie version check timed out. Command: {self.httpie_binary} --version"
            ) from e

    def _build_command(
        self,
        url: str,
        method: Optional[HttpMethod] = None,
        use_https: bool = False,
        **kwargs: Any,
    ) -> List[str]:
        """
        Build HTTPie command from parameters.

        Args:
            url: Target URL
            method: HTTP method
            use_https: Use 'https' binary instead of 'http'
            **kwargs: Additional HTTPie options

        Returns:
            List of command arguments ready for subprocess execution
        """
        cmd = [self.https_binary if use_https else self.httpie_binary]

        # Add method if specified
        if method:
            cmd.append(method.value)

        # Add URL
        cmd.append(url)

        return cmd

    def _add_common_options(
        self, cmd: List[str], request: HttpRequestInput
    ) -> None:
        """
        Add common HTTP request options to command.

        Args:
            cmd: Command list to append options to
            request: HTTP request input schema
        """
        # Authentication
        if request.auth:
            cmd.extend(["--auth", request.auth])
            if request.auth_type:
                cmd.extend(["--auth-type", request.auth_type.value])

        # Headers
        if request.headers:
            for key, value in request.headers.items():
                # Sanitize header values to prevent injection
                sanitized_value = self._sanitize_header_value(value)
                cmd.append(f"{key}:{sanitized_value}")

        # Query parameters
        if request.query_params:
            for key, value in request.query_params.items():
                cmd.append(f"{key}=={value}")

        # JSON data
        if request.json_data:
            cmd.append("--json")
            for key, value in request.json_data.items():
                if isinstance(value, (dict, list)):
                    # Non-string JSON data
                    cmd.append(f"{key}:={json.dumps(value)}")
                else:
                    cmd.append(f"{key}={value}")

        # Form data
        if request.form_data:
            cmd.append("--form")
            for key, value in request.form_data.items():
                cmd.append(f"{key}={value}")

        # Raw data
        if request.raw_data:
            cmd.extend(["--raw", request.raw_data])

        # Network options
        if request.timeout is not None:
            cmd.extend(["--timeout", str(request.timeout)])

        if request.follow_redirects:
            cmd.append("--follow")

        if request.max_redirects is not None:
            cmd.extend(["--max-redirects", str(request.max_redirects)])

        if not request.verify_ssl:
            cmd.extend(["--verify", "no"])

        if request.proxy:
            cmd.extend(["--proxy", request.proxy])

        # SSL options
        if request.cert:
            cmd.extend(["--cert", request.cert])
        if request.cert_key:
            cmd.extend(["--cert-key", request.cert_key])

        # Session
        if request.session:
            cmd.extend(["--session", request.session])

        # Output control
        print_what = ""
        if request.output_headers:
            print_what += "h"
        if request.output_body:
            print_what += "b"
        if request.output_metadata:
            print_what += "m"
        if print_what:
            cmd.extend(["--print", print_what])

        if request.verbose:
            cmd.append("--verbose")

        if request.pretty_print:
            cmd.extend(["--pretty", request.pretty_print.value])

        # File output
        if request.download:
            cmd.append("--download")
        if request.output_file:
            cmd.extend(["--output", request.output_file])

        # Offline mode
        if request.offline:
            cmd.append("--offline")

        # Always ignore stdin to prevent hanging
        cmd.append("--ignore-stdin")

    def _sanitize_header_value(self, value: str) -> str:
        """
        Sanitize header value to prevent command injection.

        Args:
            value: Header value to sanitize

        Returns:
            Sanitized header value
        """
        # Remove newlines and carriage returns
        sanitized = value.replace("\n", "").replace("\r", "")
        # Escape quotes
        sanitized = sanitized.replace('"', '\\"')
        return sanitized

    def _parse_response(
        self, stdout: str, stderr: str, returncode: int, command: str
    ) -> HttpResponse:
        """
        Parse HTTPie output into structured response.

        Args:
            stdout: Standard output from HTTPie
            stderr: Standard error from HTTPie
            returncode: Process return code
            command: The command that was executed

        Returns:
            Structured HTTP response
        """
        success = returncode == 0
        error_msg = None

        if not success:
            error_msg = stderr.strip() if stderr else f"Command failed with exit code {returncode}"
            logger.error(f"HTTPie command failed: {error_msg}")

        # Try to extract status code from output
        status_code = None
        headers = None
        body = None
        metadata = None

        if stdout:
            # HTTPie typically formats output as: HTTP/1.1 200 OK\nHeaders...\n\nBody
            lines = stdout.split("\n")

            # Look for HTTP status line
            for i, line in enumerate(lines):
                if line.startswith("HTTP/"):
                    try:
                        status_code = int(line.split()[1])
                    except (IndexError, ValueError):
                        pass

                    # Everything from status line until empty line is headers
                    header_end = i + 1
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == "":
                            header_end = j
                            break
                    headers = "\n".join(lines[i : header_end + 1])

                    # Everything after empty line is body
                    if header_end < len(lines) - 1:
                        body = "\n".join(lines[header_end + 1 :])
                    break
            else:
                # No HTTP status line found, treat entire output as body
                body = stdout

        return HttpResponse(
            success=success,
            status_code=status_code,
            headers=headers,
            body=body,
            metadata=metadata,
            error=error_msg,
            command=command,
        )

    def _execute_command(
        self, cmd: List[str], timeout: Optional[int] = None
    ) -> Tuple[str, str, int]:
        """
        Execute HTTPie command safely.

        Args:
            cmd: Command list to execute
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            HTTPieExecutionError: If command execution fails critically
        """
        # Log the command (sanitized for security)
        safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
        logger.info(f"Executing HTTPie command: {safe_cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout if timeout and timeout > 0 else None,
                check=False,  # We handle return codes manually
            )
            logger.debug(f"Command stdout: {result.stdout[:500]}")  # Log first 500 chars
            logger.debug(f"Command stderr: {result.stderr}")
            logger.debug(f"Command return code: {result.returncode}")

            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired as e:
            error_msg = f"HTTPie command timed out after {timeout} seconds"
            logger.error(error_msg)
            raise HTTPieExecutionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error executing HTTPie command: {str(e)}"
            logger.error(error_msg)
            raise HTTPieExecutionError(error_msg) from e

    def make_request(self, request: HttpRequestInput) -> HttpResponse:
        """
        Make an HTTP request using HTTPie.

        Args:
            request: HTTP request parameters

        Returns:
            Structured HTTP response

        Raises:
            HTTPieClientError: If request execution fails
        """
        try:
            # Determine whether to use https binary
            use_https = request.url.startswith("https://")

            # Build base command
            cmd = self._build_command(
                url=request.url, method=request.method, use_https=use_https
            )

            # Add all options
            self._add_common_options(cmd, request)

            # Execute command
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=request.timeout if request.timeout else None
            )

            # Parse and return response
            safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
            return self._parse_response(stdout, stderr, returncode, safe_cmd)

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in make_request: {str(e)}")
            raise HTTPieClientError(f"Request failed: {str(e)}") from e

    def download_file(self, download: HttpDownloadInput) -> HttpResponse:
        """
        Download a file using HTTPie.

        Args:
            download: Download parameters

        Returns:
            Structured HTTP response

        Raises:
            HTTPieClientError: If download fails
        """
        try:
            use_https = download.url.startswith("https://")
            cmd = self._build_command(url=download.url, use_https=use_https)

            # Download options
            cmd.append("--download")

            if download.output_file:
                cmd.extend(["--output", download.output_file])

            if download.resume:
                cmd.append("--continue")

            # Authentication
            if download.auth:
                cmd.extend(["--auth", download.auth])
                if download.auth_type:
                    cmd.extend(["--auth-type", download.auth_type.value])

            # Headers
            if download.headers:
                for key, value in download.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # SSL verification
            if not download.verify_ssl:
                cmd.extend(["--verify", "no"])

            # Timeout
            timeout = download.timeout if download.timeout else None
            if timeout is not None:
                cmd.extend(["--timeout", str(timeout)])

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            stdout, stderr, returncode = self._execute_command(cmd, timeout=timeout)

            # Parse and return
            safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
            return self._parse_response(stdout, stderr, returncode, safe_cmd)

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in download_file: {str(e)}")
            raise HTTPieClientError(f"Download failed: {str(e)}") from e

    def session_request(self, session_req: SessionRequestInput) -> HttpResponse:
        """
        Make an HTTP request using HTTPie sessions for state persistence.

        Args:
            session_req: Session request parameters

        Returns:
            Structured HTTP response

        Raises:
            HTTPieClientError: If request fails
        """
        try:
            use_https = session_req.url.startswith("https://")
            cmd = self._build_command(
                url=session_req.url, method=session_req.method, use_https=use_https
            )

            # Session option
            session_flag = "--session-read-only" if session_req.read_only else "--session"
            cmd.extend([session_flag, session_req.session_name])

            # Authentication
            if session_req.auth:
                cmd.extend(["--auth", session_req.auth])
                if session_req.auth_type:
                    cmd.extend(["--auth-type", session_req.auth_type.value])

            # Headers
            if session_req.headers:
                for key, value in session_req.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # JSON data
            if session_req.json_data:
                cmd.append("--json")
                for key, value in session_req.json_data.items():
                    if isinstance(value, (dict, list)):
                        cmd.append(f"{key}:={json.dumps(value)}")
                    else:
                        cmd.append(f"{key}={value}")

            # Form data
            if session_req.form_data:
                cmd.append("--form")
                for key, value in session_req.form_data.items():
                    cmd.append(f"{key}={value}")

            # Network options
            if session_req.follow_redirects:
                cmd.append("--follow")

            if not session_req.verify_ssl:
                cmd.extend(["--verify", "no"])

            if session_req.verbose:
                cmd.append("--verbose")

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            stdout, stderr, returncode = self._execute_command(cmd)

            # Parse and return
            safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
            return self._parse_response(stdout, stderr, returncode, safe_cmd)

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in session_request: {str(e)}")
            raise HTTPieClientError(f"Session request failed: {str(e)}") from e

    def multipart_upload(
        self, upload_input: "HttpMultipartUploadInput"
    ) -> HttpResponse:
        """
        Upload files using multipart/form-data encoding.

        Args:
            upload_input: Multipart upload parameters

        Returns:
            Structured HTTP response

        Raises:
            HTTPieClientError: If upload fails
        """
        try:
            use_https = upload_input.url.startswith("https://")
            cmd = self._build_command(
                url=upload_input.url, method=upload_input.method, use_https=use_https
            )

            # Use --form or --multipart
            cmd.append("--form")

            # Add custom boundary if specified
            if upload_input.boundary:
                cmd.extend(["--boundary", upload_input.boundary])

            # Add files with @ syntax
            for field_name, file_path in upload_input.files.items():
                cmd.append(f"{field_name}@{file_path}")

            # Add form data
            if upload_input.form_data:
                for key, value in upload_input.form_data.items():
                    cmd.append(f"{key}={value}")

            # Authentication
            if upload_input.auth:
                cmd.extend(["--auth", upload_input.auth])
                if upload_input.auth_type:
                    cmd.extend(["--auth-type", upload_input.auth_type.value])

            # Headers
            if upload_input.headers:
                for key, value in upload_input.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # SSL verification
            if not upload_input.verify_ssl:
                cmd.extend(["--verify", "no"])

            # Timeout
            if upload_input.timeout is not None:
                cmd.extend(["--timeout", str(upload_input.timeout)])

            # Verbose
            if upload_input.verbose:
                cmd.append("--verbose")

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=upload_input.timeout
            )

            # Parse and return
            safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
            return self._parse_response(stdout, stderr, returncode, safe_cmd)

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in multipart_upload: {str(e)}")
            raise HTTPieClientError(f"Multipart upload failed: {str(e)}") from e

    def check_status(
        self, check_input: "HttpCheckStatusInput"
    ) -> "HttpCheckStatusResponse":
        """
        Make an HTTP request and validate status code.

        Args:
            check_input: Status check parameters

        Returns:
            Status check response with validation results

        Raises:
            HTTPieClientError: If request fails
        """
        import time

        try:
            use_https = check_input.url.startswith("https://")
            cmd = self._build_command(
                url=check_input.url, method=check_input.method, use_https=use_https
            )

            # Add --check-status flag
            cmd.append("--check-status")

            # Authentication
            if check_input.auth:
                cmd.extend(["--auth", check_input.auth])
                if check_input.auth_type:
                    cmd.extend(["--auth-type", check_input.auth_type.value])

            # Headers
            if check_input.headers:
                for key, value in check_input.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # JSON data
            if check_input.json_data:
                cmd.append("--json")
                for key, value in check_input.json_data.items():
                    if isinstance(value, (dict, list)):
                        cmd.append(f"{key}:={json.dumps(value)}")
                    else:
                        cmd.append(f"{key}={value}")

            # Form data
            if check_input.form_data:
                cmd.append("--form")
                for key, value in check_input.form_data.items():
                    cmd.append(f"{key}={value}")

            # Network options
            if check_input.follow_redirects:
                cmd.append("--follow")

            if not check_input.verify_ssl:
                cmd.extend(["--verify", "no"])

            if check_input.timeout is not None:
                cmd.extend(["--timeout", str(check_input.timeout)])

            # Print only headers to extract status
            cmd.extend(["--print", "h"])

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute and measure time
            start_time = time.time()
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=check_input.timeout
            )
            response_time_ms = int((time.time() - start_time) * 1000)

            # Parse response to get status code
            response = self._parse_response(stdout, stderr, returncode, " ".join(shlex.quote(arg) for arg in cmd))

            # Check if status matches expected
            actual_status = response.status_code
            status_check = (
                "passed"
                if actual_status and actual_status in check_input.expected_status
                else "failed"
            )

            # Import the response model here to avoid circular imports
            from .schemas import HttpCheckStatusResponse

            return HttpCheckStatusResponse(
                success=response.success and status_check == "passed",
                status_code=actual_status,
                status_check=status_check,
                expected=check_input.expected_status,
                actual=actual_status,
                response_time_ms=response_time_ms,
                error=response.error,
                command=" ".join(shlex.quote(arg) for arg in cmd),
            )

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in check_status: {str(e)}")
            raise HTTPieClientError(f"Status check failed: {str(e)}") from e

    def stream_response(self, stream_input: "HttpStreamInput") -> HttpResponse:
        """
        Stream HTTP response line by line.

        Args:
            stream_input: Stream parameters

        Returns:
            Structured HTTP response with streamed content

        Raises:
            HTTPieClientError: If streaming fails
        """
        try:
            use_https = stream_input.url.startswith("https://")
            cmd = self._build_command(
                url=stream_input.url, method=stream_input.method, use_https=use_https
            )

            # Add --stream flag
            cmd.append("--stream")

            # Authentication
            if stream_input.auth:
                cmd.extend(["--auth", stream_input.auth])
                if stream_input.auth_type:
                    cmd.extend(["--auth-type", stream_input.auth_type.value])

            # Headers
            if stream_input.headers:
                for key, value in stream_input.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # JSON data
            if stream_input.json_data:
                cmd.append("--json")
                for key, value in stream_input.json_data.items():
                    if isinstance(value, (dict, list)):
                        cmd.append(f"{key}:={json.dumps(value)}")
                    else:
                        cmd.append(f"{key}={value}")

            # SSL verification
            if not stream_input.verify_ssl:
                cmd.extend(["--verify", "no"])

            # Timeout
            if stream_input.timeout is not None:
                cmd.extend(["--timeout", str(stream_input.timeout)])

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            logger.info(f"Streaming from: {stream_input.url}")
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=stream_input.timeout
            )

            # Limit output if max_lines specified
            if stream_input.max_lines and stdout:
                lines = stdout.split("\n")
                stdout = "\n".join(lines[: stream_input.max_lines])

            # Parse and return
            safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
            return self._parse_response(stdout, stderr, returncode, safe_cmd)

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in stream_response: {str(e)}")
            raise HTTPieClientError(f"Streaming failed: {str(e)}") from e

    def validate_json_schema(
        self, validate_input: "HttpValidateJsonSchemaInput"
    ) -> "HttpValidateJsonSchemaResponse":
        """
        Make an HTTP request and validate response against JSON schema.

        Args:
            validate_input: Validation parameters including JSON schema

        Returns:
            Validation response with schema validation results

        Raises:
            HTTPieClientError: If request fails
        """
        try:
            # First, make the request
            use_https = validate_input.url.startswith("https://")
            cmd = self._build_command(
                url=validate_input.url, method=validate_input.method, use_https=use_https
            )

            # Authentication
            if validate_input.auth:
                cmd.extend(["--auth", validate_input.auth])
                if validate_input.auth_type:
                    cmd.extend(["--auth-type", validate_input.auth_type.value])

            # Headers
            if validate_input.headers:
                for key, value in validate_input.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # JSON data
            if validate_input.json_data:
                cmd.append("--json")
                for key, value in validate_input.json_data.items():
                    if isinstance(value, (dict, list)):
                        cmd.append(f"{key}:={json.dumps(value)}")
                    else:
                        cmd.append(f"{key}={value}")

            # SSL verification
            if not validate_input.verify_ssl:
                cmd.extend(["--verify", "no"])

            # Timeout
            if validate_input.timeout is not None:
                cmd.extend(["--timeout", str(validate_input.timeout)])

            # Print only body for validation
            cmd.extend(["--print", "b"])

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=validate_input.timeout
            )

            # Parse response
            response = self._parse_response(stdout, stderr, returncode, " ".join(shlex.quote(arg) for arg in cmd))

            # Validate JSON schema
            validation_passed = False
            validation_errors = []

            if response.success and response.body:
                try:
                    # Try to import jsonschema
                    try:
                        from jsonschema import validate, ValidationError
                    except ImportError:
                        logger.warning("jsonschema not installed, skipping validation")
                        validation_errors.append(
                            "jsonschema package not installed. Install with: pip install jsonschema"
                        )
                    else:
                        # Parse JSON response
                        response_json = json.loads(response.body)

                        # Validate against schema
                        try:
                            validate(instance=response_json, schema=validate_input.json_schema)
                            validation_passed = True
                        except ValidationError as ve:
                            validation_errors.append(str(ve.message))
                            logger.error(f"Schema validation failed: {ve.message}")

                except json.JSONDecodeError as je:
                    validation_errors.append(f"Response is not valid JSON: {str(je)}")
                except Exception as ve:
                    validation_errors.append(f"Validation error: {str(ve)}")

            # Import response model
            from .schemas import HttpValidateJsonSchemaResponse

            return HttpValidateJsonSchemaResponse(
                success=response.success,
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                status_code=response.status_code,
                body=response.body,
                error=response.error,
                command=" ".join(shlex.quote(arg) for arg in cmd),
            )

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate_json_schema: {str(e)}")
            raise HTTPieClientError(f"JSON schema validation failed: {str(e)}") from e

    def retry_request(self, retry_input: "HttpRetryInput") -> "HttpRetryResponse":
        """
        Make an HTTP request with automatic retry logic.

        Args:
            retry_input: Retry parameters

        Returns:
            Retry response with attempt history

        Raises:
            HTTPieClientError: If all retries fail
        """
        import time

        retry_history = []
        last_error = None

        for attempt in range(retry_input.max_retries + 1):
            try:
                # Build command
                use_https = retry_input.url.startswith("https://")
                cmd = self._build_command(
                    url=retry_input.url, method=retry_input.method, use_https=use_https
                )

                # Authentication
                if retry_input.auth:
                    cmd.extend(["--auth", retry_input.auth])
                    if retry_input.auth_type:
                        cmd.extend(["--auth-type", retry_input.auth_type.value])

                # Headers
                if retry_input.headers:
                    for key, value in retry_input.headers.items():
                        sanitized_value = self._sanitize_header_value(value)
                        cmd.append(f"{key}:{sanitized_value}")

                # JSON data
                if retry_input.json_data:
                    cmd.append("--json")
                    for key, value in retry_input.json_data.items():
                        if isinstance(value, (dict, list)):
                            cmd.append(f"{key}:={json.dumps(value)}")
                        else:
                            cmd.append(f"{key}={value}")

                # Form data
                if retry_input.form_data:
                    cmd.append("--form")
                    for key, value in retry_input.form_data.items():
                        cmd.append(f"{key}={value}")

                # SSL verification
                if not retry_input.verify_ssl:
                    cmd.extend(["--verify", "no"])

                # Timeout
                if retry_input.timeout is not None:
                    cmd.extend(["--timeout", str(retry_input.timeout)])

                # Always ignore stdin
                cmd.append("--ignore-stdin")

                # Execute
                logger.info(f"Attempt {attempt + 1}/{retry_input.max_retries + 1}")
                stdout, stderr, returncode = self._execute_command(
                    cmd, timeout=retry_input.timeout
                )

                # Parse response
                response = self._parse_response(stdout, stderr, returncode, " ".join(shlex.quote(arg) for arg in cmd))

                # Check if we should retry
                should_retry = (
                    response.status_code in retry_input.retry_on_status
                    if response.status_code
                    else not response.success
                )

                if should_retry and attempt < retry_input.max_retries:
                    # Calculate delay
                    if retry_input.exponential_backoff:
                        delay_ms = retry_input.retry_delay_ms * (2**attempt)
                    else:
                        delay_ms = retry_input.retry_delay_ms

                    retry_history.append(
                        {
                            "attempt": attempt + 1,
                            "status": response.status_code,
                            "delay_ms": delay_ms,
                            "error": response.error,
                        }
                    )

                    logger.info(f"Retrying after {delay_ms}ms...")
                    time.sleep(delay_ms / 1000.0)
                    last_error = response.error
                    continue

                # Success or final attempt
                retry_history.append(
                    {
                        "attempt": attempt + 1,
                        "status": response.status_code,
                        "delay_ms": 0,
                        "error": response.error,
                    }
                )

                # Import response model
                from .schemas import HttpRetryResponse

                return HttpRetryResponse(
                    success=response.success,
                    status_code=response.status_code,
                    attempts=attempt + 1,
                    retry_history=retry_history,
                    body=response.body,
                    error=response.error if not response.success else None,
                    command=" ".join(shlex.quote(arg) for arg in cmd),
                )

            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed: {e}")

                if attempt < retry_input.max_retries:
                    # Calculate delay
                    if retry_input.exponential_backoff:
                        delay_ms = retry_input.retry_delay_ms * (2**attempt)
                    else:
                        delay_ms = retry_input.retry_delay_ms

                    retry_history.append(
                        {
                            "attempt": attempt + 1,
                            "status": None,
                            "delay_ms": delay_ms,
                            "error": str(e),
                        }
                    )

                    time.sleep(delay_ms / 1000.0)
                else:
                    retry_history.append(
                        {"attempt": attempt + 1, "status": None, "delay_ms": 0, "error": str(e)}
                    )

        # All retries exhausted
        from .schemas import HttpRetryResponse

        return HttpRetryResponse(
            success=False,
            status_code=None,
            attempts=retry_input.max_retries + 1,
            retry_history=retry_history,
            body=None,
            error=f"All {retry_input.max_retries + 1} attempts failed. Last error: {last_error}",
            command=" ".join(shlex.quote(arg) for arg in cmd) if 'cmd' in locals() else "N/A",
        )

    def extract_response(
        self, extract_input: "HttpResponseExtractInput"
    ) -> "HttpExtractResponse":
        """
        Make an HTTP request and extract specific data from response.

        Args:
            extract_input: Extract parameters including expressions

        Returns:
            Extract response with extracted data

        Raises:
            HTTPieClientError: If request fails
        """
        try:
            # First, make the request
            use_https = extract_input.url.startswith("https://")
            cmd = self._build_command(
                url=extract_input.url, method=extract_input.method, use_https=use_https
            )

            # Authentication
            if extract_input.auth:
                cmd.extend(["--auth", extract_input.auth])
                if extract_input.auth_type:
                    cmd.extend(["--auth-type", extract_input.auth_type.value])

            # Headers
            if extract_input.headers:
                for key, value in extract_input.headers.items():
                    sanitized_value = self._sanitize_header_value(value)
                    cmd.append(f"{key}:{sanitized_value}")

            # JSON data
            if extract_input.json_data:
                cmd.append("--json")
                for key, value in extract_input.json_data.items():
                    if isinstance(value, (dict, list)):
                        cmd.append(f"{key}:={json.dumps(value)}")
                    else:
                        cmd.append(f"{key}={value}")

            # SSL verification
            if not extract_input.verify_ssl:
                cmd.extend(["--verify", "no"])

            # Timeout
            if extract_input.timeout is not None:
                cmd.extend(["--timeout", str(extract_input.timeout)])

            # Print only body for extraction
            cmd.extend(["--print", "b"])

            # Always ignore stdin
            cmd.append("--ignore-stdin")

            # Execute
            stdout, stderr, returncode = self._execute_command(
                cmd, timeout=extract_input.timeout
            )

            # Parse response
            response = self._parse_response(stdout, stderr, returncode, " ".join(shlex.quote(arg) for arg in cmd))

            # Extract data
            extracted_data = {}
            extraction_errors = {}

            if response.success and response.body:
                if extract_input.extractor.value == "jsonpath":
                    # JSONPath extraction
                    try:
                        try:
                            from jsonpath_ng import parse
                        except ImportError:
                            extraction_errors["_import"] = (
                                "jsonpath-ng not installed. Install with: pip install jsonpath-ng"
                            )
                        else:
                            response_json = json.loads(response.body)
                            for field_name, expression in extract_input.expressions.items():
                                try:
                                    jsonpath_expr = parse(expression)
                                    matches = [match.value for match in jsonpath_expr.find(response_json)]
                                    extracted_data[field_name] = matches[0] if len(matches) == 1 else matches
                                except Exception as e:
                                    extraction_errors[field_name] = f"JSONPath error: {str(e)}"

                    except json.JSONDecodeError as je:
                        extraction_errors["_json"] = f"Response is not valid JSON: {str(je)}"

                elif extract_input.extractor.value == "regex":
                    # Regex extraction
                    import re

                    for field_name, pattern in extract_input.expressions.items():
                        try:
                            matches = re.findall(pattern, response.body)
                            extracted_data[field_name] = matches[0] if len(matches) == 1 else matches
                        except Exception as e:
                            extraction_errors[field_name] = f"Regex error: {str(e)}"

                else:  # xpath
                    extraction_errors["_xpath"] = "XPath extraction not yet implemented"

            # Import response model
            from .schemas import HttpExtractResponse

            return HttpExtractResponse(
                success=response.success,
                extracted_data=extracted_data,
                extraction_errors=extraction_errors,
                status_code=response.status_code,
                error=response.error,
                command=" ".join(shlex.quote(arg) for arg in cmd),
            )

        except HTTPieClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in extract_response: {str(e)}")
            raise HTTPieClientError(f"Response extraction failed: {str(e)}") from e
