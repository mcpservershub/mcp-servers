"""Tests for individual MCP tools functionality."""

import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from mcp.types import CallToolRequest, CallToolRequestParams
from mcp_server.server import LocAgentMCPServer, RepositoryConfig


class TestSearchCodeSnippets:
    """Test cases for search_code_snippets tool."""
    
    async def test_search_with_terms(
        self, 
        mcp_server: LocAgentMCPServer, 
        search_code_args: Dict[str, Any]
    ):
        """Test search_code_snippets with search terms."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = "Found 3 code snippets matching your search..."
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments=search_code_args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with correct arguments
            mock_search.assert_called_once_with(
                search_terms=search_code_args["search_terms"],
                line_nums=None,
                file_path_or_pattern=search_code_args["file_path_or_pattern"]
            )
            
            # Verify result
            assert result.content is not None
            assert "Found 3 code snippets" in result.content[0].text
    
    async def test_search_with_line_numbers(
        self, 
        mcp_server: LocAgentMCPServer, 
        search_line_nums_args: Dict[str, Any]
    ):
        """Test search_code_snippets with line numbers."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = {
                "results": [
                    {"file": "main.py", "line": 5, "content": "class MainClass:"},
                    {"file": "main.py", "line": 10, "content": "def process_data(self, data):"}
                ]
            }
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments=search_line_nums_args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with correct arguments
            mock_search.assert_called_once_with(
                search_terms=None,
                line_nums=search_line_nums_args["line_nums"],
                file_path_or_pattern=search_line_nums_args["file_path_or_pattern"]
            )
            
            # Verify result contains JSON
            assert result.content is not None
            assert "results" in result.content[0].text
    
    async def test_search_no_arguments(self, mcp_server: LocAgentMCPServer):
        """Test search_code_snippets with no search terms or line numbers."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="search_code_snippets",
                arguments={"file_path_or_pattern": "**/*.py"}
            )
        )
        
        result = await mcp_server._call_tool(request)
        
        # Should return error about missing required arguments
        assert result.content is not None
        assert "Either search_terms or line_nums must be provided" in result.content[0].text
    
    async def test_search_function_exception(self, mcp_server: LocAgentMCPServer):
        """Test search_code_snippets when underlying function raises exception."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.side_effect = Exception("Search index not found")
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={"search_terms": ["test"]}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Should return error message
            assert result.content is not None
            assert "Search failed" in result.content[0].text
            assert "Search index not found" in result.content[0].text


class TestExploreTreeStructure:
    """Test cases for explore_tree_structure tool."""
    
    async def test_explore_tree_basic(
        self, 
        mcp_server: LocAgentMCPServer, 
        explore_tree_args: Dict[str, Any]
    ):
        """Test basic tree structure exploration."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = """
Tree Structure:
main.py:MainClass
├── process_data (method)
├── calculate_sum (method)
└── __init__ (method)
"""
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments=explore_tree_args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with correct arguments
            mock_explore.assert_called_once_with(
                start_entities=explore_tree_args["start_entities"],
                direction=explore_tree_args["direction"],
                traversal_depth=explore_tree_args["traversal_depth"],
                entity_type_filter=explore_tree_args["entity_type_filter"],
                dependency_type_filter=explore_tree_args["dependency_type_filter"]
            )
            
            # Verify result
            assert result.content is not None
            assert "Tree Structure" in result.content[0].text
            assert "main.py:MainClass" in result.content[0].text
    
    async def test_explore_tree_defaults(self, mcp_server: LocAgentMCPServer):
        """Test tree exploration with default parameters."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = "Simple tree structure"
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments={"start_entities": ["main.py"]}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with defaults
            mock_explore.assert_called_once_with(
                start_entities=["main.py"],
                direction="downstream",  # default
                traversal_depth=2,       # default
                entity_type_filter=None, # default
                dependency_type_filter=None  # default
            )
            
            # Verify result
            assert result.content is not None
            assert "Simple tree structure" in result.content[0].text
    
    async def test_explore_tree_json_result(self, mcp_server: LocAgentMCPServer):
        """Test tree exploration with JSON result."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = {
                "nodes": ["main.py:MainClass", "main.py:MainClass.process_data"],
                "edges": [{"from": "main.py:MainClass", "to": "main.py:MainClass.process_data"}]
            }
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments={"start_entities": ["main.py:MainClass"]}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify result contains JSON
            assert result.content is not None
            result_text = result.content[0].text
            assert "nodes" in result_text
            assert "edges" in result_text


class TestExploreGraphStructure:
    """Test cases for explore_graph_structure tool."""
    
    async def test_explore_graph_basic(
        self, 
        mcp_server: LocAgentMCPServer, 
        explore_graph_args: Dict[str, Any]
    ):
        """Test basic graph structure exploration."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = """
