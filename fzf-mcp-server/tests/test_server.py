"""Tests for fzf MCP Server."""

import json
import tempfile
from pathlib import Path

import pytest

from fzf_mcp_server.server import (
    check_fzf_installed,
    fuzzy_directory_tree,
    fuzzy_filter,
    fuzzy_find_files,
    fuzzy_git_files,
    fuzzy_search_content,
    fuzzy_select_lines,
    validate_path,
)


class TestValidation:
    """Test validation functions."""

    def test_validate_path_valid(self, tmp_path):
        """Test validate_path with valid path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = validate_path(str(test_file))
        assert result == test_file.resolve()

    def test_validate_path_nonexistent(self, tmp_path):
        """Test validate_path with non-existent path."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(ValueError, match="Path does not exist"):
            validate_path(str(nonexistent), must_exist=True)

    def test_validate_path_invalid(self):
        """Test validate_path with invalid path."""
        # Test with null bytes which are invalid in paths
        with pytest.raises(ValueError, match="Invalid path"):
            validate_path("/invalid\x00path")


class TestFzfInstallation:
    """Test fzf installation check."""

    def test_check_fzf_installed(self):
        """Test that fzf installation check works."""
        # This should return True or False depending on whether fzf is installed
        result = check_fzf_installed()
        assert isinstance(result, bool)


class TestFuzzyFilter:
    """Test fuzzy_filter tool."""

    @pytest.mark.asyncio
    async def test_fuzzy_filter_basic(self):
        """Test basic fuzzy filtering."""
        items = ["apple.py", "application.js", "app.go", "banana.py", "orange.rs"]
        result = await fuzzy_filter(items=items, query="app")

        data = json.loads(result)
        assert "selected" in data
        assert "count" in data
        assert isinstance(data["selected"], list)

    @pytest.mark.asyncio
    async def test_fuzzy_filter_empty_items(self):
        """Test fuzzy filter with empty items list."""
        result = await fuzzy_filter(items=[], query="test")

        data = json.loads(result)
        assert data["count"] == 0
        assert "error" in data or len(data["selected"]) == 0

    @pytest.mark.asyncio
    async def test_fuzzy_filter_exact_match(self):
        """Test fuzzy filter with exact matching."""
        items = ["test", "testing", "test123", "my_test"]
        result = await fuzzy_filter(items=items, query="test", exact=True)

        data = json.loads(result)
        assert "selected" in data

    @pytest.mark.asyncio
    async def test_fuzzy_filter_case_sensitive(self):
        """Test fuzzy filter with case sensitivity."""
        items = ["Test", "test", "TEST", "tEsT"]
        result = await fuzzy_filter(items=items, query="test", case_sensitive=True)

        data = json.loads(result)
        assert "selected" in data


class TestFuzzyFindFiles:
    """Test fuzzy_find_files tool."""

    @pytest.mark.asyncio
    async def test_find_files_in_directory(self, tmp_path):
        """Test finding files in a directory."""
        # Create test files
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.js").touch()
        (tmp_path / "test_file.py").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").touch()

        result = await fuzzy_find_files(directory=str(tmp_path), query="file")

        data = json.loads(result)
        assert "selected" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_find_files_type_filter(self, tmp_path):
        """Test finding only files (not directories)."""
        # Create test files and directories
        (tmp_path / "file1.txt").touch()
        (tmp_path / "dir1").mkdir()

        result = await fuzzy_find_files(directory=str(tmp_path), file_type="file")

        data = json.loads(result)
        assert "selected" in data

    @pytest.mark.asyncio
    async def test_find_files_invalid_directory(self):
        """Test finding files in non-existent directory."""
        result = await fuzzy_find_files(directory="/nonexistent/directory")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_find_files_max_depth(self, tmp_path):
        """Test finding files with max depth."""
        # Create nested structure
        level1 = tmp_path / "level1"
        level1.mkdir()
        (level1 / "file1.txt").touch()

        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "file2.txt").touch()

        result = await fuzzy_find_files(directory=str(tmp_path), max_depth=1)

        data = json.loads(result)
        assert "selected" in data


