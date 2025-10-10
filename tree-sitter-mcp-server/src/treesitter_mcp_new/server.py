#!/usr/bin/env python3
"""Enhanced Tree-sitter MCP Server implementation."""

import json
import base64
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator
import tree_sitter as ts
from tree_sitter_languages import get_language

from .utils.tree_sitter_helpers import (
    get_cached_language,
    parse_code,
    parse_file,
    node_to_dict,
    find_node_at_position,
    execute_query,
    detect_language
)
# TODO: Uncomment when adding back DOT/PNG/SVG support
# from .utils.graph_generator import generate_dot_graph, render_dot_to_image
from .utils.query_templates import (
    get_query_template,
    list_available_templates,
    build_combined_query
)
from .utils.code_analysis import (
    extract_symbols,
    analyze_complexity as analyze_code_complexity,
    find_dependencies,
    find_pattern_matches
)

# Initialize MCP server
mcp = FastMCP(name="treesitter-mcp-enhanced")


# Helper function for writing output files
def write_output_file(file_path: str, content: Any, format: str = "json") -> Dict[str, Any]:
    """Write content to a file in the specified format."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        
        if format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(content, str):
                    f.write(content)
                else:
                    json.dump(content, f, indent=2)
        elif format in ["png", "svg"]:
            # For binary formats, content should be base64 encoded or bytes
            if isinstance(content, str):
                # Assume it's base64 encoded
                content = base64.b64decode(content)
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(file_path, mode) as f:
                f.write(content)
        else:  # dot, txt, or other text formats
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content if isinstance(content, str) else str(content))
        
        return {
            "file_written": True,
            "file_path": os.path.abspath(file_path),
            "file_size": os.path.getsize(file_path)
        }
    except Exception as e:
        return {
            "file_written": False,
            "file_error": str(e)
        }


# Request Models
class ASTRequest(BaseModel):
    """Request model for AST generation."""
    source_code: str = Field(..., description="The source code to parse")
    language: str = Field(..., description="Programming language (e.g., 'python', 'javascript')")
    encoding: str = Field(default="utf-8", description="Source encoding")
    include_positions: bool = Field(default=True, description="Include byte/point positions")
    include_text: bool = Field(default=True, description="Include text content for nodes")
    max_depth: Optional[int] = Field(default=None, description="Maximum tree depth to return")

    @field_validator("language")
    def validate_language(cls, v):
        """Validate that the language is supported."""
        try:
            get_language(v)
            return v
        except Exception:
            raise ValueError(f"Unsupported language: {v}")


# TODO: Uncomment GraphRequest when adding back DOT/PNG/SVG support
# class GraphRequest(BaseModel):
#     """Request model for graph generation."""
#     source_code: str = Field(..., description="The source code to parse")
#     language: str = Field(..., description="Programming language")
#     format: str = Field(..., description="Output format: 'dot', 'json', 'png', 'svg'")
#     encoding: str = Field(default="utf-8", description="Source encoding")
#     max_nodes: int = Field(default=1000, description="Maximum nodes to include")
# 
#     @field_validator("language")
#     def validate_language(cls, v):
#         """Validate that the language is supported."""
#         try:
#             get_language(v)
#             return v
#         except Exception:
#             raise ValueError(f"Unsupported language: {v}")
# 
#     @field_validator("format")
#     def validate_format(cls, v):
#         """Validate the output format."""
#         allowed_formats = ["dot", "json", "png", "svg"]
#         if v not in allowed_formats:
#             raise ValueError(f"Unsupported format: {v}. Use one of: {', '.join(allowed_formats)}")
#         return v


# Tool: Generate AST
@mcp.tool()
async def generate_ast(
    source_code: str,
    language: str,
    encoding: str = "utf-8",
    include_positions: bool = True,
    include_text: bool = True,
    max_depth: Optional[int] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an Abstract Syntax Tree (AST) from source code.
    
    Args:
        source_code: The source code to parse
        language: Programming language (e.g., 'python', 'javascript', 'go', 'rust')
        encoding: Source encoding (default: 'utf-8')
        include_positions: Include byte and point positions in the AST
        include_text: Include text content for nodes
        max_depth: Maximum depth of the tree to return (None for unlimited)
        output_file: Optional path to save the AST as JSON file
    
    Returns:
        JSON representation of the syntax tree
    """
    try:
        request = ASTRequest(
            source_code=source_code,
            language=language,
            encoding=encoding,
            include_positions=include_positions,
            include_text=include_text,
            max_depth=max_depth
        )
        
        tree, source_bytes = parse_code(request.source_code, request.language, request.encoding)
        
        ast_dict = node_to_dict(
            tree.root_node,
            source_bytes,
            request.include_positions,
            request.max_depth,
            include_text=request.include_text
        )
        
        result = {
            "success": True,
            "language": request.language,
            "ast": ast_dict,
            "node_count": tree.root_node.descendant_count
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, ast_dict, "json")
            result.update(file_result)
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate AST: {str(e)}",
            "error_type": "parse_error"
        }


