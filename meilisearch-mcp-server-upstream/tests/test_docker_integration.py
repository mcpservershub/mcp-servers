"""
Integration tests for Docker image build.

These tests verify that the Docker image can be built successfully.
"""
import subprocess
import pytest
import shutil


# Check if Docker is available
def docker_available():
    """Check if Docker is available on the system."""
    if not shutil.which("docker"):
        return False
    # Try to run docker version to ensure it's working
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Skip all tests in this module if Docker is not available
pytestmark = pytest.mark.skipif(
    not docker_available(),
    reason="Docker not available on this system"
)


def test_docker_build():
    """Test that the Docker image can be built successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", "meilisearch-mcp-test", "."],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Docker build failed: {result.stderr}"


def test_docker_image_runs():
    """Test that the Docker image can run and show help."""
    # First build the image
    build_result = subprocess.run(
        ["docker", "build", "-t", "meilisearch-mcp-test", "."],
        capture_output=True,
        text=True
    )
    if build_result.returncode != 0:
        pytest.skip(f"Docker build failed: {build_result.stderr}")
    
    # Try to run the container and check it starts
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-e", "MEILI_HTTP_ADDR=http://localhost:7700",
            "-e", "MEILI_MASTER_KEY=test",
            "meilisearch-mcp-test",
            "python", "-c", "import src.meilisearch_mcp; print('MCP module loaded successfully')"
        ],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert result.returncode == 0, f"Docker run failed: {result.stderr}"
    assert "MCP module loaded successfully" in result.stdout


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])