"""Graph generation utilities for syntax trees."""

import base64
from typing import Optional
import tree_sitter as ts

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


def generate_dot_graph(node: ts.Node, source_bytes: bytes, max_nodes: int = 1000) -> str:
    """Generate a DOT graph representation of the syntax tree."""
    dot_lines = ["digraph SyntaxTree {", '    rankdir=TB;', '    node [shape=box];']
    node_count = 0
    
    def add_node(n: ts.Node, parent_id: Optional[str] = None) -> Optional[str]:
        nonlocal node_count
        if node_count >= max_nodes:
            return None
            
        node_id = f"node_{id(n)}"
        node_count += 1
        
        # Get node label
        label = n.type
        if not n.children:
            try:
                text = source_bytes[n.start_byte:n.end_byte].decode("utf-8")
                if len(text) <= 20:
                    label = f"{n.type}\\n'{text}'"
                else:
                    label = f"{n.type}\\n'{text[:17]}...'"
            except:
                pass
        
        # Add node definition
        color = "lightblue" if n.is_named else "lightgray"
        dot_lines.append(f'    {node_id} [label="{label}", fillcolor={color}, style=filled];')
        
        # Add edge from parent
        if parent_id:
            dot_lines.append(f'    {parent_id} -> {node_id};')
        
        # Add children
        for child in n.children:
            add_node(child, node_id)
        
        return node_id
    
    add_node(node)
    dot_lines.append("}")
    
    return "\n".join(dot_lines)


def render_dot_to_image(dot_content: str, format: str = "png") -> bytes:
    """Render DOT content to PNG or SVG image using graphviz."""
    if not GRAPHVIZ_AVAILABLE:
        raise ImportError("graphviz package is required for image generation")
    
    # Create a graph from DOT content
    graph = graphviz.Source(dot_content)
    
    # Render to bytes
    if format == "png":
        return graph.pipe(format='png')
    elif format == "svg":
        return graph.pipe(format='svg')
    else:
        raise ValueError(f"Unsupported image format: {format}")