#!/usr/bin/env python3
"""Simple test to verify graphviz works in container."""

import sys
import subprocess

try:
    # Test if dot command exists
    result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
    print(f"✓ Graphviz dot command found: {result.stderr.strip()}")
except FileNotFoundError:
    print("✗ Graphviz dot command NOT found")
    sys.exit(1)

try:
    import graphviz
    print(f"✓ Python graphviz package imported (version: {graphviz.__version__})")
    
    # Test rendering
    dot_content = "digraph G { A -> B; }"
    graph = graphviz.Source(dot_content)
    png_data = graph.pipe(format='png')
    print(f"✓ PNG rendering successful ({len(png_data)} bytes)")
    
except ImportError as e:
    print(f"✗ Failed to import graphviz: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Rendering failed: {e}")
    sys.exit(1)

print("\n✅ All graphviz tests passed!")