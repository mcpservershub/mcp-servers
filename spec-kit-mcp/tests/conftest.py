"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock

from spec_kit_mcp.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_settings(temp_dir):
    """Create mock settings for testing."""
    return Settings(
        repo_path=temp_dir,
        templates_path=temp_dir / "templates",
        scripts_path=temp_dir / "scripts",
        restrict_to_repo=False,
        github_token="test_token"
    )


@pytest.fixture
def mock_github_client():
    """Mock GitHub client."""
    client = AsyncMock()
    client.download_template.return_value = Path("/tmp/template")
    client.check_rate_limit.return_value = {
        "limit": 5000,
        "remaining": 4999,
        "reset": 1234567890
    }
    return client


@pytest.fixture
def mock_script_runner():
    """Mock script runner."""
    runner = AsyncMock()
    runner.run_script.return_value = {
        "BRANCH_NAME": "001-test-feature",
        "SPEC_FILE": "/tmp/specs/001-test-feature/spec.md"
    }
    runner.check_script_exists.return_value = True
    return runner


@pytest.fixture
def mock_git_ops():
    """Mock git operations."""
    git_ops = AsyncMock()
    git_ops.get_current_branch.return_value = "main"
    git_ops.get_next_feature_number.return_value = 1
    git_ops.is_git_repo.return_value = True
    git_ops.list_branches.return_value = ["main", "001-feature-one"]
    return git_ops