Graph Structure Analysis:
Starting from: utils.py:Logger
Upstream dependencies (depth=1):
- helpers.py:Helper.logger (invokes)
- main.py:MainClass (indirect dependency)
"""
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_graph_structure",
                    arguments=explore_graph_args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with correct arguments
            mock_explore.assert_called_once_with(
                start_entities=explore_graph_args["start_entities"],
                direction=explore_graph_args["direction"],
                traversal_depth=explore_graph_args["traversal_depth"],
                entity_type_filter=explore_graph_args["entity_type_filter"],
                dependency_type_filter=explore_graph_args["dependency_type_filter"]
            )
            
            # Verify result
            assert result.content is not None
            assert "Graph Structure Analysis" in result.content[0].text
            assert "utils.py:Logger" in result.content[0].text
    
    async def test_explore_graph_both_directions(self, mcp_server: LocAgentMCPServer):
        """Test graph exploration in both directions."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = {"bidirectional": "graph_data"}
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_graph_structure",
                    arguments={
                        "start_entities": ["main.py:MainClass"],
                        "direction": "both",
                        "traversal_depth": -1  # unlimited
                    }
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with correct arguments
            mock_explore.assert_called_once_with(
                start_entities=["main.py:MainClass"],
                direction="both",
                traversal_depth=-1,
                entity_type_filter=None,
                dependency_type_filter=None
            )
            
            # Verify result
            assert result.content is not None
            assert "bidirectional" in result.content[0].text
    
    async def test_explore_graph_with_filters(self, mcp_server: LocAgentMCPServer):
        """Test graph exploration with entity and dependency filters."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            mock_explore.return_value = "Filtered graph results"
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_graph_structure",
                    arguments={
                        "start_entities": ["main.py"],
                        "entity_type_filter": ["class", "function"],
                        "dependency_type_filter": ["imports", "invokes"]
                    }
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Verify function was called with filters
            mock_explore.assert_called_once_with(
                start_entities=["main.py"],
                direction="downstream",  # default
                traversal_depth=2,       # default
                entity_type_filter=["class", "function"],
                dependency_type_filter=["imports", "invokes"]
            )
            
            # Verify result
            assert result.content is not None
            assert "Filtered graph results" in result.content[0].text


class TestToolErrorHandling:
    """Test cases for error handling across all tools."""
    
    async def test_repository_not_setup_error(self, mcp_server: LocAgentMCPServer):
        """Test that all tools fail gracefully when repository is not set up."""
        tools_to_test = [
            ("search_code_snippets", {"search_terms": ["test"]}),
            ("explore_tree_structure", {"start_entities": ["main.py"]}),
            ("explore_graph_structure", {"start_entities": ["main.py"]})
        ]
        
        for tool_name, args in tools_to_test:
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name=tool_name,
                    arguments=args
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # All should return repository not initialized error
            assert result.content is not None
            assert "Repository not initialized" in result.content[0].text
    
    async def test_underlying_function_exceptions(self, mcp_server: LocAgentMCPServer):
        """Test handling of exceptions from underlying LocAgent functions."""
        # Set up repository
        mcp_server.repository_config = RepositoryConfig(repo_path="/test/path")
        
        tools_and_patches = [
            ("search_code_snippets", 'mcp_server.server.search_code_snippets', {"search_terms": ["test"]}),
            ("explore_tree_structure", 'mcp_server.server.explore_tree_structure', {"start_entities": ["main.py"]}),
            ("explore_graph_structure", 'mcp_server.server.explore_graph_structure', {"start_entities": ["main.py"]})
        ]
        
        for tool_name, patch_target, args in tools_and_patches:
            with patch(patch_target) as mock_func:
                mock_func.side_effect = RuntimeError(f"Test error for {tool_name}")
                
                request = CallToolRequest(
                    params=CallToolRequestParams(
                        name=tool_name,
                        arguments=args
                    )
                )
                
                result = await mcp_server._call_tool(request)
                
                # Should return formatted error message
                assert result.content is not None
                error_text = result.content[0].text
                assert "Error:" in error_text
                assert f"Test error for {tool_name}" in error_text