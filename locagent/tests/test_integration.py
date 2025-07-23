"""Integration tests for LocAgent MCP Server with real LocAgent functionality."""

import pytest
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from mcp.types import CallToolRequest, CallToolRequestParams
from mcp_server.server import LocAgentMCPServer


class TestIntegrationWithMockLocAgent:
    """Integration tests using mocked LocAgent functions."""
    
    @pytest.fixture
    async def setup_server_with_repo(
        self, 
        mcp_server: LocAgentMCPServer, 
        temp_repo: Path
    ) -> LocAgentMCPServer:
        """Set up server with a test repository."""
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(
                repo_path=str(temp_repo),
                instance_id="integration_test",
                problem_statement="Integration test case"
            )
        return mcp_server
    
    async def test_full_workflow_search_and_explore(
        self, 
        setup_server_with_repo: LocAgentMCPServer
    ):
        """Test a complete workflow: search then explore."""
        server = setup_server_with_repo
        
        # Mock LocAgent functions with realistic responses
        with patch('mcp_server.server.search_code_snippets') as mock_search, \
             patch('mcp_server.server.explore_tree_structure') as mock_explore:
            
            # Mock search response
            mock_search.return_value = textwrap.dedent("""
                Search Results:
                
                1. main.py:MainClass (Lines 5-20)
                   class MainClass:
                       '''Main application class.'''
                       
                       def __init__(self):
                           self.helper = Helper()
                       
                       def process_data(self, data):
                           '''Process input data.'''
                           return self.helper.transform(data)
                
                2. main.py:main_function (Lines 25-30)
                   def main_function():
                       '''Main entry point.'''
                       app = MainClass()
                       return app.process_data([1, 2, 3])
            """)
            
            # Mock explore response
            mock_explore.return_value = textwrap.dedent("""
                Tree Structure for main.py:MainClass:
                
                main.py:MainClass
                ├── process_data (method) → invokes helper.transform
                ├── calculate_sum (method)
                └── __init__ (method) → imports Helper
                    └── helpers.py:Helper
                        ├── transform (method) → invokes Logger.log
                        └── validate (method)
                            └── utils.py:Logger
                                └── log (method)
            """)
            
            # Step 1: Search for MainClass
            search_request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={"search_terms": ["MainClass"]}
                )
            )
            
            search_result = await server._call_tool(search_request)
            
            # Verify search results
            assert search_result.content is not None
            search_text = search_result.content[0].text
            assert "Search Results" in search_text
            assert "main.py:MainClass" in search_text
            assert "process_data" in search_text
            
            # Step 2: Explore the found class structure
            explore_request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments={
                        "start_entities": ["main.py:MainClass"],
                        "direction": "downstream",
                        "traversal_depth": 3
                    }
                )
            )
            
            explore_result = await server._call_tool(explore_request)
            
            # Verify exploration results
            assert explore_result.content is not None
            explore_text = explore_result.content[0].text
            assert "Tree Structure" in explore_text
            assert "main.py:MainClass" in explore_text
            assert "helpers.py:Helper" in explore_text
            assert "utils.py:Logger" in explore_text
            
            # Verify both functions were called
            mock_search.assert_called_once()
            mock_explore.assert_called_once()
    
    async def test_search_by_line_numbers_integration(
        self, 
        setup_server_with_repo: LocAgentMCPServer
    ):
        """Test searching by line numbers integration."""
        server = setup_server_with_repo
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            # Mock response for line number search
            mock_search.return_value = {
                "search_type": "line_numbers",
                "file": "main.py",
                "results": [
                    {
                        "line_number": 5,
                        "content": "class MainClass:",
                        "context": "Class definition start"
                    },
                    {
                        "line_number": 10,
                        "content": "    def process_data(self, data):",
                        "context": "Method definition"
                    },
                    {
                        "line_number": 15,
                        "content": "        return self.helper.transform(data)",
                        "context": "Method implementation"
                    }
                ]
            }
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={
                        "line_nums": [5, 10, 15],
                        "file_path_or_pattern": "main.py"
                    }
                )
            )
            
            result = await server._call_tool(request)
            
            # Verify result
            assert result.content is not None
            result_text = result.content[0].text
            assert "line_numbers" in result_text
            assert "main.py" in result_text
            assert "class MainClass" in result_text
            assert "process_data" in result_text
            
            # Verify function call
            mock_search.assert_called_once_with(
                search_terms=None,
                line_nums=[5, 10, 15],
                file_path_or_pattern="main.py"
            )
    
    async def test_graph_exploration_integration(
        self, 
        setup_server_with_repo: LocAgentMCPServer
    ):
        """Test graph exploration integration."""
        server = setup_server_with_repo
        
        with patch('mcp_server.server.explore_graph_structure') as mock_explore:
            # Mock comprehensive graph response
            mock_explore.return_value = {
                "graph_type": "dependency_graph",
                "start_entities": ["utils.py:Logger"],
                "direction": "upstream",
                "depth": 2,
                "nodes": [
                    {
                        "id": "utils.py:Logger",
                        "type": "class",
                        "file": "utils.py"
                    },
                    {
                        "id": "helpers.py:Helper",
                        "type": "class", 
                        "file": "helpers.py"
                    },
                    {
                        "id": "main.py:MainClass",
                        "type": "class",
                        "file": "main.py"
                    }
                ],
                "edges": [
                    {
                        "from": "helpers.py:Helper",
                        "to": "utils.py:Logger",
                        "relationship": "imports",
                        "line": 3
                    },
                    {
                        "from": "main.py:MainClass",
                        "to": "helpers.py:Helper",
                        "relationship": "invokes",
                        "line": 7
                    }
                ],
                "statistics": {
                    "total_nodes": 3,
                    "total_edges": 2,
                    "max_depth_reached": 2
                }
            }
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_graph_structure",
                    arguments={
                        "start_entities": ["utils.py:Logger"],
                        "direction": "upstream",
                        "traversal_depth": 2,
                        "entity_type_filter": ["class"],
                        "dependency_type_filter": ["imports", "invokes"]
                    }
                )
            )
            
            result = await server._call_tool(request)
            
            # Verify result contains graph data
            assert result.content is not None
            result_text = result.content[0].text
            assert "dependency_graph" in result_text
            assert "utils.py:Logger" in result_text
            assert "nodes" in result_text
            assert "edges" in result_text
            assert "statistics" in result_text
            
            # Verify function call with filters
            mock_explore.assert_called_once_with(
                start_entities=["utils.py:Logger"],
                direction="upstream",
                traversal_depth=2,
                entity_type_filter=["class"],
                dependency_type_filter=["imports", "invokes"]
            )
    
    async def test_repository_reset_and_reinitialization(
        self, 
        mcp_server: LocAgentMCPServer,
        temp_repo: Path
    ):
        """Test resetting repository and reinitializing with different config."""
        # Step 1: Set up initial repository
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(
                repo_path=str(temp_repo),
                instance_id="first_setup"
            )
        
        assert mcp_server.repository_config is not None
        assert mcp_server.repository_config.instance_id == "first_setup"
        
        # Step 2: Reset repository
        with patch('mcp_server.server.reset_current_issue'):
            reset_request = CallToolRequest(
                params=CallToolRequestParams(
                    name="reset_repository",
                    arguments={}
                )
            )
            
            reset_result = await mcp_server._call_tool(reset_request)
            
            assert reset_result.content is not None
            assert "reset" in reset_result.content[0].text
            assert mcp_server.repository_config is None
        
        # Step 3: Set up new repository configuration
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(
                repo_path=str(temp_repo),
                instance_id="second_setup",
                problem_statement="Different problem"
            )
        
        assert mcp_server.repository_config is not None
        assert mcp_server.repository_config.instance_id == "second_setup"
        assert mcp_server.repository_config.problem_statement == "Different problem"
    
    async def test_error_recovery_and_continuation(
        self, 
        setup_server_with_repo: LocAgentMCPServer
    ):
        """Test that server can recover from errors and continue operating."""
        server = setup_server_with_repo
        
        # Step 1: Cause an error in search
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.side_effect = Exception("Temporary search failure")
            
            error_request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={"search_terms": ["test"]}
                )
            )
            
            error_result = await server._call_tool(error_request)
            
            # Should get error response
            assert error_result.content is not None
            assert "Search failed" in error_result.content[0].text
            assert "Temporary search failure" in error_result.content[0].text
        
        # Step 2: Verify server can still handle successful requests
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = "Successful exploration after error"
            
            success_request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments={"start_entities": ["main.py"]}
                )
            )
            
            success_result = await server._call_tool(success_request)
            
            # Should get successful response
            assert success_result.content is not None
            assert "Successful exploration after error" in success_result.content[0].text
            
            # Verify repository config is still intact
            assert server.repository_config is not None
            assert server.repository_config.instance_id == "integration_test"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_empty_search_results(self, mcp_server: LocAgentMCPServer, temp_repo: Path):
        """Test handling of empty search results."""
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(repo_path=str(temp_repo))
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = ""  # Empty result
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={"search_terms": ["nonexistent"]}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Should handle empty result gracefully
            assert result.content is not None
            # Empty string should be handled properly
            assert len(result.content[0].text) == 0 or "No results found" in result.content[0].text
    
    async def test_none_search_results(self, mcp_server: LocAgentMCPServer, temp_repo: Path):
        """Test handling of None search results."""
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(repo_path=str(temp_repo))
        
        with patch('mcp_server.server.search_code_snippets') as mock_search:
            mock_search.return_value = None  # None result
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="search_code_snippets",
                    arguments={"search_terms": ["test"]}
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Should handle None result gracefully
            assert result.content is not None
            assert "No results found" in result.content[0].text
    
    async def test_large_traversal_depth(self, mcp_server: LocAgentMCPServer, temp_repo: Path):
        """Test handling of very large traversal depths."""
        with patch('mcp_server.server.set_current_issue'):
            await mcp_server._setup_repository(repo_path=str(temp_repo))
        
        with patch('mcp_server.server.explore_tree_structure') as mock_explore:
            mock_explore.return_value = "Deep traversal completed successfully"
            
            request = CallToolRequest(
                params=CallToolRequestParams(
                    name="explore_tree_structure",
                    arguments={
                        "start_entities": ["main.py"],
                        "traversal_depth": 999999  # Very large depth
                    }
                )
            )
            
            result = await mcp_server._call_tool(request)
            
            # Should handle large depth values
            assert result.content is not None
            assert "Deep traversal completed" in result.content[0].text
            
            # Verify the large depth was passed through
            mock_explore.assert_called_once()
            call_args = mock_explore.call_args[1]
            assert call_args["traversal_depth"] == 999999