"""
LocAgent MCP Server Implementation using FastMCP

This module provides a Model Context Protocol (MCP) server that exposes
LocAgent's code localization tools for use by LLM clients.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Add the parent directory to sys.path to import LocAgent modules
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Set up LocAgent required environment variables if not already set
if not os.environ.get("GRAPH_INDEX_DIR"):
    os.environ["GRAPH_INDEX_DIR"] = str(parent_dir / "graph_index")
if not os.environ.get("BM25_INDEX_DIR"):
    os.environ["BM25_INDEX_DIR"] = str(parent_dir / "bm25_index")

# Create index directories if they don't exist
os.makedirs(os.environ["GRAPH_INDEX_DIR"], exist_ok=True)
os.makedirs(os.environ["BM25_INDEX_DIR"], exist_ok=True)

# Log environment setup to stderr to avoid interfering with MCP protocol
import sys
print(f"LocAgent MCP Server Environment:", file=sys.stderr)
print(f"  GRAPH_INDEX_DIR: {os.environ['GRAPH_INDEX_DIR']}", file=sys.stderr)
print(f"  BM25_INDEX_DIR: {os.environ['BM25_INDEX_DIR']}", file=sys.stderr)

try:
    # Import LocAgent modules
    from plugins.location_tools.repo_ops.repo_ops import (
        set_current_issue,
        reset_current_issue,
        search_code_snippets as _search_code_snippets,
        explore_tree_structure as _explore_tree_structure,
        explore_graph_structure as _explore_graph_structure,
    )
    # Import additional modules for local repo support
    import pickle
    import uuid
    import os
    from dependency_graph.build_graph import build_graph
    from dependency_graph import RepoEntitySearcher, RepoDependencySearcher
    from plugins.location_tools.utils.util import GRAPH_INDEX_DIR
    import plugins.location_tools.repo_ops.repo_ops as repo_ops_module
except ImportError as e:
    logging.error(f"Failed to import LocAgent modules: {e}")
    raise


logger = logging.getLogger(__name__)

# Create FastMCP app
app = FastMCP("LocAgent MCP Server")

# Global state for repository configuration
_repository_config: Optional[Dict[str, Any]] = None


class RepositorySetupRequest(BaseModel):
    """Request model for repository setup."""
    repo_path: str = Field(..., description="Path to the repository to analyze")
    instance_id: Optional[str] = Field(None, description="Instance ID for the analysis")
    problem_statement: Optional[str] = Field(None, description="Problem description")
    base_commit: Optional[str] = Field(None, description="Base commit hash")


class SearchRequest(BaseModel):
    """Request model for code search."""
    search_terms: Optional[List[str]] = Field(None, description="Keywords to search for")
    line_nums: Optional[List[int]] = Field(None, description="Line numbers to examine")
    file_path_or_pattern: str = Field("**/*.py", description="File pattern to filter results")


class ExploreRequest(BaseModel):
    """Request model for structure exploration."""
    start_entities: List[str] = Field(..., description="Entities to start exploration from")
    direction: str = Field("downstream", description="Direction of traversal")
    traversal_depth: int = Field(2, description="Maximum depth of traversal")
    entity_type_filter: Optional[List[str]] = Field(None, description="Filter by entity types")
    dependency_type_filter: Optional[List[str]] = Field(None, description="Filter by dependency types")


def _setup_local_repository(instance_data: dict, local_repo_path: str, rank: int = 0) -> None:
    """Setup a local repository for analysis without cloning."""
    # Set global variables directly in the repo_ops module
    repo_ops_module.CURRENT_ISSUE_ID = instance_data['instance_id']
    repo_ops_module.CURRENT_INSTANCE = instance_data
    
    # For local repos, we don't need a temporary playground directory
    # We'll work directly with the local repository
    repo_ops_module.REPO_SAVE_DIR = local_repo_path
    
    # Setup graph traverser
    graph_index_file = f"{GRAPH_INDEX_DIR}/{instance_data['instance_id']}.pkl"
    G = None  # Initialize G variable
    
    if not os.path.exists(graph_index_file):
        # Build graph directly from local repository
        try:
            os.makedirs(GRAPH_INDEX_DIR, exist_ok=True)
            G = build_graph(local_repo_path, global_import=True)
            with open(graph_index_file, 'wb') as f:
                pickle.dump(G, f)
            logging.info(f'[{rank}] Processed local repo {instance_data["instance_id"]}')
        except Exception as e:
            logging.error(f'[{rank}] Error processing local repo {instance_data["instance_id"]}: {e}')
            raise
    else:
        try:
            with open(graph_index_file, 'rb') as f:
                G = pickle.load(f)
            logging.info(f'[{rank}] Loaded cached graph for {instance_data["instance_id"]}')
        except Exception as e:
            logging.error(f'[{rank}] Error loading cached graph for {instance_data["instance_id"]}: {e}')
            raise
    
    # Ensure G is properly loaded
    if G is None:
        raise RuntimeError(f"Failed to load or build graph for repository {local_repo_path}")
    
    # Set up global searchers
    repo_ops_module.DP_GRAPH_ENTITY_SEARCHER = RepoEntitySearcher(G)
    repo_ops_module.DP_GRAPH_DEPENDENCY_SEARCHER = RepoDependencySearcher(G)
    repo_ops_module.DP_GRAPH = G
    
    # Set up node lists
    from dependency_graph.build_graph import NODE_TYPE_FILE, NODE_TYPE_CLASS, NODE_TYPE_FUNCTION
    repo_ops_module.ALL_FILE = repo_ops_module.DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_FILE)
    repo_ops_module.ALL_CLASS = repo_ops_module.DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_CLASS)
    repo_ops_module.ALL_FUNC = repo_ops_module.DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_FUNCTION)
    
    logging.debug(f'Rank = {rank}, set CURRENT_ISSUE_ID = {instance_data["instance_id"]} for local repo')


def _check_repository_setup() -> None:
    """Check if repository is properly set up."""
    if _repository_config is None:
        raise RuntimeError(
            "Repository not initialized. Please call setup_repository first."
        )


@app.tool()
async def setup_repository(
    repo_path: str,
    instance_id: Optional[str] = None,
    problem_statement: Optional[str] = None,
    base_commit: Optional[str] = None
) -> str:
    """Initialize repository for analysis. Must be called before using other tools.
    
    Args:
        repo_path: Path to local repository OR GitHub URL (e.g., https://github.com/user/repo)
        instance_id: Optional instance ID for the analysis
        problem_statement: Optional problem description
        base_commit: Optional base commit hash
        
    Returns:
        Success message with repository details
        
    Raises:
        ValueError: If repository path does not exist or URL is invalid
        RuntimeError: If setup fails
    """
    global _repository_config
    
    try:
        # Determine if this is a GitHub URL or local path
        is_github_url = repo_path.startswith(('https://github.com/', 'git@github.com:'))
        logger.info(f"Repository path: {repo_path}, is_github_url: {is_github_url}")
        
        if is_github_url:
            # Handle GitHub URL
            if repo_path.startswith('https://github.com/'):
                # Extract repo name from URL (e.g., "user/repo" from "https://github.com/user/repo")
                repo_name = repo_path.replace('https://github.com/', '').replace('.git', '')
                if repo_name.endswith('/'):
                    repo_name = repo_name[:-1]
            else:
                # Handle git@github.com:user/repo.git format
                repo_name = repo_path.replace('git@github.com:', '').replace('.git', '')
            
            # Create instance data for LocAgent (GitHub repository)
            instance_data = {
                "instance_id": instance_id or f"mcp_{repo_name.replace('/', '_')}",
                "repo": repo_name,
                "problem_statement": problem_statement or "MCP Server Analysis",
                "base_commit": base_commit or "HEAD",
                "patch": "",
            }
            
            logger.info(f"Setting up GitHub repository: {repo_name}")
            
        else:
            # Handle local filesystem path
            repo_path_obj = Path(repo_path)
            if not repo_path_obj.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            if not repo_path_obj.is_dir():
                raise ValueError(f"Repository path is not a directory: {repo_path}")
            
            # Check if it's a git repository
            git_dir = repo_path_obj / '.git'
            if not git_dir.exists():
                raise ValueError(f"Directory is not a git repository: {repo_path}")
            
            # Create instance data for LocAgent (local repository)
            instance_data = {
                "instance_id": instance_id or f"mcp_{repo_path_obj.name}",
                "repo": str(repo_path_obj.absolute()),  # Use absolute path for local repos
                "problem_statement": problem_statement or "MCP Server Analysis",
                "base_commit": base_commit or "HEAD",
                "patch": "",
            }
            
            logger.info(f"Setting up local repository: {repo_path_obj.absolute()}")
        
        # Set up LocAgent repository context
        if is_github_url:
            # Use the standard LocAgent setup for GitHub repositories
            logger.info(f"Using standard LocAgent setup for GitHub repo: {repo_name}")
            set_current_issue(instance_data=instance_data, rank=0)
        else:
            # Use our custom setup for local repositories
            logger.info(f"Using custom setup for local repo: {repo_path}")
            _setup_local_repository(instance_data, repo_path, rank=0)
        
        # Store configuration
        _repository_config = {
            "repo_path": repo_path,
            "instance_id": instance_data["instance_id"],
            "problem_statement": problem_statement,
            "base_commit": base_commit,
            "is_github_url": is_github_url
        }
        
        result_text = f"Repository initialized successfully!\n\n" \
                     f"Repository: {repo_path}\n" \
                     f"Type: {'GitHub URL' if is_github_url else 'Local Path'}\n" \
                     f"Instance ID: {instance_data['instance_id']}\n" \
                     f"Problem Statement: {problem_statement or 'Not provided'}\n" \
                     f"Base Commit: {base_commit or 'HEAD'}\n\n" \
                     f"You can now use the other tools to analyze the codebase."
        
        return result_text
        
    except Exception as e:
        raise RuntimeError(f"Failed to setup repository: {str(e)}")


@app.tool()
async def reset_repository() -> str:
    """Reset the current repository context. Useful for switching to a different repository.
    
    Returns:
        Success message confirming reset
    """
    global _repository_config
    
    try:
        reset_current_issue()
        _repository_config = None
        
        return "Repository context has been reset. Use setup_repository to initialize a new repository."
        
    except Exception as e:
        raise RuntimeError(f"Failed to reset repository: {str(e)}")


@app.tool()
async def search_code_snippets(
    search_terms: Optional[List[str]] = None,
    line_nums: Optional[List[int]] = None,
    file_path_or_pattern: str = "**/*.py"
) -> str:
    """Search codebase for relevant code snippets based on terms or line numbers.
    
    Args:
        search_terms: List of keywords, function names, class names to search for
        line_nums: Specific line numbers to locate code snippets within a file
        file_path_or_pattern: Glob pattern or specific file path to filter results
        
    Returns:
        Search results as formatted text or JSON
        
    Raises:
        ValueError: If neither search_terms nor line_nums are provided
        RuntimeError: If repository is not initialized or search fails
    """
    _check_repository_setup()
    
    try:
        # Validate inputs
        if not search_terms and not line_nums:
            raise ValueError("Either search_terms or line_nums must be provided")
        
        # Call LocAgent function
        result = _search_code_snippets(
            search_terms=search_terms,
            line_nums=line_nums,
            file_path_or_pattern=file_path_or_pattern
        )
        
        # Format result
        if isinstance(result, str):
            return result
        elif result is not None:
            return json.dumps(result, indent=2)
        else:
            return "No results found."
            
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}")


@app.tool()
async def explore_tree_structure(
    start_entities: List[str],
    direction: str = "downstream",
    traversal_depth: int = 2,
    entity_type_filter: Optional[List[str]] = None,
    dependency_type_filter: Optional[List[str]] = None
) -> str:
    """Analyze code dependencies and relationships in tree format.
    
    Useful for understanding code structure and dependencies.
    
    Args:
        start_entities: List of entities to start exploration from.
                       Format: 'file_path:QualifiedName' for functions/classes,
                       or just 'file_path' for files, or 'dir_path' for directories
        direction: Direction of traversal: 'upstream' (dependencies), 
                  'downstream' (dependents), or 'both'
        traversal_depth: Maximum depth of traversal (-1 for unlimited)
        entity_type_filter: Filter by entity types: 'class', 'function', 'file', 'directory'
        dependency_type_filter: Filter by dependency types: 'contains', 'imports', 'invokes', 'inherits'
        
    Returns:
        Tree structure analysis as formatted text or JSON
        
    Raises:
        RuntimeError: If repository is not initialized or exploration fails
    """
    _check_repository_setup()
    
    try:
        # Call LocAgent function
        result = _explore_tree_structure(
            start_entities=start_entities,
            direction=direction,
            traversal_depth=traversal_depth,
            entity_type_filter=entity_type_filter,
            dependency_type_filter=dependency_type_filter
        )
        
        # Format result
        if isinstance(result, str):
            return result
        elif result is not None:
            return json.dumps(result, indent=2)
        else:
            return "No structure found."
            
    except Exception as e:
        raise RuntimeError(f"Tree exploration failed: {str(e)}")


@app.tool()
async def explore_graph_structure(
    start_entities: List[str],
    direction: str = "downstream",
    traversal_depth: int = 2,
    entity_type_filter: Optional[List[str]] = None,
    dependency_type_filter: Optional[List[str]] = None
) -> str:
    """Analyze code dependencies and relationships in graph format.
    
    Similar to tree structure but provides graph-based output with additional relationship details.
    
    Args:
        start_entities: List of entities to start exploration from
        direction: Direction of traversal: 'upstream', 'downstream', or 'both'
        traversal_depth: Maximum depth of traversal (-1 for unlimited)
        entity_type_filter: Filter by entity types
        dependency_type_filter: Filter by dependency types
        
    Returns:
        Graph structure analysis as formatted text or JSON
        
    Raises:
        RuntimeError: If repository is not initialized or exploration fails
    """
    _check_repository_setup()
    
    try:
        # Call LocAgent function
        result = _explore_graph_structure(
            start_entities=start_entities,
            direction=direction,
            traversal_depth=traversal_depth,
            entity_type_filter=entity_type_filter,
            dependency_type_filter=dependency_type_filter
        )
        
        # Format result
        if isinstance(result, str):
            return result
        elif result is not None:
            return json.dumps(result, indent=2)
        else:
            return "No structure found."
            
    except Exception as e:
        raise RuntimeError(f"Graph exploration failed: {str(e)}")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


if __name__ == "__main__":
    # Run the server with stdio transport
    app.run(transport="stdio")