# Contributing to HTTPie MCP Server

Thank you for considering contributing to the HTTPie MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in your interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior**
- **Actual behavior**
- **Environment details** (OS, Python version, HTTPie version)
- **Logs or error messages**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** and motivation
- **Proposed solution** or implementation approach
- **Alternatives considered**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, descriptive commits
3. **Add tests** for any new functionality
4. **Ensure all tests pass**: `pytest`
5. **Run linting**: `ruff check src/ tests/`
6. **Update documentation** if needed
7. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.12+
- HTTPie CLI
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/httpie-mcp-server.git
cd httpie-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install HTTPie
pip install httpie
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=httpie_mcp --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_server.py -v

# Run specific test
pytest tests/test_server.py::TestHTTPieClient::test_make_request_simple_get -v
```

### Code Quality

```bash
# Run linter
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector python -m httpie_mcp.server
```

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function parameters and return values
- Write **docstrings** for all public functions, classes, and modules
- Keep functions focused and under 50 lines when possible
- Use descriptive variable names

### Example

```python
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
    # Implementation
    pass
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests liberally

### Examples

```
feat: Add support for custom SSL certificates
fix: Handle timeout errors properly in http_request
docs: Update README with session examples
test: Add integration tests for http_download
refactor: Simplify command building logic
```

## Project Structure

```
httpie-mcp-server/
├── src/httpie_mcp/        # Main source code
│   ├── __init__.py
│   ├── server.py          # FastMCP server
│   ├── httpie_client.py   # HTTPie wrapper
│   └── schemas.py         # Pydantic schemas
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_server.py
├── Dockerfile            # Container definition
├── pyproject.toml        # Project metadata
└── README.md            # Documentation
```

## Adding New Features

When adding a new feature:

1. **Discuss first**: Open an issue to discuss the feature
2. **Write tests**: Add tests before implementing
3. **Implement**: Write clean, well-documented code
4. **Update docs**: Update README and docstrings
5. **Test thoroughly**: Run all tests and manual testing
6. **Submit PR**: Create a pull request with clear description

## Testing Guidelines

### Test Structure

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test tool endpoints with mocked subprocess calls
- **Edge cases**: Test error conditions, timeouts, invalid inputs

### Writing Tests

```python
def test_feature_name(self):
    """Test description of what this test validates."""
    # Arrange: Set up test data
    request = HttpRequestInput(url="https://example.com")

    # Act: Execute the code being tested
    response = client.make_request(request)

    # Assert: Verify the results
    assert response.success is True
    assert response.status_code == 200
```

### Mocking

Use `unittest.mock` for subprocess calls:

```python
@patch("subprocess.run")
def test_make_request(self, mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="HTTP/1.1 200 OK\n\n{}",
        stderr=""
    )
    # Test implementation
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed, explaining the purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised

    Examples:
        >>> function_name("test", 42)
        True
    """
    pass
```

### README Updates

When adding features, update:

- Available tools section
- Examples section
- Table of contents if needed
- Configuration examples

## Release Process

1. Update version in `pyproject.toml` and `src/httpie_mcp/__init__.py`
2. Update CHANGELOG.md with release notes
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Build and publish Docker image
6. Create GitHub release with notes

## Questions?

If you have questions about contributing:

- Open a GitHub issue with the "question" label
- Join project discussions
- Contact maintainers

Thank you for contributing to HTTPie MCP Server!
