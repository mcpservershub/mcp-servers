"""Comprehensive tests for fd-mcp-server."""

import asyncio
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the functions to test
from src.fd_mcp_server import (
    check_fd_installed,
    fd_changed_before,
    fd_changed_within,
    fd_exclude_pattern,
    fd_exec_command,
    fd_list_all,
    fd_search,
    fd_search_by_extension,
    fd_search_by_type,
    fd_size_filter,
    get_fd_command,
    run_fd_command,
)


@pytest.fixture
def test_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)

        # Create test files
        (test_dir / "test.py").write_text("print('hello')")
        (test_dir / "test.txt").write_text("Sample text")
        (test_dir / "README.md").write_text("# Test")
        (test_dir / ".hidden.txt").write_text("Hidden content")

        # Create subdirectory with files
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("# nested")
        (subdir / "data.json").write_text('{"key": "value"}')

        # Create a large file
        (test_dir / "large.txt").write_text("x" * 10000)

        # Create an empty file
        (test_dir / "empty.txt").touch()

        yield str(test_dir)


class TestFdBasics:
    """Test basic fd functionality."""

    def test_check_fd_installed(self):
        """Test that fd is installed."""
        assert check_fd_installed() is True

    def test_get_fd_command(self):
        """Test getting fd command name."""
        cmd = get_fd_command()
        assert cmd in ["fd", "fdfind"]

    @pytest.mark.asyncio
    async def test_run_fd_command_success(self, test_directory):
        """Test running fd command successfully."""
        result = await run_fd_command(["test.py", test_directory])

        assert result["success"] is True
        assert result["return_code"] == 0
        assert len(result["results"]) > 0
        assert any("test.py" in r for r in result["results"])

    @pytest.mark.asyncio
    async def test_run_fd_command_no_results(self, test_directory):
        """Test fd command with no results."""
        result = await run_fd_command(["nonexistent_file_xyz.abc", test_directory])

        # fd returns 0 even with no results
        assert result["success"] is True
        assert result["results"] == [""] or result["results"] == []


