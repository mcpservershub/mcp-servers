# Tree-sitter Graph CLI Setup Guide

## Overview
The `tree_sitter_graph` tool in the MCP server invokes the external `tree-sitter-graph` CLI tool. This requires proper configuration of language grammars for the CLI to work correctly.

## Prerequisites

1. **Install tree-sitter-graph CLI**:
   ```bash
   cargo install tree-sitter-graph
   # or
   npm install -g @tree-sitter/graph
   ```

2. **Tree-sitter Configuration**:
   The CLI looks for a configuration file at `~/.config/tree-sitter/config.json` that specifies parser directories:
   ```json
   {
     "parser-directories": [
       "/home/user/tree-sitter",
       "/home/user/projects"
     ]
   }
   ```

## Language Grammar Setup

For each language you want to use with tree-sitter-graph, you need:

1. **Grammar Directory**: A directory named `tree-sitter-<language>` in one of your parser directories
2. **Compiled Parser**: The `src/parser.c` file must exist (pre-compiled grammars work)
3. **Configuration File**: A `tree-sitter.json` file in the grammar directory

### Example tree-sitter.json

Create this file in each `tree-sitter-<language>` directory:

```json
{
  "grammars": [
    {
      "name": "python",
      "scope": "source.python", 
      "path": ".",
      "file-types": ["py"]
    }
  ]
}
```

Replace "python" with the appropriate language name.

## Directory Structure Example

```
~/tree-sitter/
├── tree-sitter-python/
│   ├── tree-sitter.json    # Configuration file
│   ├── src/
│   │   ├── parser.c        # Compiled parser
│   │   └── ...
│   └── ...
└── tree-sitter-javascript/
    ├── tree-sitter.json
    ├── src/
    │   ├── parser.c
    │   └── ...
    └── ...
```

## Testing the Setup

1. **Test the CLI directly**:
   ```bash
   cd ~/tree-sitter/tree-sitter-python
   tree-sitter-graph --json query.tsg code.py
   ```

2. **Test via MCP tool**:
   ```python
   {
     "tool": "tree_sitter_graph",
     "arguments": {
       "tsg_file": "./query.tsg",
       "source_file": "./code.py",
       "output_file": "./output.json"
     }
   }
   ```

## TSG Query Syntax

Tree-sitter graph queries use a specific syntax:

```tsg
; Capture function definitions
(function_definition
  name: (identifier) @name)
{
  node func_node
  attr (func_node) type = "function"
  attr (func_node) name = (source-text @name)
}
```

Key points:
- Comments start with `;`
- Captures use `@name` syntax
- Graph stanzas define nodes and attributes
- Use `(source-text @capture)` to get text content

## Troubleshooting

### "No language found" error
- Ensure the grammar directory exists in a configured parser directory
- Check that `tree-sitter.json` exists in the grammar directory
- Verify the `src/parser.c` file exists

### "Cannot parse TSG file" error
- Check TSG syntax - no colons after attribute names
- Ensure all captures are used or prefixed with `_` if unused
- Validate parentheses are balanced

### Working Directory Matters
The tree-sitter-graph CLI searches for grammars relative to the current directory and configured parser directories. Running from different locations may affect language detection.

## Using with Docker

When running the MCP server in Docker, the tree-sitter-graph CLI and grammar files need to be available inside the container. Consider:
1. Installing grammars during Docker build
2. Mounting grammar directories as volumes
3. Setting up configuration in the container

## Resources

- [Tree-sitter Graph Documentation](https://github.com/tree-sitter/tree-sitter-graph)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [TSG Query Syntax](https://docs.rs/tree-sitter-graph/latest/tree_sitter_graph/)