# Tool: Generate Graph
@mcp.tool()
async def generate_graph(
    source_code: str,
    language: str,
    format: str = "json",
    encoding: str = "utf-8",
    max_nodes: int = 1000,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a graph representation of the syntax tree.
    
    Args:
        source_code: The source code to parse
        language: Programming language (e.g., 'python', 'javascript', 'go', 'rust')
        format: Output format - currently only 'json' is supported
        encoding: Source encoding (default: 'utf-8')
        max_nodes: Maximum number of nodes to include in the graph
        output_file: Optional path to save the graph as JSON file
    
    Returns:
        Graph representation in JSON format
    """
    try:
        # TODO: Add support for DOT, PNG, and SVG formats
        # These require implementing custom graph visualization functions
        # since tree-sitter doesn't provide built-in graph generation.
        # The generate_dot_graph() and render_dot_to_image() functions
        # in utils/graph_generator.py need to be properly implemented and tested.
        
        # For now, only support JSON format
        if format != "json":
            return {
                "success": False,
                "error": f"Format '{format}' is not currently supported. Only 'json' format is available.",
                "supported_formats": ["json"]
            }
        
        # Validate language
        try:
            get_language(language)
        except Exception:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "error_type": "validation_error"
            }
        
        tree, source_bytes = parse_code(source_code, language, encoding)
        
        # Generate JSON representation
        tree_dict = node_to_dict(tree.root_node, source_bytes, include_positions=False, max_depth=None)
        
        result = {
            "success": True,
            "language": language,
            "format": "json",
            "graph": tree_dict,
            "node_count": tree.root_node.descendant_count
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, tree_dict, "json")
            result.update(file_result)
        
        return result
        
        # === COMMENTED OUT: DOT, PNG, SVG support ===
        # if request.format in ["dot", "png", "svg"]:
        #     dot_content = generate_dot_graph(tree.root_node, source_bytes, request.max_nodes)
        #     
        #     if request.format == "dot":
        #         result = {
        #             "success": True,
        #             "language": request.language,
        #             "format": "dot",
        #             "graph": dot_content,
        #             "node_count": min(tree.root_node.descendant_count, request.max_nodes)
        #         }
        #         if output_file:
        #             file_result = write_output_file(output_file, dot_content, "dot")
        #             result.update(file_result)
        #         return result
        #         
        #     elif request.format in ["png", "svg"]:
        #         try:
        #             image_data = render_dot_to_image(dot_content, request.format)
        #             encoded_image = base64.b64encode(image_data).decode('utf-8')
        #             
        #             result = {
        #                 "success": True,
        #                 "language": request.language,
        #                 "format": request.format,
        #                 "graph": encoded_image,
        #                 "graph_encoding": "base64",
        #                 "node_count": min(tree.root_node.descendant_count, request.max_nodes)
        #             }
        #             if output_file:
        #                 file_result = write_output_file(output_file, image_data, request.format)
        #                 result.update(file_result)
        #             return result
        #             
        #         except Exception as e:
        #             return {
        #                 "success": False,
        #                 "error": f"Failed to render image: {str(e)}",
        #                 "error_type": "render_error"
        #             }
        # === END COMMENTED OUT ===
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate graph: {str(e)}",
            "error_type": "graph_error"
        }


# Tool: Get Node at Position
@mcp.tool()
async def get_node_at_position(
    source_code: str,
    language: str,
    row: int,
    column: int
) -> Optional[Dict[str, Any]]:
    """
    Find the AST node at a specific position in the code.
    
    Args:
        source_code: The source code to analyze
        language: Programming language
        row: Row number (0-indexed)
        column: Column number (0-indexed)
    
    Returns:
        Information about the node at the position
    """
    try:
        tree, source_bytes = parse_code(source_code, language)
        node_info = find_node_at_position(tree.root_node, row, column, source_bytes)
        
        if node_info:
            return {
                "success": True,
                "node": node_info
            }
        else:
            return {
                "success": False,
                "error": f"No node found at position ({row}, {column})"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find node: {str(e)}"
        }


# Tool: Query Code
@mcp.tool()
async def query_code(
    source_code: str,
    language: str,
    query_pattern: str,
    encoding: str = "utf-8",
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a Tree-sitter query pattern on source code.
    
    Args:
        source_code: The source code to analyze
        language: Programming language
        query_pattern: Tree-sitter query pattern (S-expression syntax)
        encoding: Source encoding (default: 'utf-8')
        output_file: Optional path to save the results as JSON file
    
    Returns:
        List of matches with captured nodes
    """
    try:
        tree, source_bytes = parse_code(source_code, language, encoding)
        matches = execute_query(tree, query_pattern, language, source_bytes)
        
        result = {
            "success": True,
            "language": language,
            "matches": matches,
            "match_count": len(matches)
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, {"matches": matches, "query": query_pattern}, "json")
            result.update(file_result)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Query failed: {str(e)}",
            "error_type": "query_error"
        }


