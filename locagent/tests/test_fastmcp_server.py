"""Tests for FastMCP-based LocAgent MCP Server."""

import pytest
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
import json

# Import the FastMCP app and functions
from mcp_server.server import (
    app,
    setup_repository,
    reset_repository,
    search_code_snippets,
    explore_tree_structure,
    explore_graph_structure,
    _repository_config
)


class TestFastMCPServer:
    """Test cases for FastMCP-based LocAgent MCP Server."""
    
    def test_app_initialization(self):
        """Test that the FastMCP app is properly initialized."""
        assert app is not None
        assert app.name == "LocAgent MCP Server"
        # Check that tools are registered
        tools = app.get_tools()
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "setup_repository",
            "reset_repository", 
            "search_code_snippets",
            "explore_tree_structure",
            "explore_graph_structure"
        ]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @pytest.mark.asyncio
    async def test_setup_repository_success(self):
        """Test successful repository setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch('mcp_server.server.set_current_issue') as mock_set_issue:
                result = await setup_repository(
                    repo_path=str(temp_path),
                    instance_id="test_001",
                    problem_statement="Test problem"
                )
                
                # Verify mock was called
                mock_set_issue.assert_called_once()
                
                # Verify result
                assert "Repository initialized successfully" in result
                assert str(temp_path) in result
                assert "test_001" in result
                assert "Test problem" in result
                
                # Verify global state
                import mcp_server.server as server_module
                assert server_module._repository_config is not None
                assert server_module._repository_config["repo_path"] == str(temp_path)
                assert server_module._repository_config["instance_id"] == "test_001"
    
    @pytest.mark.asyncio
    async def test_setup_repository_invalid_path(self):
        """Test repository setup with invalid path."""
        with pytest.raises(RuntimeError) as exc_info:
            await setup_repository(repo_path="/nonexistent/path")
        
        assert "Failed to setup repository" in str(exc_info.value)
        assert "does not exist" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_reset_repository(self):
        """Test repository reset functionality."""
        # First set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {
            "repo_path": "/test/path",
            "instance_id": "test_id"
        }
        
        with patch('mcp_server.server.reset_current_issue') as mock_reset:
            result = await reset_repository()
            
            # Verify mock was called
            mock_reset.assert_called_once()
            
            # Verify result
            assert "Repository context has been reset" in result
            
            # Verify global state
            assert server_module._repository_config is None
    
    @pytest.mark.asyncio
    async def test_search_code_snippets_success(self):
        """Test successful code search."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = "Found 3 code snippets matching your search..."
            
            result = await search_code_snippets(
                search_terms=["MainClass", "process_data"],
                file_path_or_pattern="**/*.py"
            )
            
            # Verify function was called with correct arguments
            mock_search.assert_called_once_with(
                search_terms=["MainClass", "process_data"],
                line_nums=None,
                file_path_or_pattern="**/*.py"
            )
            
            # Verify result
            assert "Found 3 code snippets" in result
    
    @pytest.mark.asyncio
    async def test_search_without_repository_setup(self):
        """Test that search fails when repository is not set up."""
        # Clear repository state
        import mcp_server.server as server_module
        server_module._repository_config = None
        
        with pytest.raises(RuntimeError) as exc_info:
            await search_code_snippets(search_terms=["test"])
        
        assert "Repository not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_invalid_arguments(self):
        """Test search with invalid arguments."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with pytest.raises(RuntimeError) as exc_info:
            await search_code_snippets()  # No search terms or line numbers
        
        assert "Search failed" in str(exc_info.value)
        assert "Either search_terms or line_nums must be provided" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_with_line_numbers(self):
        """Test search with line numbers."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = {
                "results": [
                    {"file": "main.py", "line": 5, "content": "class MainClass:"}
                ]
            }
            
            result = await search_code_snippets(
                line_nums=[5, 10, 15],
                file_path_or_pattern="main.py"
            )
            
            # Verify function was called with correct arguments
            mock_search.assert_called_once_with(
                search_terms=None,
                line_nums=[5, 10, 15],
                file_path_or_pattern="main.py"
            )
            
            # Verify result contains JSON
            assert "results" in result
            assert "main.py" in result
    
    @pytest.mark.asyncio
    async def test_explore_tree_structure_success(self):
        """Test successful tree structure exploration."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = """
