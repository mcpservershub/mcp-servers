"""Code analysis utilities."""

from typing import Dict, List, Any, Optional
import tree_sitter as ts
from .tree_sitter_helpers import execute_query, get_cached_language
from .query_templates import get_query_template


def extract_symbols(source_code: str, language: str, symbol_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Extract symbols (functions, classes, etc) from code."""
    # Default symbol types if not specified
    if symbol_types is None:
        if language in ["rust", "go", "c"]:
            symbol_types = ["functions", "structs", "imports"]
        elif language == "cpp":
            symbol_types = ["functions", "classes", "structs", "imports"]
        elif language == "typescript":
            symbol_types = ["functions", "classes", "interfaces", "imports"]
        elif language in ["java", "kotlin"]:
            symbol_types = ["classes", "interfaces", "methods", "imports"]
        else:
            symbol_types = ["functions", "classes", "imports"]
    
    # Parse the code
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    # Extract symbols for each type
    symbols: Dict[str, List[Dict[str, Any]]] = {}
    
    for symbol_type in symbol_types:
        template = get_query_template(language, symbol_type)
        if template:
            matches = execute_query(tree, template, language, source_bytes)
            
            # Group by symbol type and format
            formatted_matches = []
            for match in matches:
                if match["capture"].endswith(".name"):
                    # This is a name capture, find its definition
                    name = match["text"]
                    # Look for the corresponding definition
                    for m in matches:
                        if m["capture"].endswith(".def") and m["start_byte"] <= match["start_byte"] <= m["end_byte"]:
                            formatted_matches.append({
                                "name": name,
                                "type": symbol_type.rstrip("s"),  # Remove plural
                                "line": match["start_point"]["row"] + 1,
                                "column": match["start_point"]["column"],
                                "text": m["text"][:100] if len(m["text"]) > 100 else m["text"]
                            })
                            break
            
            if formatted_matches:
                symbols[symbol_type] = formatted_matches
    
    return symbols


def analyze_complexity(source_code: str, language: str) -> Dict[str, Any]:
    """Analyze code complexity metrics."""
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    # Basic metrics
    lines = source_code.split('\n')
    metrics = {
        "total_lines": len(lines),
        "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*'))]),
        "comment_lines": len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))]),
        "blank_lines": len([l for l in lines if not l.strip()]),
    }
    
    # Count different node types for complexity
    def count_nodes(node: ts.Node, node_counts: Dict[str, int]):
        node_type = node.type
        if node_type in ["if_statement", "while_statement", "for_statement", "switch_statement",
                         "try_statement", "catch_clause", "conditional_expression"]:
            node_counts["branches"] = node_counts.get("branches", 0) + 1
        elif node_type in ["function_definition", "function_declaration", "method_definition",
                          "arrow_function", "function_item"]:
            node_counts["functions"] = node_counts.get("functions", 0) + 1
        elif node_type in ["class_definition", "class_declaration", "struct_item", "struct_specifier"]:
            node_counts["classes"] = node_counts.get("classes", 0) + 1
        
        for child in node.children:
            count_nodes(child, node_counts)
    
    node_counts: Dict[str, int] = {}
    count_nodes(tree.root_node, node_counts)
    
    metrics.update({
        "cyclomatic_complexity": node_counts.get("branches", 0) + 1,
        "function_count": node_counts.get("functions", 0),
        "class_count": node_counts.get("classes", 0),
        "max_depth": calculate_max_depth(tree.root_node),
    })
    
    return metrics


def calculate_max_depth(node: ts.Node, current_depth: int = 0) -> int:
    """Calculate the maximum depth of the syntax tree."""
    if not node.children:
        return current_depth
    
    max_child_depth = current_depth
    for child in node.children:
        child_depth = calculate_max_depth(child, current_depth + 1)
        max_child_depth = max(max_child_depth, child_depth)
    
    return max_child_depth


def find_dependencies(source_code: str, language: str) -> Dict[str, List[str]]:
    """Find dependencies (imports) in the code."""
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    dependencies = {
        "imports": [],
        "modules": [],
        "packages": []
    }
    
    # Get import template for the language
    import_template = get_query_template(language, "imports")
    if import_template:
        matches = execute_query(tree, import_template, language, source_bytes)
        for match in matches:
            import_text = match["text"]
            dependencies["imports"].append({
                "statement": import_text,
                "line": match["start_point"]["row"] + 1
            })
            
            # Try to extract module/package names
            if language == "python":
                if "import " in import_text:
                    parts = import_text.replace("from ", "").replace("import ", "").split()
                    if parts:
                        dependencies["modules"].append(parts[0].split('.')[0])
            elif language in ["javascript", "typescript"]:
                if "from" in import_text:
                    # Extract module name from import statement
                    parts = import_text.split("from")
                    if len(parts) > 1:
                        module = parts[1].strip().strip("'\"`;")
                        dependencies["packages"].append(module)
    
    return dependencies


def find_pattern_matches(source_code: str, language: str, pattern: str) -> List[Dict[str, Any]]:
    """Find matches for a custom tree-sitter pattern."""
    lang = get_cached_language(language)
    parser = ts.Parser()
    parser.set_language(lang)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    try:
        matches = execute_query(tree, pattern, language, source_bytes)
        return matches
    except Exception as e:
        return [{"error": str(e)}]