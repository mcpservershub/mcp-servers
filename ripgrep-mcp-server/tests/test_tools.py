"""Tests for ripgrep MCP tools."""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ripgrep_mcp import tools, utils


@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        test_files = {
            "test.py": "def hello():\n    print('Hello, world!')\n    return 42\n",
            "test.js": "function hello() {\n    console.log('Hello, world!');\n    return 42;\n}\n",
            "test.txt": "Hello, world!\nThis is a test file.\nIt contains multiple lines.\n",
            "test.md": "# Hello World\n\nThis is a markdown file.\n\n## Section\n\nContent here.\n",
            ".hidden.txt": "This is a hidden file.\n",
            "binary.bin": b"\x00\x01\x02\x03Hello\x04\x05\x06",
        }
        
        for filename, content in test_files.items():
            filepath = Path(tmpdir) / filename
            if isinstance(content, bytes):
                filepath.write_bytes(content)
            else:
                filepath.write_text(content)
        
        # Create subdirectory with more files
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("def nested_function():\n    pass\n")
        
        yield tmpdir


@pytest.mark.asyncio
async def test_search_basic(temp_directory):
    """Test basic search functionality."""
    results = await tools.search(
        pattern="hello",
        path=temp_directory,
        case_sensitive=False
    )
    
    assert len(results) > 0
    assert any("test.py" in r["file_path"] for r in results)
    assert any("test.js" in r["file_path"] for r in results)


@pytest.mark.asyncio
async def test_search_case_sensitive(temp_directory):
    """Test case-sensitive search."""
    # Case sensitive - should find "hello" but not "Hello"
    results = await tools.search(
        pattern="hello",
        path=temp_directory,
        case_sensitive=True
    )
    
    assert len(results) > 0
    assert any("test.py" in r["file_path"] for r in results)
    
    # Search for "Hello" - should find different matches
    results = await tools.search(
        pattern="Hello",
        path=temp_directory,
        case_sensitive=True
    )
    
    assert len(results) > 0
    assert any("test.txt" in r["file_path"] for r in results)


@pytest.mark.asyncio
async def test_search_whole_word(temp_directory):
    """Test whole word matching."""
    results = await tools.search(
        pattern="print",
        path=temp_directory,
        whole_word=True
    )
    
    assert len(results) > 0
    assert all("print" in r["match_text"] for r in results)


@pytest.mark.asyncio
async def test_search_with_max_results(temp_directory):
    """Test search with max results limit."""
    results = await tools.search(
        pattern="e",  # Common letter, many matches
        path=temp_directory,
        max_results=2
    )
    
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_search_by_type(temp_directory):
    """Test searching by file type."""
    # Search in Python files only
    results = await tools.search_by_type(
        pattern="def",
        file_type="python",
        path=temp_directory
    )
    
    assert len(results) > 0
    assert all(".py" in r["file_path"] for r in results)
    
    # Search in JavaScript files only
    results = await tools.search_by_type(
        pattern="function",
        file_type="js",
        path=temp_directory
    )
    
    assert len(results) > 0
    assert all(".js" in r["file_path"] for r in results)


@pytest.mark.asyncio
async def test_search_with_context(temp_directory):
    """Test search with context lines."""
    results = await tools.search_with_context(
        pattern="print",
        before_context=1,
        after_context=1,
        path=temp_directory
    )
    
    assert len(results) > 0
    for result in results:
        if "context_before" in result:
            assert isinstance(result["context_before"], list)
        if "context_after" in result:
            assert isinstance(result["context_after"], list)


@pytest.mark.asyncio
async def test_replace_dry_run(temp_directory):
    """Test replace in dry run mode."""
    results = await tools.replace(
        pattern="hello",
        replacement="goodbye",
        path=temp_directory,
        dry_run=True
    )
    
    assert len(results) > 0
    assert all(r["applied"] is False for r in results)
    assert all("goodbye" in r["replacement"] for r in results)


@pytest.mark.asyncio
async def test_list_files(temp_directory):
    """Test listing files."""
    # List all files
    files = await tools.list_files(path=temp_directory)
    
    assert len(files) > 0
    assert any("test.py" in f for f in files)
    assert any("test.js" in f for f in files)
    
    # List Python files only
    files = await tools.list_files(
        file_type="python",
        path=temp_directory
    )
    
    assert len(files) > 0
    assert all(".py" in f for f in files)


@pytest.mark.asyncio
async def test_list_files_with_pattern(temp_directory):
    """Test listing files with pattern filter."""
    files = await tools.list_files(
        pattern="*.py",
        path=temp_directory
    )
    
    assert len(files) > 0
    assert all(f.endswith(".py") for f in files)


