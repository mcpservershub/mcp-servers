"""Test MCP tools"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from inspektor_mcp.tools import (
    ListContainersTool,
    TraceExecTool,
    TraceNetworkTool,
    ProfileCPUTool,
    SnapshotSystemTool,
)
from inspektor_mcp.models import CommandResult


@pytest.fixture
def mock_command_executor():
    """Create a mock CommandExecutor"""
    with patch('inspektor_mcp.tools.base.CommandExecutor') as MockExecutor:
        mock_executor = MagicMock()
        MockExecutor.return_value = mock_executor
        mock_executor.execute = AsyncMock()
        yield mock_executor


class TestListContainersTool:
    @pytest.mark.asyncio
    async def test_list_containers_success(self, mock_command_executor):
        """Test successful container listing"""
        # Mock executor response
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": [
                {"id": "abc123", "name": "test1", "runtime": "docker"},
                {"id": "def456", "name": "test2", "runtime": "docker"}
            ],
            "command": "ig list-containers",
            "duration_ms": 100
        }
        
        tool = ListContainersTool()
        result = await tool.execute({
            "runtime": "docker",
            "output_format": "json"
        })
        
        assert isinstance(result, CommandResult)
        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["name"] == "test1"
    
    @pytest.mark.asyncio
    async def test_list_containers_with_filter(self, mock_command_executor):
        """Test container listing with name filter"""
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": [{"id": "abc123", "name": "nginx", "runtime": "docker"}],
            "command": "ig list-containers --containername nginx",
            "duration_ms": 50
        }
        
        tool = ListContainersTool()
        result = await tool.execute({
            "containername": "nginx",
            "output_format": "json"
        })
        
        # Verify the correct arguments were passed
        mock_command_executor.execute.assert_called_once()
        call_args = mock_command_executor.execute.call_args[0]
        assert "--containername" in call_args[1]
        assert "nginx" in call_args[1]


class TestTraceExecTool:
    @pytest.mark.asyncio
    async def test_trace_exec_host(self, mock_command_executor):
        """Test trace exec on host"""
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": [
                {"pid": 1234, "comm": "bash", "uid": 1000},
                {"pid": 5678, "comm": "ls", "uid": 1000}
            ],
            "command": "ig trace exec --host",
            "duration_ms": 10000
        }
        
        tool = TraceExecTool()
        result = await tool.execute({
            "target": "host",
            "duration": 10,
            "follow_fork": True
        })
        
        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["comm"] == "bash"
    
    @pytest.mark.asyncio
    async def test_trace_exec_container(self, mock_command_executor):
        """Test trace exec in container"""
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": [{"pid": 9999, "comm": "node", "container": "app"}],
            "command": "ig trace exec --containername app",
            "duration_ms": 5000
        }
        
        tool = TraceExecTool()
        result = await tool.execute({
            "target": "container",
            "container_name": "app",
            "duration": 5
        })
        
        assert result.success is True
        assert result.data[0]["container"] == "app"


class TestProfileCPUTool:
    @pytest.mark.asyncio
    async def test_profile_cpu_container(self, mock_command_executor):
        """Test CPU profiling for container"""
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": "flamegraph_data_here",
            "command": "ig profile cpu --containername app --frequency 99 --flamegraph",
            "duration_ms": 30000
        }
        
        tool = ProfileCPUTool()
        result = await tool.execute({
            "target": "container",
            "container_name": "app",
            "duration": 30,
            "frequency": 99,
            "output_format": "flamegraph"
        })
        
        assert result.success is True
        assert result.data == "flamegraph_data_here"
    
    @pytest.mark.asyncio
    async def test_profile_cpu_pid(self, mock_command_executor):
        """Test CPU profiling for specific PID"""
        mock_command_executor.execute.return_value = {
            "success": True,
            "data": {"samples": 1000},
            "command": "ig profile cpu --pid 12345",
            "duration_ms": 10000
        }
        
        tool = ProfileCPUTool()
        result = await tool.execute({
            "target": "pid",
            "pid": 12345,
            "duration": 10,
            "output_format": "raw"
        })
        
        assert result.success is True
        assert result.data["samples"] == 1000


class TestSnapshotSystemTool:
    @pytest.mark.asyncio
    async def test_snapshot_all(self, mock_command_executor):
        """Test taking all snapshots"""
        # Mock will be called twice (process and socket)
        mock_command_executor.execute.side_effect = [
            {
                "success": True,
                "data": [{"pid": 1, "comm": "systemd"}],
                "command": "ig snapshot process",
                "duration_ms": 100
            },
            {
                "success": True,
                "data": [{"protocol": "tcp", "state": "LISTEN"}],
                "command": "ig snapshot socket",
                "duration_ms": 100
            }
        ]
        
        tool = SnapshotSystemTool()
        result = await tool.execute({
            "snapshot_type": "all"
        })
        
        assert result.success is True
        assert "snapshots" in result.data
        assert len(result.data["snapshots"]) == 2
        assert result.data["snapshots"][0]["snapshot_type"] == "process"
        assert result.data["snapshots"][1]["snapshot_type"] == "socket"