# Tool: Get Query Template
@mcp.tool()
async def get_query_template(
    language: str,
    template_name: str
) -> Dict[str, Any]:
    """
    Get a predefined tree-sitter query template.
    
    Args:
        language: Language name (e.g., 'python', 'javascript')
        template_name: Template name (e.g., 'functions', 'classes', 'imports')
    
    Returns:
        Query template string
    """
    template = get_query_template(language, template_name)
    
    if template:
        return {
            "success": True,
            "language": language,
            "template_name": template_name,
            "query": template
        }
    else:
        available = list_available_templates(language)
        return {
            "success": False,
            "error": f"Template '{template_name}' not found for language '{language}'",
            "available_templates": available.get(language, [])
        }


# Tool: List Query Templates
@mcp.tool()
async def list_query_templates(
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available query templates.
    
    Args:
        language: Optional language to filter by
    
    Returns:
        Available templates by language
    """
    templates = list_available_templates(language)
    
    return {
        "success": True,
        "templates": templates,
        "language_count": len(templates),
        "template_count": sum(len(t) for t in templates.values())
    }


# Tool: Build Query
@mcp.tool()
async def build_query(
    language: str,
    patterns: List[str]
) -> Dict[str, str]:
    """
    Build a tree-sitter query from multiple pattern types.
    
    Args:
        language: Language name
        patterns: List of pattern types (e.g., ['functions', 'classes'])
    
    Returns:
        Combined query string
    """
    query = build_combined_query(language, patterns)
    
    if query:
        return {
            "success": True,
            "language": language,
            "patterns": patterns,
            "query": query
        }
    else:
        return {
            "success": False,
            "error": f"Could not build query for patterns: {patterns}",
            "available_patterns": list(list_available_templates(language).get(language, []))
        }


# Tool: Extract Symbols
@mcp.tool()
async def get_symbols(
    source_file: str,
    symbol_types: Optional[List[str]] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract symbols (functions, classes, imports, etc.) from source code.
    
    Args:
        source_file: Path to the source file to analyze
        symbol_types: Types of symbols to extract (default: language-specific)
        output_file: Optional path to save the symbols as JSON file
    
    Returns:
        Dictionary of symbols by type
    """
    try:
        # Read the file
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        # Detect language from file extension
        file_ext = Path(source_file).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'c_sharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
        }
        
        language = language_map.get(file_ext, 'python')
        
        symbols = extract_symbols(source_code, language, symbol_types)
        
        result = {
            "success": True,
            "language": language,
            "symbols": symbols,
            "total_symbols": sum(len(s) for s in symbols.values())
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, symbols, "json")
            result.update(file_result)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to extract symbols: {str(e)}"
        }