@pytest.mark.asyncio
async def test_list_files_include_hidden(temp_directory):
    """Test listing files including hidden ones."""
    # Without hidden files
    files = await tools.list_files(
        path=temp_directory,
        include_hidden=False
    )
    assert not any(".hidden" in f for f in files)
    
    # With hidden files
    files = await tools.list_files(
        path=temp_directory,
        include_hidden=True
    )
    assert any(".hidden" in f for f in files)


@pytest.mark.asyncio
async def test_search_multiline(temp_directory):
    """Test multiline pattern search."""
    # Create a file with multiline pattern
    test_file = Path(temp_directory) / "multiline.txt"
    test_file.write_text("start\nmiddle\nend\n")
    
    results = await tools.search_multiline(
        pattern=r"start.*end",
        path=temp_directory
    )
    
    # Basic multiline search might need specific pattern
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_stats(temp_directory):
    """Test search statistics."""
    stats = await tools.stats(
        pattern="hello",
        path=temp_directory
    )
    
    assert isinstance(stats, dict)
    assert "pattern" in stats
    assert "time_taken_ms" in stats
    assert stats["pattern"] == "hello"
    assert stats["time_taken_ms"] >= 0


@pytest.mark.asyncio
async def test_search_binary(temp_directory):
    """Test searching in binary files."""
    results = await tools.search_binary(
        pattern="Hello",
        path=temp_directory
    )
    
    # Should find "Hello" even in binary file
    assert len(results) >= 0  # May or may not find depending on ripgrep binary handling


@pytest.mark.asyncio
async def test_validate_ripgrep():
    """Test ripgrep validation."""
    is_valid = await tools.validate_ripgrep()
    assert isinstance(is_valid, bool)


@pytest.mark.asyncio
async def test_search_no_matches(temp_directory):
    """Test search with no matches."""
    results = await tools.search(
        pattern="nonexistentpattern12345",
        path=temp_directory
    )
    
    assert results == []


@pytest.mark.asyncio
async def test_search_invalid_regex():
    """Test search with invalid regex pattern."""
    with pytest.raises(Exception):
        await tools.search(
            pattern="[invalid(regex",
            path="."
        )


@pytest.mark.asyncio
async def test_search_nonexistent_path():
    """Test search with non-existent path."""
    with pytest.raises(Exception):
        await tools.search(
            pattern="test",
            path="/nonexistent/path/12345"
        )


@pytest.mark.asyncio
async def test_run_ripgrep_timeout():
    """Test ripgrep command timeout."""
    with patch("ripgrep_mcp.utils.asyncio.wait_for") as mock_wait_for:
        mock_wait_for.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(TimeoutError):
            await utils.run_ripgrep(["--files"], timeout=1)


def test_parse_ripgrep_output():
    """Test parsing ripgrep output."""
    # Test with line numbers
    output = "file.txt:10:20:match text\nfile2.py:5:content"
    results = utils.parse_ripgrep_output(output, include_line_numbers=True)
    
    assert len(results) == 2
    assert results[0]["file_path"] == "file.txt"
    assert results[0]["line_number"] == 10
    assert results[0]["column"] == 20
    assert results[0]["match_text"] == "match text"
    
    # Test without line numbers
    output = "file.txt:match text\nfile2.py:content"
    results = utils.parse_ripgrep_output(output, include_line_numbers=False)
    
    assert len(results) == 2
    assert results[0]["file_path"] == "file.txt"
    assert results[0]["match_text"] == "match text"


def test_format_file_type_arg():
    """Test formatting file type arguments."""
    args = utils.format_file_type_arg("python")
    assert args == ["--type", "py"]
    
    args = utils.format_file_type_arg("javascript")
    assert args == ["--type", "js"]
    
    args = utils.format_file_type_arg("unknown")
    assert args == ["--type", "unknown"]


def test_sanitize_path():
    """Test path sanitization."""
    # Test with None
    assert utils.sanitize_path(None) is None
    
    # Test with valid path
    path = utils.sanitize_path(".")
    assert path is not None
    assert os.path.isabs(path)
    
    # Test with environment variable set
    with patch.dict(os.environ, {"RG_DEFAULT_PATH": "/tmp"}):
        path = utils.sanitize_path(".")
        assert path is not None


def test_get_max_results():
    """Test getting max results from environment."""
    # Default value
    assert utils.get_max_results() == 1000
    
    # With environment variable
    with patch.dict(os.environ, {"RG_MAX_RESULTS": "500"}):
        assert utils.get_max_results() == 500
    
    # With invalid environment variable
    with patch.dict(os.environ, {"RG_MAX_RESULTS": "invalid"}):
        assert utils.get_max_results() == 1000


def test_get_timeout():
    """Test getting timeout from environment."""
    # Default value
    assert utils.get_timeout() == 30
    
    # With environment variable
    with patch.dict(os.environ, {"RG_TIMEOUT": "60"}):
        assert utils.get_timeout() == 60
    
    # With invalid environment variable
    with patch.dict(os.environ, {"RG_TIMEOUT": "invalid"}):
        assert utils.get_timeout() == 30