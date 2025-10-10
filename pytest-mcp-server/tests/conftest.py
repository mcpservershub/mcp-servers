"""
Test configuration and fixtures.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from pytest_mcp_server.models import TestEnvironment, TestCase, TestOutcome
from pytest_mcp_server.storage import TestStorage
from pytest_mcp_server.server import create_server


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def storage(temp_db):
    """Create a test storage instance."""
    return TestStorage(db_path=temp_db)


@pytest.fixture
def test_environment():
    """Create a test environment."""
    return TestEnvironment(
        os="Linux",
        python_version="3.12.0",
        pytest_version="8.0.0",
        platform="Linux-5.4.0-x86_64",
        architecture="x86_64"
    )


@pytest.fixture
def sample_test_case():
    """Create a sample test case."""
    return TestCase(
        nodeid="tests/test_example.py::test_function",
        outcome=TestOutcome.PASSED,
        duration=0.123,
        markers=["unit", "fast"],
        keywords=["test", "function"],
        file_path="tests/test_example.py",
        line_number=10
    )


@pytest.fixture
def failed_test_case():
    """Create a failed test case."""
    return TestCase(
        nodeid="tests/test_example.py::test_failure",
        outcome=TestOutcome.FAILED,
        duration=0.456,
        error="AssertionError: assert 1 == 2",
        traceback="Traceback (most recent call last):\n  File 'test.py', line 5, in test_failure\n    assert 1 == 2\nAssertionError: assert 1 == 2",
        markers=["unit"],
        keywords=["test", "failure"],
        file_path="tests/test_example.py",
        line_number=15
    )


@pytest.fixture
def mcp_server():
    """Create an MCP server instance for testing."""
    return create_server()


@pytest.fixture
def sample_environment_data():
    """Sample environment data for testing."""
    return {
        "os": "Linux",
        "python_version": "3.12.0",
        "pytest_version": "8.0.0",
        "platform": "Linux-5.4.0-x86_64",
        "architecture": "x86_64"
    }


@pytest.fixture
def sample_test_outcome_data():
    """Sample test outcome data for testing."""
    return {
        "nodeid": "tests/test_sample.py::test_example",
        "outcome": "passed",
        "duration": 0.123,
        "markers": ["unit", "fast"],
        "keywords": ["test", "example"],
        "file_path": "tests/test_sample.py",
        "line_number": 10
    }


@pytest.fixture
def sample_failed_test_data():
    """Sample failed test data for testing."""
    return {
        "nodeid": "tests/test_sample.py::test_failure",
        "outcome": "failed",
        "duration": 0.456,
        "error": "AssertionError: assert 1 == 2",
        "traceback": "Traceback (most recent call last):\n  File 'test.py', line 5\n    assert 1 == 2\nAssertionError",
        "markers": ["unit"],
        "keywords": ["test", "failure"],
        "file_path": "tests/test_sample.py",
        "line_number": 20
    }


@pytest.fixture
def sample_session_summary():
    """Sample session summary data for testing."""
    return {
        "total_tests": 10,
        "passed": 7,
        "failed": 2,
        "skipped": 1,
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0,
        "exitstatus": 1,
        "duration": 5.5
    }