Tree Structure:
main.py:MainClass
├── process_data (method)
├── calculate_sum (method)
└── __init__ (method)
"""
            
            result = await explore_tree_structure(
                start_entities=["main.py:MainClass"],
                direction="downstream",
                traversal_depth=2
            )
            
            # Verify function was called with correct arguments
            mock_explore.assert_called_once_with(
                start_entities=["main.py:MainClass"],
                direction="downstream",
                traversal_depth=2,
                entity_type_filter=None,
                dependency_type_filter=None
            )
            
            # Verify result
            assert "Tree Structure" in result
            assert "main.py:MainClass" in result
    
    @pytest.mark.asyncio
    async def test_explore_graph_structure_success(self):
        """Test successful graph structure exploration."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = {
                "nodes": ["main.py:MainClass", "utils.py:Logger"],
                "edges": [{"from": "main.py:MainClass", "to": "utils.py:Logger"}]
            }
            
            result = await explore_graph_structure(
                start_entities=["main.py:MainClass"],
                direction="both",
                traversal_depth=-1
            )
            
            # Verify function was called with correct arguments
            mock_explore.assert_called_once_with(
                start_entities=["main.py:MainClass"],
                direction="both",
                traversal_depth=-1,
                entity_type_filter=None,
                dependency_type_filter=None
            )
            
            # Verify result contains JSON
            assert "nodes" in result
            assert "edges" in result
    
    @pytest.mark.asyncio
    async def test_explore_without_repository_setup(self):
        """Test that exploration fails when repository is not set up."""
        # Clear repository state
        import mcp_server.server as server_module
        server_module._repository_config = None
        
        with pytest.raises(RuntimeError) as exc_info:
            await explore_tree_structure(start_entities=["main.py"])
        
        assert "Repository not initialized" in str(exc_info.value)
        
        with pytest.raises(RuntimeError) as exc_info:
            await explore_graph_structure(start_entities=["main.py"])
        
        assert "Repository not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_function_exception_handling(self):
        """Test handling of exceptions from underlying LocAgent functions."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        # Test search exception
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.side_effect = Exception("Test search error")
            
            with pytest.raises(RuntimeError) as exc_info:
                await search_code_snippets(search_terms=["test"])
            
            assert "Search failed" in str(exc_info.value)
            assert "Test search error" in str(exc_info.value)
        
        # Test tree exploration exception
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.side_effect = Exception("Test tree error")
            
            with pytest.raises(RuntimeError) as exc_info:
                await explore_tree_structure(start_entities=["main.py"])
            
            assert "Tree exploration failed" in str(exc_info.value)
            assert "Test tree error" in str(exc_info.value)
        
        # Test graph exploration exception
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.side_effect = Exception("Test graph error")
            
            with pytest.raises(RuntimeError) as exc_info:
                await explore_graph_structure(start_entities=["main.py"])
            
            assert "Graph exploration failed" in str(exc_info.value)
            assert "Test graph error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_none_and_empty_results(self):
        """Test handling of None and empty results from LocAgent functions."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        # Test None result
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = None
            
            result = await search_code_snippets(search_terms=["test"])
            assert result == "No results found."
        
        # Test empty string result
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = ""
            
            result = await explore_tree_structure(start_entities=["main.py"])
            assert result == ""
        
        # Test None result for exploration
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = None
            
            result = await explore_graph_structure(start_entities=["main.py"])
            assert result == "No structure found."


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_repository_setup_with_minimal_args(self):
        """Test repository setup with only required arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch('mcp_server.server.set_current_issue') as mock_set_issue:
                result = await setup_repository(repo_path=str(temp_path))
                
                # Verify result contains auto-generated values
                assert "Repository initialized successfully" in result
                assert f"mcp_{temp_path.name}" in result  # Auto-generated instance_id
                assert "MCP Server Analysis" in result  # Default problem statement
                assert "HEAD" in result  # Default base commit
    
    @pytest.mark.asyncio
    async def test_large_traversal_depth(self):
        """Test exploration with very large traversal depth."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = "Deep traversal completed"
            
            result = await explore_tree_structure(
                start_entities=["main.py"],
                traversal_depth=999999
            )
            
            # Verify the large depth was passed through
            mock_explore.assert_called_once()
            call_args = mock_explore.call_args
            assert call_args[1]["traversal_depth"] == 999999
            assert "Deep traversal completed" in result
    
    @pytest.mark.asyncio 
    async def test_complex_entity_filters(self):
        """Test exploration with complex entity and dependency filters."""
        # Set up repository state
        import mcp_server.server as server_module
        server_module._repository_config = {"repo_path": "/test/path"}
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = {"filtered": "results"}
            
            entity_filter = ["class", "function", "file"]
            dependency_filter = ["imports", "invokes", "inherits"]
            
            result = await explore_graph_structure(
                start_entities=["main.py:MainClass"],
                direction="both",
                entity_type_filter=entity_filter,
                dependency_type_filter=dependency_filter
            )
            
            # Verify filters were passed correctly
            mock_explore.assert_called_once()
            call_args = mock_explore.call_args[1]
            assert call_args["entity_type_filter"] == entity_filter
            assert call_args["dependency_type_filter"] == dependency_filter
            assert "filtered" in result