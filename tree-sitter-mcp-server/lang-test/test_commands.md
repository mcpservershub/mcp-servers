# Tree-sitter MCP Container Test Commands

This directory contains sample code files in 6 different languages for testing the Tree-sitter MCP server in a container.

## Setup

1. **Build the Docker image:**
```bash
docker build -t tree-sitter-mcp .
```

2. **Run container with mounted test directory:**
```bash
# Mount the lang-test directory to /test in the container
docker run -i -v $(pwd)/lang-test:/test tree-sitter-mcp
```

3. **Connect with MCP Inspector:**
```bash
# Run inspector with mounted volume
npx @modelcontextprotocol/inspector docker run -i -v $(pwd)/lang-test:/test tree-sitter-mcp
```

## Test Commands for MCP Inspector

### 1. Python - Generate AST and save to file

```json
{
  "tool": "generate_ast",
  "arguments": {
    "source_code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)",
    "language": "python",
    "max_depth": 4,
    "output_file": "/test/output/python_ast.json"
  }
}
```

### 2. JavaScript - Generate PNG graph

```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "class Dog extends Animal {\n    speak() {\n        return 'Woof!';\n    }\n}",
    "language": "javascript",
    "format": "png",
    "output_file": "/test/output/javascript_graph.png"
  }
}
```

### 3. Go - Generate DOT graph

```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "func Map[T, U any](slice []T, fn func(T) U) []U {\n    result := make([]U, len(slice))\n    for i, v := range slice {\n        result[i] = fn(v)\n    }\n    return result\n}",
    "language": "go",
    "format": "dot",
    "output_file": "/test/output/go_graph.dot"
  }
}
```

### 4. Rust - Generate SVG graph

```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "impl<T: Clone> Repository<T> for InMemoryRepository<T> {\n    fn save(&mut self, item: T) -> Result<(), AppError> {\n        Ok(())\n    }\n}",
    "language": "rust",
    "format": "svg",
    "output_file": "/test/output/rust_graph.svg"
  }
}
```

### 5. Java - Query for class definitions

```json
{
  "tool": "query_code",
  "arguments": {
    "source_code": "class Car extends AbstractVehicle {\n    public void start() {\n        System.out.println(\"Started\");\n    }\n}",
    "language": "java",
    "query_pattern": "(class_declaration name: (identifier) @class_name)"
  }
}
```

### 6. C# (.NET) - Generate AST with Records and Pattern Matching

```json
{
  "tool": "generate_ast",
  "arguments": {
    "source_code": "public record Person(string FirstName, string LastName)\n{\n    public string FullName => $\"{FirstName} {LastName}\";\n}",
    "language": "c_sharp",
    "max_depth": 5,
    "output_file": "/test/output/csharp_ast.json"
  }
}
```

### C# - Generate PNG graph for async method

```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "public async Task<Customer?> GetCustomerAsync(int id)\n{\n    var customer = await _repository.GetByIdAsync(id);\n    return customer?.Type == CustomerType.VIP ? customer : null;\n}",
    "language": "c_sharp",
    "format": "png",
    "output_file": "/test/output/csharp_async_graph.png"
  }
}
```

## Reading Files from Container

The tools now support reading files directly by providing file paths instead of source code:

### Read Python file directly and generate AST
```json
{
  "tool": "generate_ast",
  "arguments": {
    "source_code": "/test/example.py",
    "language": "python",
    "output_file": "/test/output/example_py_full_ast.json"
  }
}
```

### Generate graph from Go file
```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "/test/example.go",
    "language": "go",
    "format": "png",
    "max_nodes": 500,
    "output_file": "/test/output/example_go_full.png"
  }
}
```

### Read JavaScript file and generate SVG
```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "/test/example.js",
    "language": "javascript",
    "format": "svg",
    "output_file": "/test/output/example_js.svg"
  }
}
```

### Generate AST from Rust file
```json
{
  "tool": "generate_ast",
  "arguments": {
    "source_code": "/test/example.rs",
    "language": "rust",
    "max_depth": 3,
    "output_file": "/test/output/rust_ast.json"
  }
}
```

### Process C# file
```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "/test/example.cs",
    "language": "c_sharp",
    "format": "dot",
    "output_file": "/test/output/csharp.dot"
  }
}
```

### Java file to PNG
```json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "/test/example.java",
    "language": "java",
    "format": "png",
    "max_nodes": 1000,
    "output_file": "/test/output/java_full.png"
  }
}
```

## Verify Output

After running the tests, check the output directory:

```bash
# From host machine
ls -la lang-test/output/

# Files should include:
# - python_ast.json
# - javascript_graph.png
# - go_graph.dot
# - rust_graph.svg
```

## Container Commands

### Interactive testing
```bash
# Run container interactively
docker run -it -v $(pwd)/lang-test:/test tree-sitter-mcp bash

# Inside container, test the server manually
python -m tree_sitter_mcp.server
```

### Check generated files
```bash
# View generated AST
cat lang-test/output/python_ast.json | jq '.'

# Convert DOT to PNG (if graphviz installed locally)
dot -Tpng lang-test/output/go_graph.dot -o lang-test/output/go_graph_converted.png

# Open SVG in browser
open lang-test/output/rust_graph.svg
```

## Notes

- The `/test` directory in the container maps to `./lang-test` on the host
- Output files are saved to `/test/output/` in the container (creates `./lang-test/output/` on host)
- PNG and SVG formats require the graphviz package (included in the container)
- All generated files persist on the host after container stops