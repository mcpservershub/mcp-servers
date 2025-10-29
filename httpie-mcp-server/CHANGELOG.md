# Changelog

All notable changes to the HTTPie MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Add support for HTTPie plugins
- Implement request/response caching
- Add metrics and monitoring endpoints
- Support for batch requests
- WebSocket support via HTTPie extensions

## [0.1.0] - 2024-10-23

### Added
- Initial release of HTTPie MCP Server
- Core MCP tools:
  - `http_request`: Make HTTP requests with comprehensive options
  - `http_download`: Download files with resume capability
  - `http_session_request`: Persistent session management
- Comprehensive input validation using Pydantic schemas
- Security features:
  - Command injection prevention
  - Header value sanitization
  - Secure subprocess execution
- HTTPie client wrapper with full feature support:
  - All HTTP methods (GET, POST, PUT, DELETE, etc.)
  - JSON and form data support
  - Custom headers and query parameters
  - Authentication (Basic, Bearer, Digest)
  - SSL/TLS configuration
  - Proxy support
  - Timeout configuration
  - Redirect handling
  - Offline mode (dry-run)
- Docker support:
  - Multi-stage Dockerfile for optimized image size
  - Non-root user execution
  - Health checks
  - Volume support for persistent sessions
- Comprehensive test suite:
  - Unit tests for all components
  - Integration tests for MCP tools
  - Mocked subprocess tests
  - Edge case and error scenario coverage
- Documentation:
  - Detailed README with installation and usage instructions
  - API documentation with examples
  - Contributing guidelines
  - Sample MCP configuration
  - Troubleshooting guide
- Development tooling:
  - Ruff for linting and formatting
  - MyPy for type checking
  - Pytest for testing
  - Pre-commit hooks support
- Python 3.12+ support with full type hints
- FastMCP integration for MCP protocol
- Structured logging for debugging
- Docker Compose configuration for easy deployment

### Security
- Input validation on all user inputs
- Sanitization of header values to prevent injection
- Subprocess execution without shell=True
- Configurable timeouts to prevent hanging
- Non-root Docker container execution
- Minimal dependency footprint

### Developer Experience
- Clear error messages with actionable information
- Verbose logging option for debugging
- Offline mode for request inspection
- MCP Inspector support for testing
- Type-safe interfaces with Pydantic
- Comprehensive docstrings and inline documentation

[Unreleased]: https://github.com/httpie/mcp-server/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/httpie/mcp-server/releases/tag/v0.1.0