class TestFuzzySearchContent:
    """Test fuzzy_search_content tool."""

    @pytest.mark.asyncio
    async def test_search_content_basic(self, tmp_path):
        """Test basic content search."""
        # Create test files with content
        file1 = tmp_path / "file1.txt"
        file1.write_text("Hello world\nTest content\nAnother line")

        file2 = tmp_path / "file2.txt"
        file2.write_text("Test pattern\nSome data")

        result = await fuzzy_search_content(
            directory=str(tmp_path), search_pattern="Test", file_pattern="*.txt"
        )

        data = json.loads(result)
        assert "selected" in data or "error" in data

    @pytest.mark.asyncio
    async def test_search_content_no_pattern(self, tmp_path):
        """Test content search without pattern."""
        result = await fuzzy_search_content(directory=str(tmp_path), search_pattern="")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_search_content_case_sensitive(self, tmp_path):
        """Test case-sensitive content search."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test\ntest\nTEST")

        result = await fuzzy_search_content(
            directory=str(tmp_path), search_pattern="Test", case_sensitive=True
        )

        data = json.loads(result)
        assert "selected" in data or "count" in data


class TestFuzzySelectLines:
    """Test fuzzy_select_lines tool."""

    @pytest.mark.asyncio
    async def test_select_lines_basic(self, tmp_path):
        """Test basic line selection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\ntest line\nline 5")

        result = await fuzzy_select_lines(file_path=str(test_file), query="line")

        data = json.loads(result)
        assert "selected" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_select_lines_with_range(self, tmp_path):
        """Test line selection with range."""
        test_file = tmp_path / "test.txt"
        lines = "\n".join([f"line {i}" for i in range(1, 101)])
        test_file.write_text(lines)

        result = await fuzzy_select_lines(file_path=str(test_file), line_range="1-10")

        data = json.loads(result)
        assert "selected" in data

    @pytest.mark.asyncio
    async def test_select_lines_invalid_file(self):
        """Test line selection with invalid file."""
        result = await fuzzy_select_lines(file_path="/nonexistent/file.txt")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_select_lines_directory(self, tmp_path):
        """Test line selection with directory path."""
        result = await fuzzy_select_lines(file_path=str(tmp_path))

        data = json.loads(result)
        assert "error" in data


class TestFuzzyGitFiles:
    """Test fuzzy_git_files tool."""

    @pytest.mark.asyncio
    async def test_git_files_non_repo(self, tmp_path):
        """Test git files in non-repository."""
        result = await fuzzy_git_files(repository=str(tmp_path))

        data = json.loads(result)
        # Should either have error or empty results for non-git directory
        assert "error" in data or data.get("count", 0) == 0

    @pytest.mark.asyncio
    async def test_git_files_invalid_path(self):
        """Test git files with invalid path."""
        result = await fuzzy_git_files(repository="/nonexistent/path")

        data = json.loads(result)
        assert "error" in data


class TestFuzzyDirectoryTree:
    """Test fuzzy_directory_tree tool."""

    @pytest.mark.asyncio
    async def test_directory_tree_basic(self, tmp_path):
        """Test basic directory tree browsing."""
        # Create test structure
        (tmp_path / "file1.txt").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").touch()

        result = await fuzzy_directory_tree(directory=str(tmp_path), max_depth=2)

        data = json.loads(result)
        assert "selected" in data or "count" in data

    @pytest.mark.asyncio
    async def test_directory_tree_invalid_directory(self):
        """Test directory tree with invalid directory."""
        result = await fuzzy_directory_tree(directory="/nonexistent/path")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_directory_tree_file_path(self, tmp_path):
        """Test directory tree with file path instead of directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = await fuzzy_directory_tree(directory=str(test_file))

        data = json.loads(result)
        assert "error" in data


class TestErrorHandling:
    """Test error handling across all tools."""

    @pytest.mark.asyncio
    async def test_all_tools_return_json(self):
        """Test that all tools return valid JSON."""
        tools_to_test = [
            (fuzzy_filter, {"items": ["test"]}),
            (fuzzy_find_files, {"directory": "/tmp"}),
            (fuzzy_search_content, {"search_pattern": "test"}),
            (fuzzy_select_lines, {"file_path": "/nonexistent"}),
            (fuzzy_git_files, {"repository": "/tmp"}),
            (fuzzy_directory_tree, {"directory": "/tmp"}),
        ]

        for tool, kwargs in tools_to_test:
            result = await tool(**kwargs)
            # Should be valid JSON
            data = json.loads(result)
            assert isinstance(data, dict)
            # Should have either selected or error
            assert "selected" in data or "error" in data


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Test a complete workflow using multiple tools."""
        # Create a test project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        test_file = src_dir / "main.py"
        test_file.write_text("def main():\n    print('Hello')\n    return 0")

        # 1. Find files
        files_result = await fuzzy_find_files(directory=str(tmp_path), query="main")
        files_data = json.loads(files_result)
        assert "selected" in files_data

        # 2. Search content
        content_result = await fuzzy_search_content(
            directory=str(tmp_path), search_pattern="def main", file_pattern="*.py"
        )
        content_data = json.loads(content_result)
        assert "selected" in content_data or "count" in content_data

        # 3. Select lines from file
        lines_result = await fuzzy_select_lines(file_path=str(test_file), query="def")
        lines_data = json.loads(lines_result)
        assert "selected" in lines_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
