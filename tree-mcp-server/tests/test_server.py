#!/usr/bin/env python3.12
"""Test suite for Tree MCP Server."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from tree_mcp.server import (
    tree_basic,
    tree_with_size,
    tree_directories_only,
    tree_with_permissions,
    tree_with_pattern,
    tree_with_dates,
    tree_full_paths,
    tree_json_output,
    tree_xml_output,
    tree_colorized,
    tree_hidden_files,
    tree_advanced
)


@pytest_asyncio.fixture
async def test_directory():
    """Create a temporary test directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "dir1").mkdir()
        (base / "dir2").mkdir()
        (base / "dir1" / "subdir1").mkdir()
        (base / ".hidden_dir").mkdir()
        
        (base / "file1.txt").write_text("content1")
        (base / "file2.py").write_text("print('hello')")
        (base / "dir1" / "file3.md").write_text("# Markdown")
        (base / "dir1" / "subdir1" / "deep.txt").write_text("deep content")
        (base / ".hidden_file").write_text("hidden")
        
        yield str(base)


@pytest.mark.asyncio
async def test_tree_basic(test_directory):
    """Test basic tree functionality."""
    result = await tree_basic(path=test_directory)
    assert result["success"] is True
    assert "dir1" in result["stdout"]
    assert "dir2" in result["stdout"]
    assert "file1.txt" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_basic_with_output_file(test_directory):
    """Test basic tree with output file."""
    output_file = Path(test_directory) / "output.txt"
    result = await tree_basic(path=test_directory, output_file=str(output_file))
    
    assert result["success"] is True
    assert output_file.exists()
    assert "Output written to:" in result["output_file_status"]
    
    content = output_file.read_text()
    assert "dir1" in content


@pytest.mark.asyncio
async def test_tree_with_size(test_directory):
    """Test tree with file sizes."""
    result = await tree_with_size(path=test_directory, human_readable=True)
    assert result["success"] is True
    assert "dir1" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_directories_only(test_directory):
    """Test tree showing only directories."""
    result = await tree_directories_only(path=test_directory)
    assert result["success"] is True
    assert "dir1" in result["stdout"]
    assert "dir2" in result["stdout"]
    assert "file1.txt" not in result["stdout"]


@pytest.mark.asyncio
async def test_tree_directories_with_depth(test_directory):
    """Test tree with max depth."""
    result = await tree_directories_only(path=test_directory, max_depth=1)
    assert result["success"] is True
    assert "dir1" in result["stdout"]
    assert "subdir1" not in result["stdout"]


@pytest.mark.asyncio
async def test_tree_with_permissions(test_directory):
    """Test tree with permissions."""
    result = await tree_with_permissions(path=test_directory, show_owner=True)
    assert result["success"] is True
    assert "dir1" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_with_pattern(test_directory):
    """Test tree with pattern matching."""
    result = await tree_with_pattern(path=test_directory, pattern="*.py")
    assert result["success"] is True
    assert "file2.py" in result["stdout"]
    assert "file1.txt" not in result["stdout"] or "file1.txt" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_with_exclude_pattern(test_directory):
    """Test tree with exclude pattern."""
    result = await tree_with_pattern(path=test_directory, exclude_pattern="*.txt")
    assert result["success"] is True
    assert "file2.py" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_with_dates(test_directory):
    """Test tree with dates."""
    result = await tree_with_dates(path=test_directory)
    assert result["success"] is True
    assert "dir1" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_full_paths(test_directory):
    """Test tree with full paths."""
    result = await tree_full_paths(path=test_directory)
    assert result["success"] is True
    assert test_directory in result["stdout"]


@pytest.mark.asyncio
async def test_tree_json_output(test_directory):
    """Test tree JSON output."""
    result = await tree_json_output(path=test_directory)
    assert result["success"] is True
    assert "json_data" in result
    assert isinstance(result["json_data"], list)


@pytest.mark.asyncio
async def test_tree_xml_output(test_directory):
    """Test tree XML output."""
    result = await tree_xml_output(path=test_directory)
    assert result["success"] is True
    assert "<tree>" in result["stdout"] or "<?xml" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_colorized(test_directory):
    """Test colorized tree output."""
    result = await tree_colorized(path=test_directory, force_colors=True)
    assert result["success"] is True
    assert "dir1" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_hidden_files(test_directory):
    """Test tree with hidden files."""
    result = await tree_hidden_files(path=test_directory, show_hidden=True)
    assert result["success"] is True
    assert ".hidden_dir" in result["stdout"]
    assert ".hidden_file" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_advanced_combined(test_directory):
    """Test advanced tree with multiple options."""
    result = await tree_advanced(
        path=test_directory,
        max_depth=2,
        show_size=True,
        human_readable=True,
        show_hidden=True,
        pattern="*.txt",
        sort_by_time=False
    )
    assert result["success"] is True
    assert "file1.txt" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_advanced_json_format(test_directory):
    """Test advanced tree with JSON output."""
    result = await tree_advanced(
        path=test_directory,
        output_format="json",
        max_depth=2
    )
    assert result["success"] is True
    assert "json_data" in result


@pytest.mark.asyncio
async def test_invalid_path():
    """Test tree with invalid path."""
    result = await tree_basic(path="/nonexistent/path/that/does/not/exist")
    assert result["success"] is False
    assert "does not exist" in result["error"]


@pytest.mark.asyncio
async def test_invalid_max_depth():
    """Test tree with invalid max depth."""
    result = await tree_directories_only(path=".", max_depth=0)
    assert result["success"] is False
    assert "must be at least 1" in result["error"]


@pytest.mark.asyncio
async def test_tree_advanced_xml_format(test_directory):
    """Test advanced tree with XML output."""
    result = await tree_advanced(
        path=test_directory,
        output_format="xml",
        directories_only=True
    )
    assert result["success"] is True
    assert "<tree>" in result["stdout"] or "<?xml" in result["stdout"]


@pytest.mark.asyncio
async def test_tree_advanced_with_all_options(test_directory):
    """Test advanced tree with all options enabled."""
    output_file = Path(test_directory) / "full_output.txt"
    result = await tree_advanced(
        path=test_directory,
        max_depth=3,
        directories_only=False,
        show_size=True,
        human_readable=True,
        show_permissions=True,
        show_owner=True,
        show_dates=True,
        full_paths=False,
        show_hidden=True,
        pattern=None,
        exclude_pattern="*.pyc",
        sort_by_time=True,
        reverse_sort=False,
        no_indent=False,
        output_format=None,
        output_file=str(output_file)
    )
    assert result["success"] is True
    assert output_file.exists()


if __name__ == "__main__":
    print("Running Tree MCP Server tests...")
    pytest.main([__file__, "-v", "--tb=short"])