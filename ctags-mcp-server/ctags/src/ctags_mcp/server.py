#!/usr/bin/env python3
"""Universal CTags MCP Server implementation."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from .utils import CTagsWrapper, validate_path
from .utils.validators import validate_tags_file as validate_tags_file_util
from .models import GenerateTagsRequest, SearchRequest, OperationResult
# Note: TagEntry from models is not used - we need ctags.TagEntry for validate_tags_file tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(name="universal-ctags-mcp")

# Initialize CTags wrapper
ctags_wrapper = CTagsWrapper(os.environ.get("CTAGS_BINARY", "ctags"))


# ============== Indexing Tools ==============

@mcp.tool()
async def generate_tags(
    path: str,
    recursive: bool = True,
    languages: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    output_file: str = "tags",
    output_format: str = "u-ctags",
    extra_options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate CTags index for a project or directory.

    This tool generates a tags file by indexing source code in the specified
    path using Universal CTags. The tags file can then be used for symbol
    navigation and search operations.

    Args:
        path: Directory or file path to index
        recursive: Recursively index subdirectories (default: True)
        languages: Specific languages to index (e.g., ["python", "javascript"])
        exclude_patterns: Patterns to exclude from indexing (e.g., ["*.min.js", "node_modules"])
        output_file: Output tags file path (default: "tags")
        output_format: Output format - "u-ctags", "e-ctags", "etags", "xref", "json" (default: "u-ctags")
        extra_options: Additional ctags command-line options

    Returns:
        Dictionary with generation status, tags file path, and statistics

    Example:
        result = await generate_tags(
            path="./src",
            recursive=True,
            languages=["python", "javascript"],
            exclude_patterns=["*.test.js", "__pycache__"],
            output_file="./project.tags",
            output_format="json"
        )
    """
    # Validate input path
    is_valid, error = validate_path(path)
    if not is_valid:
        return {"success": False, "error": error}

    try:
        result = ctags_wrapper.generate_tags(
            path=path,
            output_file=output_file,
            recursive=recursive,
            languages=languages,
            exclude_patterns=exclude_patterns,
            output_format=output_format,
            extra_options=extra_options
        )
        return result
    except Exception as e:
        logger.error(f"Failed to generate tags: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_tags(
    tags_file: str,
    modified_files: List[str]
) -> Dict[str, Any]:
    """
    Update tags file with changes in specific files.
    
    This tool performs an incremental update of an existing tags file
    by re-indexing only the specified modified files.
    
    Args:
        tags_file: Path to existing tags file
        modified_files: List of modified files to re-index
    
    Returns:
        Dictionary with update status and statistics
    
    Example:
        result = await update_tags(
            tags_file="./tags",
            modified_files=["src/main.py", "src/utils.py"]
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}
    
    # Validate modified files
    valid_files = []
    for file_path in modified_files:
        is_valid, _ = validate_path(file_path)
        if is_valid:
            valid_files.append(file_path)
    
    if not valid_files:
        return {"success": False, "error": "No valid files to update"}
    
    try:
        # For incremental update, we append to existing tags
        result = ctags_wrapper.generate_tags(
            path=" ".join(valid_files),
            output_file=tags_file,
            recursive=False,
            extra_options=["--append"]
        )
        
        result["updated_files"] = valid_files
        return result
    except Exception as e:
        logger.error(f"Failed to update tags: {e}")
        return {"success": False, "error": str(e)}


# ============== Search Tools ==============

@mcp.tool()
async def find_symbol(
    symbol_name: str,
    tags_file: str = "tags",
    match_type: str = "exact",
    case_sensitive: bool = True,
    symbol_kinds: Optional[List[str]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for symbols in the tags file.
    
    This tool searches for symbols (functions, classes, variables, etc.)
    in the tags file with various matching options.
    
    Args:
        symbol_name: Symbol name or pattern to search
        tags_file: Path to tags file (default: "tags")
        match_type: Type of matching - "exact", "partial", or "regex"
        case_sensitive: Case-sensitive matching (default: True)
        symbol_kinds: Filter by symbol types (e.g., ["function", "class"])
        limit: Maximum results to return (default: 50)
    
    Returns:
        List of matching symbols with their details
    
    Example:
        symbols = await find_symbol(
            symbol_name="handle",
            tags_file="./tags",
            match_type="partial",
            case_sensitive=False,
            limit=20
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return []
    
    try:
        results = ctags_wrapper.find_symbol(
            tags_file=tags_file,
            symbol_name=symbol_name,
            match_type=match_type,
            case_sensitive=case_sensitive,
            limit=limit
        )
        
        # Filter by symbol kinds if specified
        if symbol_kinds and results:
            results = [r for r in results if r.get('kind') in symbol_kinds]
        
        return results
    except Exception as e:
        logger.error(f"Failed to find symbol: {e}")
        return []


@mcp.tool()
async def find_references(
    symbol_name: str,
    scope_file: Optional[str] = None,
    tags_file: str = "tags"
) -> List[Dict[str, Any]]:
    """
    Find all references to a symbol across the codebase.
    
    This tool finds all occurrences and references to a specific symbol
    in the indexed codebase.
    
    Args:
        symbol_name: Symbol to find references for
        scope_file: Limit search to specific file (optional)
        tags_file: Path to tags file (default: "tags")
    
    Returns:
        List of references with context information
    
    Example:
        refs = await find_references(
            symbol_name="DatabaseConnection",
            tags_file="./tags"
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return []
    
    try:
        # Find all matches for the symbol
        results = ctags_wrapper.find_symbol(
            tags_file=tags_file,
            symbol_name=symbol_name,
            match_type="exact",
            case_sensitive=True,
            limit=1000  # Higher limit for references
        )
        
        # Filter by scope file if specified
        if scope_file and results:
            scope_file = os.path.abspath(scope_file)
            results = [r for r in results if os.path.abspath(r.get('file', '')) == scope_file]
        
        return results
    except Exception as e:
        logger.error(f"Failed to find references: {e}")
        return []


# ============== Navigation Tools ==============

@mcp.tool()
async def go_to_definition(
    symbol_name: str,
    current_file: Optional[str] = None,
    tags_file: str = "tags"
) -> Dict[str, Any]:
    """
    Find the definition location of a symbol.
    
    This tool locates the definition of a symbol, useful for code navigation
    and understanding where symbols are defined.
    
    Args:
        symbol_name: Symbol to find definition for
        current_file: Current file context for scoped search (optional)
        tags_file: Path to tags file (default: "tags")
    
    Returns:
        Dictionary with definition location and symbol details
    
    Example:
        definition = await go_to_definition(
            symbol_name="MyClass",
            current_file="./src/main.py",
            tags_file="./tags"
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}
    
    try:
        # Search for exact match first
        results = ctags_wrapper.find_symbol(
            tags_file=tags_file,
            symbol_name=symbol_name,
            match_type="exact",
            case_sensitive=True,
            limit=10
        )
        
        if not results:
            return {
                "success": False,
                "error": f"Symbol '{symbol_name}' not found"
            }
        
        # If current_file is specified, prioritize definitions in that file
        if current_file:
            current_file = os.path.abspath(current_file)
            for result in results:
                if os.path.abspath(result.get('file', '')) == current_file:
                    return {
                        "success": True,
                        "definition": result,
                        "message": "Definition found in current file"
                    }
        
        # Return the first (most likely) definition
        return {
            "success": True,
            "definition": results[0],
            "alternatives": results[1:] if len(results) > 1 else []
        }
    except Exception as e:
        logger.error(f"Failed to find definition: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_symbols_in_file(
    file_path: str,
    tags_file: str = "tags",
    group_by_kind: bool = True
) -> Dict[str, Any]:
    """
    List all symbols defined in a specific file.
    
    This tool extracts all symbols (functions, classes, variables, etc.)
    defined in a specific source file.
    
    Args:
        file_path: Path to the source file
        tags_file: Path to tags file (default: "tags")
        group_by_kind: Group symbols by their kind (default: True)
    
    Returns:
        Dictionary with symbols organized by type or as flat list
    
    Example:
        symbols = await list_symbols_in_file(
            file_path="./src/main.py",
            tags_file="./tags",
            group_by_kind=True
        )
    """
    # Validate inputs
    is_valid, error = validate_path(file_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}
    
    try:
        symbols = ctags_wrapper.get_symbols_in_file(
            tags_file=tags_file,
            file_path=file_path
        )
        
        if group_by_kind:
            grouped = {}
            for symbol in symbols:
                kind = symbol.get('kind', 'unknown')
                if kind not in grouped:
                    grouped[kind] = []
                grouped[kind].append(symbol)
            
            return {
                "success": True,
                "file": os.path.abspath(file_path),
                "symbols": grouped,
                "total_count": len(symbols)
            }
        else:
            return {
                "success": True,
                "file": os.path.abspath(file_path),
                "symbols": symbols,
                "total_count": len(symbols)
            }
    except Exception as e:
        logger.error(f"Failed to list symbols: {e}")
        return {"success": False, "error": str(e)}


# ============== Analysis Tools ==============

@mcp.tool()
async def get_file_outline(
    file_path: str,
    tags_file: str = "tags",
    include_private: bool = False,
    max_depth: int = 3
) -> Dict[str, Any]:
    """
    Generate a structured outline of symbols in a file.
    
    This tool creates a hierarchical outline of a file's structure,
    showing classes, methods, functions, and other symbols in an
    organized tree format.
    
    Args:
        file_path: Path to the source file
        tags_file: Path to tags file (default: "tags")
        include_private: Include private symbols (default: False)
        max_depth: Maximum nesting depth (default: 3)
    
    Returns:
        Dictionary with hierarchical structure of file symbols
    
    Example:
        outline = await get_file_outline(
            file_path="./src/main.py",
            tags_file="./tags",
            include_private=True
        )
    """
    # Validate inputs
    is_valid, error = validate_path(file_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}
    
    try:
        symbols = ctags_wrapper.get_symbols_in_file(
            tags_file=tags_file,
            file_path=file_path
        )
        
        # Filter private symbols if needed
        if not include_private:
            symbols = [s for s in symbols if not s['name'].startswith('_')]
        
        # Build hierarchical structure
        outline = {
            "file": os.path.abspath(file_path),
            "classes": [],
            "functions": [],
            "variables": [],
            "other": []
        }
        
        for symbol in symbols:
            kind = symbol.get('kind', '').lower()
            
            if 'class' in kind:
                outline['classes'].append(symbol)
            elif 'function' in kind or 'method' in kind:
                outline['functions'].append(symbol)
            elif 'variable' in kind or 'member' in kind:
                outline['variables'].append(symbol)
            else:
                outline['other'].append(symbol)
        
        # Sort by line number
        for category in outline:
            if isinstance(outline[category], list):
                outline[category].sort(key=lambda x: x.get('line', 0))
        
        return {
            "success": True,
            "outline": outline,
            "symbol_count": len(symbols)
        }
    except Exception as e:
        logger.error(f"Failed to generate outline: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_project_symbols(
    tags_file: str = "tags",
    group_by: str = "kind",
    languages: Optional[List[str]] = None,
    symbol_kinds: Optional[List[str]] = None,
    include_private: bool = True
) -> Dict[str, Any]:
    """
    Extract all symbols from a project-wide tags file.

    This tool generates a comprehensive list of all symbols across the entire
    project by reading from an existing tags file. Symbols can be grouped by
    various criteria for better organization.

    Args:
        tags_file: Path to tags file (default: "tags")
        group_by: How to group symbols - "kind", "file", "language", or "none" (default: "kind")
        languages: Filter by specific languages (optional)
        symbol_kinds: Filter by symbol types (e.g., ["function", "class"]) (optional)
        include_private: Include private symbols (default: True)

    Returns:
        Dictionary with symbols organized according to group_by parameter

    Example:
        symbols = await generate_project_symbols(
            tags_file="./tags",
            group_by="kind",
            symbol_kinds=["function", "class"],
            include_private=False
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}

    try:
        # Get all symbols from tags file
        all_symbols = ctags_wrapper.get_all_symbols_from_tags(tags_file)

        if not all_symbols:
            return {
                "success": True,
                "symbols": {},
                "total_count": 0,
                "message": "No symbols found in tags file"
            }

        # Filter private symbols if needed
        if not include_private:
            all_symbols = [s for s in all_symbols if not s['name'].startswith('_')]

        # Filter by symbol kinds if specified
        if symbol_kinds:
            all_symbols = [s for s in all_symbols if s.get('kind') in symbol_kinds]

        # Filter by languages if specified (approximate by file extension)
        if languages:
            # Map common extensions to languages
            lang_extensions = {
                'python': ['.py', '.pyw'],
                'javascript': ['.js', '.jsx', '.mjs'],
                'typescript': ['.ts', '.tsx'],
                'java': ['.java'],
                'c': ['.c', '.h'],
                'cpp': ['.cpp', '.hpp', '.cc', '.cxx', '.C', '.hh'],
                'go': ['.go'],
                'rust': ['.rs'],
                'ruby': ['.rb'],
                'php': ['.php'],
                'cobol': ['.cbl', '.cob', '.cpy']
            }

            allowed_extensions = []
            for lang in languages:
                lang_lower = lang.lower()
                if lang_lower in lang_extensions:
                    allowed_extensions.extend(lang_extensions[lang_lower])

            if allowed_extensions:
                all_symbols = [
                    s for s in all_symbols
                    if any(s.get('file', '').endswith(ext) for ext in allowed_extensions)
                ]

        # Group symbols based on group_by parameter
        result = {
            "success": True,
            "total_count": len(all_symbols),
            "group_by": group_by
        }

        if group_by == "kind":
            grouped = {}
            for symbol in all_symbols:
                kind = symbol.get('kind', 'unknown')
                if kind not in grouped:
                    grouped[kind] = []
                grouped[kind].append(symbol)
            result["symbols"] = grouped

        elif group_by == "file":
            grouped = {}
            for symbol in all_symbols:
                file_path = symbol.get('file', 'unknown')
                if file_path not in grouped:
                    grouped[file_path] = []
                grouped[file_path].append(symbol)
            result["symbols"] = grouped

        elif group_by == "language":
            # Group by file extension as proxy for language
            grouped = {}
            for symbol in all_symbols:
                file_path = symbol.get('file', '')
                ext = os.path.splitext(file_path)[1] or 'no_extension'
                if ext not in grouped:
                    grouped[ext] = []
                grouped[ext].append(symbol)
            result["symbols"] = grouped

        else:  # group_by == "none"
            result["symbols"] = all_symbols

        return result

    except Exception as e:
        logger.error(f"Failed to generate project symbols: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_project_outline(
    tags_file: str = "tags",
    max_depth: int = 3,
    include_private: bool = False,
    show_line_numbers: bool = True
) -> Dict[str, Any]:
    """
    Generate a hierarchical outline of the entire project structure.

    This tool creates a comprehensive, hierarchical view of the project's
    code structure by analyzing all symbols in the tags file, organized
    by files and symbol types.

    Args:
        tags_file: Path to tags file (default: "tags")
        max_depth: Maximum nesting depth for hierarchy (default: 3)
        include_private: Include private symbols (default: False)
        show_line_numbers: Include line numbers in outline (default: True)

    Returns:
        Dictionary with hierarchical project structure

    Example:
        outline = await generate_project_outline(
            tags_file="./tags",
            max_depth=2,
            include_private=False
        )
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}

    try:
        # Get all files referenced in tags
        all_files = ctags_wrapper.get_all_files_from_tags(tags_file)

        if not all_files:
            return {
                "success": True,
                "outline": {},
                "file_count": 0,
                "message": "No files found in tags file"
            }

        # Build outline for each file
        project_outline = {}
        total_symbols = 0

        for file_path in all_files:
            # Get symbols for this file
            symbols = ctags_wrapper.get_symbols_in_file(tags_file, file_path)

            # Filter private symbols if needed
            if not include_private:
                symbols = [s for s in symbols if not s['name'].startswith('_')]

            if not symbols:
                continue

            # Organize symbols by kind
            file_structure = {
                "path": os.path.abspath(file_path),
                "classes": [],
                "functions": [],
                "variables": [],
                "other": []
            }

            for symbol in symbols:
                kind = symbol.get('kind', '').lower()

                # Prepare symbol info
                symbol_info = {
                    "name": symbol['name'],
                    "kind": symbol.get('kind')
                }

                if show_line_numbers:
                    symbol_info["line"] = symbol.get('line', 0)

                # Categorize symbol
                if 'class' in kind or kind == 'c':
                    file_structure['classes'].append(symbol_info)
                elif 'function' in kind or 'method' in kind or kind in ['f', 'm']:
                    file_structure['functions'].append(symbol_info)
                elif 'variable' in kind or 'member' in kind or kind in ['v', 'm']:
                    file_structure['variables'].append(symbol_info)
                else:
                    file_structure['other'].append(symbol_info)

            # Sort by line number if showing line numbers
            if show_line_numbers:
                for category in ['classes', 'functions', 'variables', 'other']:
                    file_structure[category].sort(key=lambda x: x.get('line', 0))

            # Calculate symbol counts
            file_structure['symbol_count'] = len(symbols)
            total_symbols += len(symbols)

            project_outline[file_path] = file_structure

        return {
            "success": True,
            "outline": project_outline,
            "file_count": len(project_outline),
            "total_symbols": total_symbols,
            "stats": {
                "files_with_symbols": len(project_outline),
                "total_files_in_tags": len(all_files)
            }
        }

    except Exception as e:
        logger.error(f"Failed to generate project outline: {e}")
        return {"success": False, "error": str(e)}


# ============== Discovery and Utility Tools ==============

@mcp.tool()
async def generate_cross_reference(
    path: str,
    recursive: bool = False,
    languages: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a cross-reference (xref) output for a file or project.

    This tool creates a human-readable tabular cross-reference showing
    all symbols with their locations and context. Unlike tags files,
    xref output is meant for direct reading and documentation.

    Works with both single files and entire directories/projects.

    Args:
        path: Path to source file or directory
        recursive: Recursively process directories (default: False)
        languages: Filter by specific languages (optional)
        exclude_patterns: Patterns to exclude (e.g., ["*.md", "test_*"]) (optional)

    Returns:
        Dictionary with cross-reference entries

    Example (single file):
        xref = await generate_cross_reference(
            path="./CUSTOMER.COB",
            languages=["COBOL"]
        )

    Example (project):
        xref = await generate_cross_reference(
            path="./src",
            recursive=True,
            languages=["Python"],
            exclude_patterns=["test_*.py", "__pycache__"]
        )
    """
    # Validate path
    is_valid, error = validate_path(path)
    if not is_valid:
        return {"success": False, "error": error}

    try:
        entries = ctags_wrapper.generate_cross_reference(
            path=path,
            recursive=recursive,
            languages=languages,
            exclude_patterns=exclude_patterns
        )

        return {
            "success": True,
            "path": os.path.abspath(path),
            "is_directory": os.path.isdir(path),
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        logger.error(f"Failed to generate cross-reference: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def detect_file_language(
    file_path: str
) -> Dict[str, Any]:
    """
    Detect the programming language of a file.

    This tool uses CTags' language detection to identify what programming
    language a file is written in, based on file extension, shebang, and
    content analysis.

    Args:
        file_path: Path to file to analyze

    Returns:
        Dictionary with detected language

    Example:
        result = await detect_file_language(file_path="./script.sh")
        # Returns: {"success": True, "file": "...", "language": "Sh"}
    """
    # Validate file path
    is_valid, error = validate_path(file_path)
    if not is_valid:
        return {"success": False, "error": error}

    try:
        language = ctags_wrapper.detect_language(file_path)

        if language:
            return {
                "success": True,
                "file": os.path.abspath(file_path),
                "language": language
            }
        else:
            return {
                "success": False,
                "file": os.path.abspath(file_path),
                "error": "Language could not be detected"
            }
    except Exception as e:
        logger.error(f"Failed to detect language: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_supported_languages() -> Dict[str, Any]:
    """
    List all programming languages supported by CTags.

    This tool returns a comprehensive list of all languages that Universal
    CTags can parse and generate tags for.

    Returns:
        Dictionary with list of supported languages

    Example:
        result = await list_supported_languages()
        # Returns: {"success": True, "languages": ["Python", "JavaScript", ...], "count": 150}
    """
    try:
        languages = ctags_wrapper.list_languages()

        return {
            "success": True,
            "languages": languages,
            "count": len(languages)
        }
    except Exception as e:
        logger.error(f"Failed to list languages: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_language_kinds(
    language: str
) -> Dict[str, Any]:
    """
    List all tag kinds (types) available for a specific language.

    This tool shows what types of symbols CTags can identify in a given
    language. For example, for Python it shows: classes, functions, variables, etc.
    For COBOL: paragraphs, data, sections, etc.

    Args:
        language: Language name (e.g., "Python", "COBOL", "JavaScript")

    Returns:
        Dictionary with kind information for the language

    Example:
        result = await list_language_kinds(language="COBOL")
        # Returns kinds like: paragraph, data, section, etc.
    """
    try:
        result = ctags_wrapper.list_tag_kinds(language)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to list tag kinds: {e}")
        return {"success": False, "error": str(e)}


# ============== Management Tools ==============

@mcp.tool()
async def list_tags_files(
    search_path: str = ".",
    include_stats: bool = True
) -> List[Dict[str, Any]]:
    """
    List all available tags files in the workspace.
    
    This tool searches for all tags files in the specified directory
    and its subdirectories, providing information about each file.
    
    Args:
        search_path: Directory to search for tags files (default: ".")
        include_stats: Include file statistics (default: True)
    
    Returns:
        List of tags files with metadata
    
    Example:
        tags_files = await list_tags_files(
            search_path="./",
            include_stats=True
        )
    """
    # Validate search path
    is_valid, error = validate_path(search_path)
    if not is_valid:
        return []
    
    tags_files = []
    
    try:
        # Search for tags files using various patterns
        # Common exact names
        exact_names = ["tags", "TAGS", ".tags"]
        
        for root, dirs, files in os.walk(search_path):
            for file in files:
                # Check multiple patterns:
                # 1. Exact match with known names
                # 2. Files ending with .tags
                # 3. Files ending with .tag
                # 4. Files starting with tags
                is_tags_file = (
                    file in exact_names or
                    file.endswith(".tags") or
                    file.endswith(".tag") or
                    file.startswith("tags") or
                    file.startswith(".tags")
                )
                
                if is_tags_file:
                    file_path = os.path.join(root, file)
                    
                    file_info = {
                        "path": os.path.abspath(file_path),
                        "name": file,
                        "directory": os.path.abspath(root)
                    }
                    
                    if include_stats:
                        try:
                            stat = os.stat(file_path)
                            file_info["size"] = stat.st_size
                            file_info["modified"] = stat.st_mtime
                            
                            # Try to get tags info
                            info = ctags_wrapper.get_tags_info(file_path)
                            if "error" not in info:
                                file_info["tag_count"] = info.get("tag_count", 0)
                                file_info["format"] = info.get("format", "unknown")
                        except Exception as e:
                            logger.warning(f"Failed to get stats for {file_path}: {e}")
                    
                    tags_files.append(file_info)
        
        return tags_files
    except Exception as e:
        logger.error(f"Failed to list tags files: {e}")
        return []


@mcp.tool()
async def get_tags_info(
    tags_file: str = "tags"
) -> Dict[str, Any]:
    """
    Get detailed information about a tags file.
    
    This tool provides metadata and statistics about a tags file,
    including format, sorting, size, and tag count.
    
    Args:
        tags_file: Path to tags file (default: "tags")
    
    Returns:
        Dictionary with tags file metadata
    
    Example:
        info = await get_tags_info(tags_file="./project.tags")
    """
    # Validate tags file
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {"success": False, "error": error}
    
    try:
        info = ctags_wrapper.get_tags_info(tags_file)
        
        if "error" in info:
            return {"success": False, "error": info["error"]}
        
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        logger.error(f"Failed to get tags info: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def validate_tags_file(
    tags_file: str = "tags",
    check_files_exist: bool = True
) -> Dict[str, Any]:
    """
    Validate the integrity and consistency of a tags file.
    
    This tool checks if a tags file is valid and optionally verifies
    that all referenced source files still exist.
    
    Args:
        tags_file: Path to tags file (default: "tags")
        check_files_exist: Verify referenced files exist (default: True)
    
    Returns:
        Dictionary with validation results and any issues found
    
    Example:
        result = await validate_tags_file(
            tags_file="./tags",
            check_files_exist=True
        )
    """
    # Basic validation
    is_valid, error = validate_tags_file_util(tags_file)
    if not is_valid:
        return {
            "success": False,
            "valid": False,
            "error": error
        }
    
    issues = []
    stats = {
        "total_tags": 0,
        "missing_files": [],
        "invalid_entries": 0
    }
    
    try:
        # Open and validate tags file structure
        tag_file = ctags_wrapper.open_tags_file(tags_file)
        if not tag_file:
            return {
                "success": False,
                "valid": False,
                "error": "Cannot open tags file"
            }
        
        # Check file references if requested
        if check_files_exist:
            # Import ctags TagEntry locally to avoid import errors when ctags isn't installed
            from ctags import TagEntry as CTagsEntry
            checked_files = set()
            entry = CTagsEntry()
            
            if tag_file.first(entry):
                while True:
                    stats["total_tags"] += 1
                    
                    file_path = entry['file']
                    if file_path and file_path not in checked_files:
                        checked_files.add(file_path)
                        if not os.path.exists(file_path):
                            stats["missing_files"].append(file_path)
                            issues.append(f"Referenced file not found: {file_path}")
                    
                    if not tag_file.next(entry):
                        break
        
        return {
            "success": True,
            "valid": len(issues) == 0,
            "stats": stats,
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Failed to validate tags file: {e}")
        return {
            "success": False,
            "valid": False,
            "error": str(e)
        }


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Universal CTags MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()