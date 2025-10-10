"""Test configuration and fixtures for LocAgent MCP Server tests."""

import asyncio
import tempfile
import textwrap
from pathlib import Path
from typing import Generator, Dict, Any
import pytest
import shutil

from mcp_server.server import LocAgentMCPServer


@pytest.fixture
def temp_repo() -> Generator[Path, None, None]:
    """Create a temporary repository with sample Python files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Create sample Python files
        (repo_path / "__init__.py").write_text("")
        
        # Main module with classes and functions
        (repo_path / "main.py").write_text(textwrap.dedent("""
            '''Main module for the test application.'''
            
            import utils
            from helpers import Helper
            
            class MainClass:
                '''Main application class.'''
                
                def __init__(self):
                    self.helper = Helper()
                
                def process_data(self, data):
                    '''Process input data.'''
                    return self.helper.transform(data)
                
                def calculate_sum(self, numbers):
                    '''Calculate sum of numbers.'''
                    return sum(numbers)
            
            def main_function():
                '''Main entry point.'''
                app = MainClass()
                result = app.process_data([1, 2, 3])
                return result
            
            if __name__ == "__main__":
                main_function()
        """))
        
        # Utils module
        (repo_path / "utils.py").write_text(textwrap.dedent("""
            '''Utility functions.'''
            
            def format_output(data):
                '''Format data for output.'''
                return f"Result: {data}"
            
            def validate_input(data):
                '''Validate input data.'''
                if not data:
                    raise ValueError("Data cannot be empty")
                return True
            
            class Logger:
                '''Simple logger class.'''
                
                def log(self, message):
                    '''Log a message.'''
                    print(f"LOG: {message}")
        """))
        
        # Helpers module
        (repo_path / "helpers.py").write_text(textwrap.dedent("""
            '''Helper classes and functions.'''
            
            from utils import Logger
            
            class Helper:
                '''Helper class for data transformation.'''
                
                def __init__(self):
                    self.logger = Logger()
                
                def transform(self, data):
                    '''Transform input data.'''
                    self.logger.log("Transforming data")
                    return [x * 2 for x in data]
                
                def validate(self, data):
                    '''Validate transformed data.'''
                    return all(isinstance(x, (int, float)) for x in data)
        """))
        
        # Subdirectory with more files
        subdir = repo_path / "submodule"
        subdir.mkdir()
        (subdir / "__init__.py").write_text("")
        
        (subdir / "advanced.py").write_text(textwrap.dedent("""
            '''Advanced functionality.'''
            
            from ..main import MainClass
            
            class AdvancedProcessor(MainClass):
                '''Advanced data processor.'''
                
                def advanced_process(self, data):
                    '''Advanced processing method.'''
                    basic_result = super().process_data(data)
                    return [x ** 2 for x in basic_result]
                
                def complex_calculation(self, matrix):
                    '''Perform complex matrix calculations.'''
                    return sum(sum(row) for row in matrix)
        """))
        
        yield repo_path


@pytest.fixture
def mcp_server() -> LocAgentMCPServer:
    """Create an MCP server instance for testing."""
    return LocAgentMCPServer()


@pytest.fixture
def sample_instance_data() -> Dict[str, Any]:
    """Sample instance data for testing."""
    return {
        "instance_id": "test_instance_001",
        "repo": "test_repo",
        "problem_statement": "Test problem for MCP server",
        "base_commit": "abc123",
        "patch": "",
    }


@pytest.fixture
def setup_repository_args(temp_repo: Path) -> Dict[str, Any]:
    """Arguments for setup_repository tool."""
    return {
        "repo_path": str(temp_repo),
        "instance_id": "test_mcp_001",
        "problem_statement": "Testing MCP server functionality",
        "base_commit": "HEAD"
    }


@pytest.fixture
def search_code_args() -> Dict[str, Any]:
    """Arguments for search_code_snippets tool."""
    return {
        "search_terms": ["MainClass", "process_data"],
        "file_path_or_pattern": "**/*.py"
    }


@pytest.fixture
def search_line_nums_args() -> Dict[str, Any]:
    """Arguments for search_code_snippets tool with line numbers."""
    return {
        "line_nums": [5, 10, 15],
        "file_path_or_pattern": "main.py"
    }


@pytest.fixture
def explore_tree_args() -> Dict[str, Any]:
    """Arguments for explore_tree_structure tool."""
    return {
        "start_entities": ["main.py:MainClass"],
        "direction": "downstream",
        "traversal_depth": 2,
        "entity_type_filter": ["class", "function"],
        "dependency_type_filter": ["invokes", "imports"]
    }


@pytest.fixture
def explore_graph_args() -> Dict[str, Any]:
    """Arguments for explore_graph_structure tool."""
    return {
        "start_entities": ["utils.py:Logger"],
        "direction": "upstream",
        "traversal_depth": 1,
        "entity_type_filter": None,
        "dependency_type_filter": None
    }