"""Tests for LocAgent MCP Server core functionality."""

import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest
from mcp_server.server import LocAgentMCPServer, RepositoryConfig


class TestLocAgentMCPServer:
    """Test cases for LocAgentMCPServer class."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        server = LocAgentMCPServer()
        assert server.server is not None
        assert server.repository_config is None
        assert hasattr(server.server, 'list_tools')
        assert hasattr(server.server, 'call_tool')
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server: LocAgentMCPServer):
        """Test listing available tools."""
        request = ListToolsRequest(method="tools/list", id="test-1")
        tools = await mcp_server._list_tools(request)
        
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "setup_repository",
            "search_code_snippets", 
            "explore_tree_structure",
            "explore_graph_structure",
            "reset_repository"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    async def test_setup_repository_success(
        self, 
        mcp_server: LocAgentMCPServer, 
        temp_repo: Path,
        setup_repository_args: Dict[str, Any]
    ):
        """Test successful repository setup."""
        with patch('mcp_server.server.set_current_issue') as mock_set_issue:
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="setup_repository",
                    arguments=setup_repository_args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify mock was called
            mock_set_issue.assert_called_once()
            
            # Verify result
            assert result.content is not None
            assert len(result.content) == 1
            assert "Repository initialized successfully" in result.content[0].text
            
            # Verify server state
            assert mcp_server.repository_config is not None
            assert mcp_server.repository_config.repo_path == setup_repository_args["repo_path"]
            assert mcp_server.repository_config.instance_id == setup_repository_args["instance_id"]
    
    async def test_setup_repository_invalid_path(self, mcp_server: LocAgentMCPServer):
        """Test repository setup with invalid path."""
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="setup_repository",
                arguments={"repo_path": "/nonexistent/path"}
            )
        )
        
        result = await mcp_server._call_tool(request)
        
        # Should return error
        assert result.content is not None
        assert "Error:" in result.content[0].text
        assert "does not exist" in result.content[0].text
    
    async def test_reset_repository(self, mcp_server: LocAgentMCPServer):
        """Test repository reset functionality."""
        # First set up a repository config
        mcp_server.repository_config = RepositoryConfig(
            repo_path="/test/path",
            instance_id="test_id"
        )
        
        with patch('mcp_server.server.reset_current_issue') as mock_reset:
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="reset_repository",
                    arguments={}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify mock was called
            mock_reset.assert_called_once()
            
            # Verify result
            assert result.content is not None
            assert "Repository context has been reset" in result.content[0].text
            
            # Verify server state
            assert mcp_server.repository_config is None
    
    async def test_check_repository_setup_not_initialized(self, mcp_server: LocAgentMCPServer):
        """Test that tools fail when repository is not initialized."""
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="search_code_snippets",
                arguments={"search_terms": ["test"]}
            )
        )
        
        result = await mcp_server._call_tool(request)
        
        # Should return error about repository not being initialized
        assert result.content is not None
        assert "Repository not initialized" in result.content[0].text
    
    async def test_unknown_tool_error(self, mcp_server: LocAgentMCPServer):
        """Test handling of unknown tool calls."""
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="nonexistent_tool",
                arguments={}
            )
        )
        
        result = await mcp_server._call_tool(request)
        
        # Should return error about unknown tool
        assert result.content is not None
        assert "Unknown tool" in result.content[0].text


class TestRepositoryConfig:
    """Test cases for RepositoryConfig model."""
    
    def test_repository_config_creation(self):
        """Test RepositoryConfig model creation."""
        config = RepositoryConfig(
            repo_path="/test/path",
            instance_id="test_001",
            problem_statement="Test problem",
            base_commit="abc123"
        )
        
        assert config.repo_path == "/test/path"
        assert config.instance_id == "test_001"
        assert config.problem_statement == "Test problem"
        assert config.base_commit == "abc123"
    
    def test_repository_config_optional_fields(self):
        """Test RepositoryConfig with optional fields."""
        config = RepositoryConfig(repo_path="/test/path")
        
        assert config.repo_path == "/test/path"
        assert config.instance_id is None
        assert config.problem_statement is None
        assert config.base_commit is None