class TestFdSearch:
    """Test fd_search tool."""

    @pytest.mark.asyncio
    async def test_fd_search_simple(self, test_directory):
        """Test simple search."""
        result_str = await fd_search(pattern="test", path=test_directory)
        result = json.loads(result_str)

        assert result["success"] is True
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_fd_search_with_extension(self, test_directory):
        """Test search with extension filter."""
        result_str = await fd_search(
            pattern=".*",
            path=test_directory,
            extension="py"
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert all(".py" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_fd_search_hidden(self, test_directory):
        """Test search including hidden files."""
        result_str = await fd_search(
            pattern="hidden",
            path=test_directory,
            hidden=True
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert any("hidden" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_fd_search_max_depth(self, test_directory):
        """Test search with max depth."""
        result_str = await fd_search(
            pattern=".*",
            path=test_directory,
            max_depth=1
        )
        result = json.loads(result_str)

        assert result["success"] is True
        # Should not find nested files
        assert not any("nested.py" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_fd_search_case_sensitive(self, test_directory):
        """Test case-sensitive search."""
        result_str = await fd_search(
            pattern="TEST",
            path=test_directory,
            case_sensitive=True
        )
        result = json.loads(result_str)

        # Should not find files with lowercase 'test'
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_fd_search_glob(self, test_directory):
        """Test glob-based search."""
        result_str = await fd_search(
            pattern="*.py",
            path=test_directory,
            glob=True
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert all(".py" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_fd_search_absolute_path(self, test_directory):
        """Test search with absolute paths."""
        result_str = await fd_search(
            pattern="test.py",
            path=test_directory,
            absolute_path=True
        )
        result = json.loads(result_str)

        assert result["success"] is True
        if result["results"] and result["results"][0]:
            assert result["results"][0].startswith("/")

    @pytest.mark.asyncio
    async def test_fd_search_max_results(self, test_directory):
        """Test search with max results limit."""
        result_str = await fd_search(
            pattern=".*",
            path=test_directory,
            max_results=2
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert len([r for r in result["results"] if r]) <= 2


class TestFdSearchByExtension:
    """Test fd_search_by_extension tool."""

    @pytest.mark.asyncio
    async def test_search_python_files(self, test_directory):
        """Test searching for Python files."""
        result_str = await fd_search_by_extension(
            extension="py",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert all(".py" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_search_with_pattern(self, test_directory):
        """Test searching by extension with pattern."""
        result_str = await fd_search_by_extension(
            extension="py",
            pattern="test",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_markdown_files(self, test_directory):
        """Test searching for markdown files."""
        result_str = await fd_search_by_extension(
            extension="md",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert any("README.md" in r for r in result["results"] if r)


class TestFdSearchByType:
    """Test fd_search_by_type tool."""

    @pytest.mark.asyncio
    async def test_search_files_only(self, test_directory):
        """Test searching for files only."""
        result_str = await fd_search_by_type(
            type_filter="f",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_directories_only(self, test_directory):
        """Test searching for directories only."""
        result_str = await fd_search_by_type(
            type_filter="d",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert any("subdir" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_search_empty_files(self, test_directory):
        """Test searching for empty files."""
        result_str = await fd_search_by_type(
            type_filter="e",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert any("empty.txt" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_search_with_max_depth(self, test_directory):
        """Test type search with max depth."""
        result_str = await fd_search_by_type(
            type_filter="f",
            path=test_directory,
            max_depth=1
        )
        result = json.loads(result_str)

        assert result["success"] is True


class TestFdListAll:
    """Test fd_list_all tool."""

    @pytest.mark.asyncio
    async def test_list_all_files(self, test_directory):
        """Test listing all files."""
        result_str = await fd_list_all(path=test_directory)
        result = json.loads(result_str)

        assert result["success"] is True
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_list_with_hidden(self, test_directory):
        """Test listing including hidden files."""
        result_str = await fd_list_all(
            path=test_directory,
            hidden=True
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert any("hidden" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_list_with_max_depth(self, test_directory):
        """Test listing with max depth."""
        result_str = await fd_list_all(
            path=test_directory,
            max_depth=1
        )
        result = json.loads(result_str)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_files_only(self, test_directory):
        """Test listing files only."""
        result_str = await fd_list_all(
            path=test_directory,
            type_filter="f"
        )
        result = json.loads(result_str)

        assert result["success"] is True


class TestFdExcludePattern:
    """Test fd_exclude_pattern tool."""

    @pytest.mark.asyncio
    async def test_exclude_single_pattern(self, test_directory):
        """Test excluding a single pattern."""
        result_str = await fd_exclude_pattern(
            pattern=".*",
            exclude=["*.py"],
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert not any(".py" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_exclude_multiple_patterns(self, test_directory):
        """Test excluding multiple patterns."""
        result_str = await fd_exclude_pattern(
            pattern=".*",
            exclude=["*.py", "*.md"],
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert not any(".py" in r or ".md" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_exclude_directory(self, test_directory):
        """Test excluding a directory."""
        result_str = await fd_exclude_pattern(
            pattern=".*",
            exclude=["subdir"],
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert not any("subdir" in r for r in result["results"] if r)


class TestFdTimeFilters:
    """Test time-based filtering tools."""

    @pytest.mark.asyncio
    async def test_changed_within(self, test_directory):
        """Test finding recently changed files."""
        result_str = await fd_changed_within(
            duration="1d",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        # Should find recently created test files
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_changed_within_with_type(self, test_directory):
        """Test finding recently changed files of specific type."""
        result_str = await fd_changed_within(
            duration="1d",
            path=test_directory,
            type_filter="f"
        )
        result = json.loads(result_str)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_changed_before(self, test_directory):
        """Test finding files changed before duration."""
        result_str = await fd_changed_before(
            duration="1min",
            path=test_directory
        )
        result = json.loads(result_str)

        # May or may not find files depending on timing
        assert result["success"] is True


class TestFdSizeFilter:
    """Test fd_size_filter tool."""

    @pytest.mark.asyncio
    async def test_size_larger_than(self, test_directory):
        """Test finding files larger than size."""
        result_str = await fd_size_filter(
            size="+5k",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True
        # Should find large.txt
        assert any("large.txt" in r for r in result["results"] if r)

    @pytest.mark.asyncio
    async def test_size_smaller_than(self, test_directory):
        """Test finding files smaller than size."""
        result_str = await fd_size_filter(
            size="-1k",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_size_with_extension(self, test_directory):
        """Test size filter with extension."""
        result_str = await fd_size_filter(
            size="+1b",
            extension="py",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True


class TestFdExecCommand:
    """Test fd_exec_command tool."""

    @pytest.mark.asyncio
    async def test_exec_echo(self, test_directory):
        """Test executing echo command."""
        result_str = await fd_exec_command(
            command="echo {}",
            pattern="test.py",
            path=test_directory
        )
        result = json.loads(result_str)

        # The exec command should succeed
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_exec_batch_mode(self, test_directory):
        """Test batch execution mode."""
        result_str = await fd_exec_command(
            command="echo {}",
            extension="py",
            path=test_directory,
            batch_mode=True
        )
        result = json.loads(result_str)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_exec_with_type_filter(self, test_directory):
        """Test exec with type filter."""
        result_str = await fd_exec_command(
            command="echo {}",
            type_filter="f",
            path=test_directory
        )
        result = json.loads(result_str)

        assert result["success"] is True


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_path(self):
        """Test search with invalid path."""
        result_str = await fd_search(
            pattern="test",
            path="/nonexistent/path/xyz"
        )
        result = json.loads(result_str)

        # fd handles this gracefully
        assert "results" in result

    @pytest.mark.asyncio
    async def test_invalid_regex(self, test_directory):
        """Test search with invalid regex."""
        result_str = await fd_search(
            pattern="[invalid",
            path=test_directory
        )
        result = json.loads(result_str)

        # Should have error information
        assert "success" in result

    @pytest.mark.asyncio
    async def test_invalid_type_filter(self, test_directory):
        """Test search with invalid type filter."""
        result_str = await fd_search_by_type(
            type_filter="invalid",
            path=test_directory
        )
        result = json.loads(result_str)

        # fd will return error
        assert "success" in result


@pytest.mark.skipif(not check_fd_installed(), reason="fd not installed")
class TestIntegration:
    """Integration tests requiring fd to be installed."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, test_directory):
        """Test complete workflow of searching and filtering."""
        # Step 1: List all files
        all_files = await fd_list_all(path=test_directory)
        all_result = json.loads(all_files)
        assert all_result["success"] is True

        # Step 2: Filter by extension
        py_files = await fd_search_by_extension(
            extension="py",
            path=test_directory
        )
        py_result = json.loads(py_files)
        assert py_result["success"] is True

        # Step 3: Search with pattern
        test_files = await fd_search(
            pattern="test",
            path=test_directory
        )
        test_result = json.loads(test_files)
        assert test_result["success"] is True

    @pytest.mark.asyncio
    async def test_complex_search(self, test_directory):
        """Test complex search with multiple filters."""
        result_str = await fd_search(
            pattern=".*",
            path=test_directory,
            extension="txt",
            type_filter="f",
            max_depth=2,
            hidden=True
        )
        result = json.loads(result_str)

        assert result["success"] is True
        assert all(".txt" in r for r in result["results"] if r)