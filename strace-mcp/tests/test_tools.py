#!/usr/bin/env python3
"""
Test suite for strace MCP server tools
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strace_mcp.server import (
    check_strace_available,
    build_strace_command,
    TraceOptions,
    run_strace
)


class TestTraceOptions:
    """Test TraceOptions validation"""
    
    def test_valid_options(self):
        """Test valid trace options"""
        opts = TraceOptions(
            trace_filter="file",
            follow_forks=True,
            max_string_size=64,
            timeout=60,
            show_timestamps=True
        )
        assert opts.trace_filter == "file"
        assert opts.follow_forks == True
        assert opts.max_string_size == 64
        assert opts.timeout == 60
        assert opts.show_timestamps == True
    
    def test_invalid_filter(self):
        """Test invalid trace filter"""
        with pytest.raises(ValueError, match="Invalid filter"):
            TraceOptions(trace_filter="invalid")
    
    def test_invalid_timeout(self):
        """Test invalid timeout values"""
        with pytest.raises(ValueError, match="Timeout must be between"):
            TraceOptions(timeout=0)
        
        with pytest.raises(ValueError, match="Timeout must be between"):
            TraceOptions(timeout=301)


class TestBuildStraceCommand:
    """Test strace command building"""
    
    def test_basic_command(self):
        """Test basic command building"""
        opts = TraceOptions()
        cmd = build_strace_command(["ls"], opts)
        assert cmd[0] == "strace"
        assert "-s" in cmd
        assert "32" in cmd
        assert "ls" in cmd
    
    def test_with_file_filter(self):
        """Test command with file filter"""
        opts = TraceOptions(trace_filter="file")
        cmd = build_strace_command(["cat", "file.txt"], opts)
        assert "-e" in cmd
        assert "trace=%file" in cmd
    
    def test_with_follow_forks(self):
        """Test command with follow forks"""
        opts = TraceOptions(follow_forks=True)
        cmd = build_strace_command(["bash"], opts)
        assert "-f" in cmd
    
    def test_with_timestamps(self):
        """Test command with timestamps"""
        opts = TraceOptions(show_timestamps=True)
        cmd = build_strace_command(["date"], opts)
        assert "-t" in cmd


class TestHelperFunctions:
    """Test helper functions"""
    
    @patch('shutil.which')
    def test_check_strace_available_true(self, mock_which):
        """Test strace is available"""
        mock_which.return_value = "/usr/bin/strace"
        assert check_strace_available() == True
    
    @patch('shutil.which')
    def test_check_strace_available_false(self, mock_which):
        """Test strace is not available"""
        mock_which.return_value = None
        assert check_strace_available() == False


@pytest.mark.asyncio
class TestRunStrace:
    """Test run_strace function"""
    
    @patch('asyncio.create_subprocess_exec')
    async def test_successful_execution(self, mock_create):
        """Test successful strace execution"""
        # Mock process
        mock_proc = MagicMock()
        mock_proc.communicate = MagicMock(return_value=(b"", b"execve(\"/bin/ls\", [\"ls\"], 0x7fff) = 0\n"))
        mock_proc.returncode = 0
        
        # Make communicate async
        async def async_communicate():
            return mock_proc.communicate.return_value
        mock_proc.communicate = async_communicate
        
        # Mock create_subprocess_exec to return async
        async def async_create(*args, **kwargs):
            return mock_proc
        mock_create.side_effect = async_create
        
        result = await run_strace(["strace", "ls"], 10)
        assert result["success"] == True
        assert "execve" in result["output"]
        assert result["lines"] == 1
    
    @patch('asyncio.create_subprocess_exec')
    @patch('asyncio.wait_for')
    async def test_timeout(self, mock_wait_for, mock_create):
        """Test timeout handling"""
        # Mock process
        mock_proc = MagicMock()
        mock_proc.terminate = MagicMock()
        mock_proc.kill = MagicMock()
        mock_proc.returncode = None
        
        # Mock create_subprocess_exec
        async def async_create(*args, **kwargs):
            return mock_proc
        mock_create.side_effect = async_create
        
        # Mock timeout
        mock_wait_for.side_effect = asyncio.TimeoutError()
        
        result = await run_strace(["strace", "sleep", "100"], 1)
        assert result["success"] == False
        assert "timed out" in result["error"]
        mock_proc.terminate.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])