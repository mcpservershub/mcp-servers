# Tree-sitter MCP Test Files

This directory contains sample code files for testing the Tree-sitter MCP server with various programming languages.

## Files

- **example.py** - Python code with classes, async functions, decorators, and comprehensions
- **example.js** - JavaScript with ES6+ features, classes, async/await, and generators
- **example.go** - Go code with interfaces, goroutines, channels, and generics
- **example.rs** - Rust code with traits, ownership, async, and error handling
- **example.java** - Java with OOP, generics, streams, and modern features
- **example.cs** - C# (.NET) with records, pattern matching, LINQ, async/await, and nullable references

## Usage with Docker

```bash
# Run the container with this directory mounted
docker run -i -v $(pwd):/test tree-sitter-mcp

# Connect with MCP Inspector
npx @modelcontextprotocol/inspector docker run -i -v $(pwd):/test tree-sitter-mcp
```

## Output Directory

The `output/` directory is where generated AST and graph files will be saved when using the `output_file` parameter in the MCP tools.

## Quick Test

To quickly test all languages, use these tool calls in the MCP Inspector:

1. List supported languages:
```json
{"tool": "list_languages", "arguments": {}}
```

2. Generate AST for Python:
```json
{
  "tool": "generate_ast",
  "arguments": {
    "source_code": "class Person:\n    def __init__(self, name):\n        self.name = name",
    "language": "python",
    "output_file": "/test/output/test_ast.json"
  }
}
```

3. Generate PNG graph:
```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "function test() { return 42; }",
    "language": "javascript",
    "format": "png",
    "output_file": "/test/output/test_graph.png"
  }
}
```

See `test_commands.md` for more detailed testing instructions.