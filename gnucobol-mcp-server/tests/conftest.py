"""
Pytest configuration and shared fixtures for GnuCOBOL MCP Server tests.
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "mcp: mark test as MCP integration test"
    )
    config.addinivalue_line(
        "markers", "gnucobol: mark test as GnuCOBOL compiler test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


@pytest.fixture(scope="session")
def cobc_version():
    """Get GnuCOBOL compiler version."""
    try:
        result = subprocess.run(
            ['cobc', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


@pytest.fixture(scope="session")
def sample_dir():
    """Return path to sample COBOL directory."""
    return Path(__file__).parent / "sample_cobol"


@pytest.fixture(scope="session")
def valid_samples_dir(sample_dir):
    """Return path to valid COBOL samples."""
    return sample_dir / "valid"


@pytest.fixture(scope="session")
def invalid_samples_dir(sample_dir):
    """Return path to invalid COBOL samples."""
    return sample_dir / "invalid"


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for test files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace
