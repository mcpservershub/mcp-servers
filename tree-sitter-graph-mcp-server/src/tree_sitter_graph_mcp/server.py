#!/usr/bin/env python3
"""Tree-sitter Graph MCP Server implementation."""

import json
import os
import subprocess
import tempfile
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(name="tree-sitter-graph-mcp")


# Tool: Tree-sitter Graph CLI
@mcp.tool()
async def tree_sitter_graph(
    tsg_file: str,
    source_file: str,
    output_file: str,
    create_temp_files: bool = False
) -> Dict[str, Any]:
    """
    Generate a graph using the tree-sitter-graph CLI tool.
    
    This tool invokes the tree-sitter-graph command-line utility to generate
    graphs based on tree-sitter queries defined in a .tsg file.
    
    Args:
        tsg_file: Path to the .tsg file containing tree-sitter queries for graph generation
                  OR the TSG content itself if create_temp_files is True
        source_file: Path to the source code file to analyze
                     OR the source code content if create_temp_files is True
        output_file: Path where the JSON graph output will be saved
        create_temp_files: If True, tsg_file and source_file are treated as content strings
                          and temporary files will be created
    
    Returns:
        Dictionary with success status and output file path or error message
    
    Example:
        # With file paths:
        result = await tree_sitter_graph(
            tsg_file="./queries.tsg",
            source_file="./code.js",
            output_file="./graph.json"
        )
        
        # With content strings:
        result = await tree_sitter_graph(
            tsg_file="(program) @root",
            source_file="console.log('hello');",
            output_file="./graph.json",
            create_temp_files=True
        )
    """
    temp_tsg = None
    temp_source = None
    
    try:
        # Handle temporary file creation if needed
        if create_temp_files:
            # Create temporary TSG file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tsg', delete=False) as f:
                f.write(tsg_file)
                temp_tsg = f.name
                actual_tsg_file = temp_tsg
            
            # Create temporary source file
            # Try to determine extension from content or use generic
            ext = '.txt'
            if 'function' in source_file or 'const' in source_file or 'var' in source_file:
                ext = '.js'
            elif 'def ' in source_file or 'class ' in source_file or 'import ' in source_file:
                ext = '.py'
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write(source_file)
                temp_source = f.name
                actual_source_file = temp_source
        else:
            actual_tsg_file = tsg_file
            actual_source_file = source_file
        
        # Validate input files exist
        if not create_temp_files:
            if not os.path.exists(actual_tsg_file):
                return {
                    "success": False,
                    "error": f"TSG file not found: {actual_tsg_file}"
                }
            if not os.path.exists(actual_source_file):
                return {
                    "success": False,
                    "error": f"Source file not found: {actual_source_file}"
                }
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Build the command
        cmd = [
            "tree-sitter-graph",
            "--json",
            "--output", output_file,
            actual_tsg_file,
            actual_source_file
        ]
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Check if command succeeded
        if result.returncode == 0:
            # Verify output file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                
                # Try to load and validate the JSON
                try:
                    with open(output_file, 'r') as f:
                        graph_data = json.load(f)
                    
                    return {
                        "success": True,
                        "file_path": os.path.abspath(output_file),
                        "file_size": file_size,
                        "graph_nodes": len(graph_data) if isinstance(graph_data, list) else 1,
                        "command": " ".join(cmd)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "file_path": os.path.abspath(output_file),
                        "file_size": file_size,
                        "warning": "Output file created but may not be valid JSON",
                        "command": " ".join(cmd)
                    }
            else:
                return {
                    "success": False,
                    "error": "Command succeeded but output file was not created",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": " ".join(cmd)
                }
        else:
            # Command failed
            error_msg = result.stderr if result.stderr else result.stdout
            
            # Check if tree-sitter-graph is installed
            if "tree-sitter-graph: command not found" in error_msg or result.returncode == 127:
                return {
                    "success": False,
                    "error": "tree-sitter-graph CLI is not installed. Please install it first.",
                    "install_hint": "npm install -g @tree-sitter/graph or cargo install tree-sitter-graph"
                }
            
            return {
                "success": False,
                "error": f"Command failed with exit code {result.returncode}",
                "stderr": error_msg[:500] if error_msg else "No error output",
                "command": " ".join(cmd)
            }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
    finally:
        # Clean up temporary files
        if temp_tsg and os.path.exists(temp_tsg):
            try:
                os.unlink(temp_tsg)
            except:
                pass
        if temp_source and os.path.exists(temp_source):
            try:
                os.unlink(temp_source)
            except:
                pass


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()