# Tool: Analyze Complexity
@mcp.tool()
async def analyze_complexity(
    source_file: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze code complexity metrics.
    
    Args:
        source_file: Path to the source file to analyze
        output_file: Optional path to save the metrics as JSON file
    
    Returns:
        Complexity metrics including cyclomatic complexity
    """
    try:
        # Read the file
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        # Detect language from file extension
        file_ext = Path(source_file).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'c_sharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
        }
        
        language = language_map.get(file_ext, 'python')
        
        metrics = analyze_code_complexity(source_code, language)
        
        result = {
            "success": True,
            "language": language,
            "metrics": metrics
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, metrics, "json")
            result.update(file_result)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze complexity: {str(e)}"
        }


# Tool: Get Dependencies
@mcp.tool()
async def get_dependencies(
    source_file: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find dependencies (imports) in the source code.
    
    Args:
        source_file: Path to the source file to analyze
        output_file: Optional path to save the dependencies as JSON file
    
    Returns:
        Dictionary of dependencies
    """
    try:
        # Read the file
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        # Detect language from file extension
        file_ext = Path(source_file).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'c_sharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
        }
        
        language = language_map.get(file_ext, 'python')
        
        deps = find_dependencies(source_code, language)
        
        result = {
            "success": True,
            "language": language,
            "dependencies": deps,
            "total_imports": len(deps.get("imports", []))
        }
        
        # Write to file if requested
        if output_file:
            file_result = write_output_file(output_file, deps, "json")
            result.update(file_result)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find dependencies: {str(e)}"
        }


# Tool: Find Pattern
@mcp.tool()
async def find_pattern(
    source_code: str,
    language: str,
    pattern: str
) -> Dict[str, Any]:
    """
    Find matches for a custom tree-sitter pattern in the code.
    
    Args:
        source_code: The source code to search
        language: Programming language
        pattern: Tree-sitter query pattern
    
    Returns:
        List of pattern matches
    """
    try:
        matches = find_pattern_matches(source_code, language, pattern)
        
        if matches and len(matches) > 0 and "error" in matches[0]:
            return {
                "success": False,
                "error": matches[0]["error"]
            }
        
        return {
            "success": True,
            "language": language,
            "pattern": pattern,
            "matches": matches,
            "match_count": len(matches)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Pattern search failed: {str(e)}"
        }


