"""Helper functions for tree-sitter operations."""

import os
from typing import Dict, Any, Optional, List, Tuple
import tree_sitter as ts
from tree_sitter_languages import get_language, get_parser


# Cache for loaded languages
LANGUAGE_CACHE: Dict[str, ts.Language] = {}


def get_cached_language(language_name: str) -> ts.Language:
    """Get a Tree-sitter language, with caching."""
    if language_name not in LANGUAGE_CACHE:
        LANGUAGE_CACHE[language_name] = get_language(language_name)
    return LANGUAGE_CACHE[language_name]


def parse_code(source_code: str, language: str, encoding: str = "utf-8") -> Tuple[ts.Tree, bytes]:
    """Parse source code and return tree and source bytes."""
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    source_bytes = source_code.encode(encoding)
    tree = parser.parse(source_bytes)
    return tree, source_bytes


def parse_file(file_path: str, language: str) -> Tuple[ts.Tree, bytes]:
    """Parse a file and return tree and source bytes."""
    with open(file_path, 'rb') as f:
        source_bytes = f.read()
    
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    tree = parser.parse(source_bytes)
    return tree, source_bytes


def node_to_dict(node: ts.Node, source_bytes: bytes, include_positions: bool = True, 
                 max_depth: Optional[int] = None, current_depth: int = 0,
                 include_text: bool = True) -> Dict[str, Any]:
    """Convert a Tree-sitter node to a dictionary representation."""
    result = {
        "type": node.type,
        "is_named": node.is_named,
    }
    
    if include_positions:
        result.update({
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
            "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
        })
    
    # Add text for leaf nodes or small nodes
    if include_text and (not node.children or (node.end_byte - node.start_byte) < 100):
        try:
            result["text"] = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
        except UnicodeDecodeError:
            result["text"] = "<binary data>"
    
    # Add children if not at max depth
    if node.children and (max_depth is None or current_depth < max_depth):
        result["children"] = [
            node_to_dict(child, source_bytes, include_positions, max_depth, current_depth + 1, include_text)
            for child in node.children
        ]
    elif node.children:
        result["children_count"] = len(node.children)
    
    return result


def find_node_at_position(root_node: ts.Node, row: int, column: int, source_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Find the deepest node containing the given position."""
    def contains_position(node: ts.Node) -> bool:
        start_row, start_col = node.start_point
        end_row, end_col = node.end_point
        
        if start_row < row < end_row:
            return True
        if start_row == row and end_row == row:
            return start_col <= column < end_col
        if start_row == row:
            return start_col <= column
        if end_row == row:
            return column < end_col
        return False
    
    def find_deepest(node: ts.Node) -> Optional[ts.Node]:
        if not contains_position(node):
            return None
        
        # Check children
        for child in node.children:
            deeper = find_deepest(child)
            if deeper:
                return deeper
        
        return node
    
    found_node = find_deepest(root_node)
    if found_node:
        return node_to_dict(found_node, source_bytes, include_positions=True, max_depth=2)
    return None


def execute_query(tree: ts.Tree, query_pattern: str, language: str, source_bytes: bytes) -> List[Dict[str, Any]]:
    """Execute a tree-sitter query and return matches."""
    lang = get_cached_language(language)
    query = lang.query(query_pattern)
    captures = query.captures(tree.root_node)
    
    results = []
    for node, capture_name in captures:
        result = {
            "capture": capture_name,
            "type": node.type,
            "text": source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace"),
            "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
            "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }
        results.append(result)
    
    return results


def detect_language(file_path: str) -> Optional[str]:
    """Detect language from file extension."""
    ext_to_lang = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.java': 'java',
        '.kt': 'kotlin',
        '.swift': 'swift',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'c_sharp',
        '.scala': 'scala',
        '.r': 'r',
        '.jl': 'julia',
        '.lua': 'lua',
        '.vim': 'vim',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.fish': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'scss',
        '.sql': 'sql',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.rst': 'rst',
        '.tex': 'latex',
        '.dockerfile': 'dockerfile',
        '.Dockerfile': 'dockerfile',
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    return ext_to_lang.get(ext)