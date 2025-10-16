"""Tests for the MCP server implementation."""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ctags_mcp.server import (
    generate_tags,
    find_symbol,
    go_to_definition,
    list_symbols_in_file,
    get_file_outline,
    list_tags_files,
    get_tags_info,
)


@pytest.mark.asyncio
async def test_generate_tags(temp_dir, sample_python_file):
    """Test tags generation."""
    output_file = os.path.join(temp_dir, "test.tags")
    
    # Mock the ctags_wrapper to avoid needing actual ctags binary
    with patch('ctags_mcp.server.ctags_wrapper.generate_tags') as mock_generate:
        mock_generate.return_value = {
            "success": True,
            "tags_file": output_file,
            "tag_count": 6,
            "command": "ctags -f test.tags sample.py"
        }
        
        result = await generate_tags(
            path=temp_dir,
            output_file=output_file,
            recursive=True
        )
        
        assert result["success"] is True
        assert result["tags_file"] == output_file
        assert result["tag_count"] == 6


@pytest.mark.asyncio
async def test_find_symbol_exact(sample_tags_file):
    """Test exact symbol search."""
    with patch('ctags_mcp.server.ctags_wrapper.find_symbol') as mock_find:
        mock_find.return_value = [
            {
                "name": "MyClass",
                "file": "sample.py",
                "line": 2,
                "kind": "class",
                "pattern": "/^class MyClass:/"
            }
        ]
        
        results = await find_symbol(
            symbol_name="MyClass",
            tags_file=sample_tags_file,
            match_type="exact"
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "MyClass"
        assert results[0]["kind"] == "class"


@pytest.mark.asyncio
async def test_find_symbol_partial(sample_tags_file):
    """Test partial symbol search."""
    with patch('ctags_mcp.server.ctags_wrapper.find_symbol') as mock_find:
        mock_find.return_value = [
            {
                "name": "public_method",
                "file": "sample.py",
                "line": 8,
                "kind": "method",
                "pattern": "/^    def public_method(self):/"
            },
            {
                "name": "_private_method",
                "file": "sample.py",
                "line": 12,
                "kind": "method",
                "pattern": "/^    def _private_method(self):/"
            }
        ]
        
        results = await find_symbol(
            symbol_name="method",
            tags_file=sample_tags_file,
            match_type="partial"
        )
        
        assert len(results) == 2
        assert all("method" in r["name"] for r in results)


@pytest.mark.asyncio
async def test_go_to_definition(sample_tags_file):
    """Test go to definition."""
    with patch('ctags_mcp.server.ctags_wrapper.find_symbol') as mock_find:
        mock_find.return_value = [
            {
                "name": "standalone_function",
                "file": "sample.py",
                "line": 16,
                "kind": "function",
                "pattern": "/^def standalone_function(param1, param2):/"
            }
        ]
        
        result = await go_to_definition(
            symbol_name="standalone_function",
            tags_file=sample_tags_file
        )
        
        assert result["success"] is True
        assert result["definition"]["name"] == "standalone_function"
        assert result["definition"]["line"] == 16


@pytest.mark.asyncio
async def test_list_symbols_in_file(sample_tags_file, sample_python_file):
    """Test listing symbols in a file."""
    with patch('ctags_mcp.server.ctags_wrapper.get_symbols_in_file') as mock_get:
        mock_get.return_value = [
            {"name": "MyClass", "file": sample_python_file, "line": 2, "kind": "class"},
            {"name": "__init__", "file": sample_python_file, "line": 5, "kind": "method"},
            {"name": "public_method", "file": sample_python_file, "line": 8, "kind": "method"},
            {"name": "standalone_function", "file": sample_python_file, "line": 16, "kind": "function"},
        ]
        
        result = await list_symbols_in_file(
            file_path=sample_python_file,
            tags_file=sample_tags_file,
            group_by_kind=True
        )
        
        assert result["success"] is True
        assert "symbols" in result
        assert result["total_count"] == 4


@pytest.mark.asyncio
async def test_get_file_outline(sample_tags_file, sample_python_file):
    """Test file outline generation."""
    with patch('ctags_mcp.server.ctags_wrapper.get_symbols_in_file') as mock_get:
        mock_get.return_value = [
            {"name": "MyClass", "file": sample_python_file, "line": 2, "kind": "class"},
            {"name": "public_method", "file": sample_python_file, "line": 8, "kind": "method"},
            {"name": "_private_method", "file": sample_python_file, "line": 12, "kind": "method"},
            {"name": "standalone_function", "file": sample_python_file, "line": 16, "kind": "function"},
            {"name": "GLOBAL_VARIABLE", "file": sample_python_file, "line": 20, "kind": "variable"},
        ]
        
        result = await get_file_outline(
            file_path=sample_python_file,
            tags_file=sample_tags_file,
            include_private=False
        )
        
        assert result["success"] is True
        assert "outline" in result
        assert len(result["outline"]["classes"]) == 1
        assert len(result["outline"]["functions"]) >= 1


@pytest.mark.asyncio
async def test_list_tags_files(temp_dir, sample_tags_file):
    """Test listing tags files."""
    result = await list_tags_files(
        search_path=temp_dir,
        include_stats=True
    )
    
    assert isinstance(result, list)
    assert len(result) >= 1
    assert any(f["name"] == "tags" for f in result)


@pytest.mark.asyncio
async def test_get_tags_info(sample_tags_file):
    """Test getting tags file info."""
    with patch('ctags_mcp.server.ctags_wrapper.get_tags_info') as mock_info:
        mock_info.return_value = {
            "file": sample_tags_file,
            "size": 1024,
            "format": 2,
            "sort": 1,
            "tag_count": 6
        }
        
        result = await get_tags_info(tags_file=sample_tags_file)
        
        assert result["success"] is True
        assert "info" in result
        assert result["info"]["tag_count"] == 6


@pytest.mark.asyncio
async def test_invalid_path():
    """Test with invalid path."""
    result = await generate_tags(
        path="/nonexistent/path",
        output_file="tags"
    )
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_invalid_tags_file():
    """Test with invalid tags file."""
    results = await find_symbol(
        symbol_name="test",
        tags_file="/nonexistent/tags"
    )
    
    assert results == []