# Tool: List Languages
@mcp.tool()
async def list_languages() -> Dict[str, Any]:
    """
    List all supported programming languages.
    
    Returns:
        List of supported language identifiers
    """
    try:
        # Common languages that are typically available
        languages = [
            'ada', 'apex', 'apl', 'arduino', 'astro', 'awk', 'bash', 'beancount', 'bibtex', 
            'bicep', 'blade', 'c', 'c_sharp', 'cairo', 'capnp', 'clojure', 'cmake', 
            'comment', 'commonlisp', 'cooklang', 'corn', 'cpon', 'cpp', 'css', 'csv', 
            'cuda', 'cue', 'd', 'dart', 'devicetree', 'dhall', 'diff', 'disassembly', 
            'dockerfile', 'dot', 'doxygen', 'dtd', 'earthfile', 'ebnf', 'editorconfig', 
            'eex', 'elisp', 'elixir', 'elm', 'embedded_template', 'erlang', 'facility', 
            'faust', 'fennel', 'fidl', 'firrtl', 'fish', 'forth', 'fortran', 'fsharp', 
            'func', 'fusion', 'gdscript', 'git_config', 'git_rebase', 'gitattributes', 
            'gitcommit', 'gitignore', 'glimmer', 'glsl', 'gn', 'go', 'godot_resource', 
            'gomod', 'gosum', 'gowork', 'gql', 'graphql', 'groovy', 'gstlaunch', 'hack', 
            'hare', 'haskell', 'haskell_persistent', 'hcl', 'heex', 'helm', 'hjson', 
            'hlsl', 'hlsplaylist', 'hocon', 'hoon', 'html', 'htmldjango', 'http', 'hurl', 
            'idl', 'ini', 'inko', 'ispc', 'janet_simple', 'java', 'javascript', 'jq', 
            'jsdoc', 'json', 'json5', 'jsonc', 'jsonnet', 'jsx', 'julia', 'just', 
            'kconfig', 'kdl', 'kotlin', 'kusto', 'lalrpop', 'latex', 'lean', 'ledger', 
            'leo', 'linkerscript', 'liquid', 'liquidsoap', 'llvm', 'lua', 'luadoc', 
            'luap', 'luau', 'm68k', 'make', 'markdown', 'markdown_inline', 'matlab', 
            'mermaid', 'meson', 'muttrc', 'nasm', 'nickel', 'nim', 'ninja', 'nix', 
            'norg', 'objc', 'objdump', 'ocaml', 'ocaml_interface', 'ocamllex', 'odin', 
            'org', 'pascal', 'passwd', 'pem', 'perl', 'pest', 'php', 'php_only', 'phpdoc', 
            'pioasm', 'po', 'pod', 'poe', 'pony', 'printf', 'prisma', 'promql', 'proto', 
            'prql', 'psv', 'pug', 'puppet', 'purescript', 'pyrope', 'python', 'ql', 
            'qmldir', 'qmljs', 'query', 'r', 'racket', 'rasi', 're2c', 'readline', 
            'regex', 'requirements', 'rescript', 'rnoweb', 'robot', 'robots', 'roc', 
            'ron', 'rst', 'ruby', 'rust', 'scala', 'scfg', 'scheme', 'scss', 'slang', 
            'slim', 'slint', 'smali', 'smithy', 'sml', 'solidity', 'soql', 'sosl', 
            'sourcepawn', 'sparql', 'sql', 'squirrel', 'ssh_config', 'starlark', 'strace', 
            'styled', 'supercollider', 'surface', 'svelte', 'swift', 'sxhkdrc', 'systemtap', 
            't32', 'tablegen', 'tact', 'tcl', 'teal', 'templ', 'terraform', 'textproto', 
            'thrift', 'tiger', 'tlaplus', 'tmux', 'todotxt', 'toml', 'tsv', 'tsx', 
            'turing', 'turtle', 'twig', 'typescript', 'typespec', 'typst', 'udev', 
            'ungrammar', 'unison', 'ursa', 'usd', 'uxntal', 'v', 'vala', 'verilog', 
            'vhdl', 'vim', 'vimdoc', 'vrl', 'vue', 'wgsl', 'wgsl_bevy', 'wit', 'xml', 
            'yaml', 'yang', 'yuck', 'zig', 'zsh'
        ]
        
        # Check which are actually available
        available = []
        for lang in languages:
            try:
                get_language(lang)
                available.append(lang)
            except:
                pass
        
        return {
            "success": True,
            "languages": sorted(available),
            "count": len(available)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list languages: {str(e)}",
            "error_type": "system_error"
        }




def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()