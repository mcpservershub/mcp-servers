# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

This project uses `uv` for dependency management and `poe` for task orchestration:

- **Linting**: `uv run poe lint` (only allowed command for linting)
- **Formatting**: `uv run poe format` (only allowed command for formatting) 
- **Type checking**: `uv run poe type-check` (only allowed command for type checking)
- **Testing**: `uv run poe test [args]` (preferred) or `uv run pytest [args]`

**Important**: Always run `format`, `type-check` and `test` at the end of tasks to ensure code quality. Fix any issues and re-run until they pass.

## Architecture Overview

Serena is a powerful coding agent toolkit that turns LLMs into fully-featured agents working directly on codebases through semantic code retrieval and editing tools.

### Core Components

- **src/serena/**: Main package containing core functionality
  - `mcp.py`: Model Context Protocol server implementation
  - `agno.py`: Agno framework integration for model-agnostic agents
  - `agent.py`: Core agent implementation with semantic tools
  - **llm/**: LLM integration modules
  - **util/**: Utility functions and helpers

- **src/multilspy/**: Language server integration layer
  - **language_servers/**: Language-specific implementations
    - Python (pyright/jedi), Java (Eclipse JDTLS), TypeScript/JavaScript
    - C#, Rust, Go, Ruby, C++, PHP support
  - Provides semantic code analysis through Language Server Protocol (LSP)

- **src/interprompt/**: Template and prompt management system

### Key Design Principles

- **Semantic Code Understanding**: Uses language servers (LSP) for symbol-level code analysis rather than text-based approaches
- **Multiple Integration Methods**: Can be used as MCP server, Agno agent, or integrated into custom frameworks  
- **Language Agnostic**: Supports multiple programming languages through language server adapters
- **Context and Mode System**: Configurable behavior for different environments (desktop-app, ide-assistant, agent)

### Integration Patterns

- **MCP Server**: Primary integration method for Claude Desktop and other MCP clients
- **Agno Agent**: Model-agnostic agent framework for any LLM with GUI support
- **Framework Adapter**: Tools can be adapted to any agent framework (example: SerenaAgnoToolkit)

### Configuration System

Four-layer configuration hierarchy:
1. `serena_config.yml` - Global settings
2. CLI arguments - Client-specific overrides  
3. `.serena/project.yml` - Project-specific settings
4. Active modes - Runtime behavior modification

The codebase implements sophisticated semantic code operations through language servers, enabling precise symbol-level editing and code understanding that goes beyond simple text manipulation.

## Working on Serena's Code

**Important**: When working on this codebase, remember that you are using Serena's own tools to improve Serena itself. This means:

- You can use Serena's semantic tools (`find_symbol`, `replace_symbol_body`, `search_for_pattern`, etc.) to analyze and edit Serena's own source code
- When asked to "perform a task on Serena", you're being asked to modify/improve the current Serena codebase
- You have access to the full power of Serena's semantic code understanding to work on Serena's code