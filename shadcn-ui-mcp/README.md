# Shadcn UI v4 MCP Server - Comprehensive Developer Guide

[![npm version](https://badge.fury.io/js/@jpisnice%2Fshadcn-ui-mcp-server.svg)](https://badge.fury.io/js/@jpisnice%2Fshadcn-ui-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/Jpisnice/shadcn-ui-mcp-server)](https://archestra.ai/mcp-catalog/jpisnice__shadcn-ui-mcp-server)

> **The complete Model Context Protocol (MCP) server for AI-powered development with shadcn/ui components**

## 📚 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Installation](#-installation)
  - [NPX (Recommended)](#npx-recommended---no-installation-required)
  - [Global Installation](#global-installation)
  - [Local Development](#local-development)
- [Quick Start](#-quick-start)
  - [Get a GitHub Token](#1-get-a-github-token-recommended)
  - [Choose Your Framework](#2-choose-your-framework)
- [MCP Tools Reference](#-mcp-tools-reference)
  - [Component Tools](#component-tools)
    - [get_component](#1-get_component)
    - [get_component_demo](#2-get_component_demo)
    - [list_components](#3-list_components)
    - [get_component_metadata](#4-get_component_metadata)
  - [Block Tools](#block-tools)
    - [get_block](#5-get_block)
    - [list_blocks](#6-list_blocks)
  - [Repository Tools](#repository-tools)
    - [get_directory_structure](#7-get_directory_structure)
- [Framework Support](#-framework-support)
  - [Supported Frameworks](#supported-frameworks)
  - [Framework-Specific Features](#framework-specific-features)
- [Integration Guides](#-integration-guides)
  - [Claude Desktop](#claude-desktop)
  - [VS Code with Continue.dev](#vs-code-with-continuedev)
  - [Cursor IDE](#cursor-ide)
  - [Claude Code](#claude-code)
- [Usage Examples](#-usage-examples)
  - [AI Assistant Prompts](#ai-assistant-prompts)
  - [Programmatic Usage](#programmatic-usage)
- [Docker Support](#-docker-support)
  - [Using the Pre-built Image](#using-the-pre-built-image)
  - [Docker Compose](#docker-compose)
  - [Dockerfile Features](#dockerfile-features)
- [Configuration](#-configuration)
  - [Environment Variables](#environment-variables)
  - [Command-Line Arguments](#command-line-arguments)
- [Advanced Features](#-advanced-features)
  - [Circuit Breaker Protection](#circuit-breaker-protection)
  - [Caching System](#caching-system)
  - [Security Features](#security-features)
- [Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
  - [Debug Mode](#debug-mode)
  - [Getting Help](#getting-help)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 Overview

The Shadcn UI MCP Server is a Model Context Protocol implementation that enables AI assistants to interact with shadcn/ui components programmatically. It provides structured access to component source code, demos, blocks, and metadata across multiple frameworks including React, Vue, Svelte, and React Native.

## ✨ Key Features

- **🎨 Multi-Framework Support**: Access components in React, Vue, Svelte, and React Native
- **📦 Complete Component Library**: Full access to shadcn/ui v4 component source code
- **🏗️ Block Templates**: Ready-to-use UI blocks for dashboards, forms, calendars, and more
- **🎭 Live Demos**: Working examples and usage patterns for every component
- **📋 Metadata Access**: Component dependencies, TypeScript types, and configuration details
- **⚡ Smart Caching**: Efficient GitHub API usage with rate limit handling
- **📂 Directory Browsing**: Explore repository structure programmatically

## 📦 Installation

### NPX (Recommended - No Installation Required)

```bash
# Run directly without installation
npx @jpisnice/shadcn-ui-mcp-server

# With GitHub token for higher rate limits
npx @jpisnice/shadcn-ui-mcp-server --github-api-key ghp_your_token_here
```

### Global Installation

```bash
# Install globally
npm install -g @jpisnice/shadcn-ui-mcp-server

# Run the server
shadcn-mcp
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/Jpisnice/shadcn-ui-mcp-server.git
cd shadcn-ui-mcp-server

# Install dependencies
npm install

# Build the project
npm run build

# Start the server
npm start
```

## 🚀 Quick Start

### 1. Get a GitHub Token (Recommended)

Without a token, you're limited to 60 requests/hour. With a token, you get 5,000 requests/hour.

```bash
# Visit: https://github.com/settings/tokens
# Generate a new token (no scopes needed)
# Use it in your commands:
npx @jpisnice/shadcn-ui-mcp-server --github-api-key ghp_your_token_here
```

### 2. Choose Your Framework

```bash
# React (default)
npx @jpisnice/shadcn-ui-mcp-server

# Svelte
npx @jpisnice/shadcn-ui-mcp-server --framework svelte

# Vue
npx @jpisnice/shadcn-ui-mcp-server --framework vue

# React Native
npx @jpisnice/shadcn-ui-mcp-server --framework react-native
```

## 🛠️ MCP Tools Reference

The server exposes the following MCP tools that AI assistants can use:

### Component Tools

#### 1. `get_component`

**Description**: Retrieve the complete source code for a specific shadcn/ui component.

**Parameters**:
- `componentName` (required): Name of the component (e.g., "button", "card", "dialog")

**Returns**: Complete TypeScript/JavaScript source code including imports, interfaces, and implementation

**Example Usage**:
```json
{
  "tool": "get_component",
  "arguments": {
    "componentName": "button"
  }
}
```

**AI Assistant Example**:
```
"Show me the shadcn/ui button component source code"
"Get the card component with TypeScript"
```

#### 2. `get_component_demo`

**Description**: Get demo code showing how to use a specific component with various configurations.

**Parameters**:
- `componentName` (required): Name of the component

**Returns**: Working example code demonstrating component usage patterns and variants

**Example Usage**:
```json
{
  "tool": "get_component_demo",
  "arguments": {
    "componentName": "card"
  }
}
```

**AI Assistant Example**:
```
"Show me how to use the shadcn/ui card component"
"Get examples of button component variants"
```

#### 3. `list_components`

**Description**: List all available components in the selected framework.

**Parameters**: None

**Returns**: Array of all available component names with descriptions

**Example Usage**:
```json
{
  "tool": "list_components",
  "arguments": {}
}
```

**AI Assistant Example**:
```
"List all available shadcn/ui components"
"What components are available in the library?"
```

#### 4. `get_component_metadata`

**Description**: Get detailed metadata about a component including dependencies and configuration.

**Parameters**:
- `componentName` (required): Name of the component

**Returns**: JSON object containing:
- Dependencies (npm packages required)
- TypeScript interfaces
- Configuration options
- Related components
- Documentation links

**Example Usage**:
```json
{
  "tool": "get_component_metadata",
  "arguments": {
    "componentName": "dialog"
  }
}
```

**AI Assistant Example**:
```
"What are the dependencies for the dialog component?"
"Show me the requirements for the card component"
```

### Block Tools

#### 5. `get_block`

**Description**: Retrieve complete block implementations (full UI sections combining multiple components).

**Parameters**:
- `blockName` (required): Name of the block (e.g., "dashboard-01", "login-02", "calendar-01")
- `includeComponents` (optional, default: true): Whether to include component files for complex blocks

**Returns**: Complete block implementation with all required files and components

**Available Block Categories**:
- **Dashboards**: dashboard-01, dashboard-02, dashboard-03, etc.
- **Calendars**: calendar-01, calendar-02, calendar-03
- **Login Forms**: login-01 through login-06
- **Sidebars**: sidebar-01 through sidebar-14
- **Products**: products-01, products-02, products-03

**Example Usage**:
```json
{
  "tool": "get_block",
  "arguments": {
    "blockName": "dashboard-01",
    "includeComponents": true
  }
}
```

**AI Assistant Example**:
```
"Get the dashboard-01 block implementation"
"Show me the login-02 block with all components"
```

#### 6. `list_blocks`

**Description**: List all available blocks, optionally filtered by category.

**Parameters**:
- `category` (optional): Filter by category (dashboard, calendar, login, sidebar, products)

**Returns**: Array of block names with descriptions, organized by category

**Example Usage**:
```json
{
  "tool": "list_blocks",
  "arguments": {
    "category": "dashboard"
  }
}
```

**AI Assistant Example**:
```
"List all available shadcn/ui blocks"
"Show me all dashboard blocks"
```

### Repository Tools

#### 7. `get_directory_structure`

**Description**: Explore the repository structure to understand component organization.

**Parameters**:
- `path` (optional): Path within the repository (default: v4 registry)
- `owner` (optional): Repository owner (default: "shadcn-ui")
- `repo` (optional): Repository name (default: "ui")
- `branch` (optional): Branch name (default: "main")

**Returns**: Directory tree structure with files and folders

**Example Usage**:
```json
{
  "tool": "get_directory_structure",
  "arguments": {
    "path": "apps/www/registry/default/ui"
  }
}
```

**AI Assistant Example**:
```
"Show me the structure of the shadcn/ui repository"
"Explore the components directory"
```

## 🎨 Framework Support

### Supported Frameworks

| Framework | Repository | CLI Flag | Description |
|-----------|------------|----------|-------------|
| **React** | [shadcn/ui](https://ui.shadcn.com/) | `--framework react` (default) | Original React implementation with TypeScript |
| **Svelte** | [shadcn-svelte](https://www.shadcn-svelte.com/) | `--framework svelte` | Svelte port with full component library |
| **Vue** | [shadcn-vue](https://www.shadcn-vue.com/) | `--framework vue` | Vue 3 implementation with Composition API |
| **React Native** | [react-native-reusables](https://github.com/founded-labs/react-native-reusables) | `--framework react-native` | Mobile-optimized components |

### Framework-Specific Features

#### React (Default)
- Full TypeScript support
- Tailwind CSS styling
- Radix UI primitives
- Complete block library
- Server and client components

#### Svelte
- SvelteKit compatible
- Svelte-specific optimizations
- Full component parity with React
- Reactive stores integration

#### Vue
- Vue 3 Composition API
- TypeScript support
- Tailwind CSS integration
- Vue-specific patterns and directives

#### React Native
- Mobile-optimized components
- React Native specific primitives
- Touch-optimized interactions
- Limited block support (components only)

## 🔌 Integration Guides

### Claude Desktop

Add to your Claude Desktop configuration file:

**Location**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration**:
```json
{
  "mcpServers": {
    "shadcn-ui": {
      "command": "npx",
      "args": [
        "@jpisnice/shadcn-ui-mcp-server",
        "--github-api-key",
        "ghp_your_token_here"
      ]
    }
  }
}
```

**Multiple Frameworks**:
```json
{
  "mcpServers": {
    "shadcn-ui-react": {
      "command": "npx",
      "args": ["@jpisnice/shadcn-ui-mcp-server", "--framework", "react"]
    },
    "shadcn-ui-svelte": {
      "command": "npx",
      "args": ["@jpisnice/shadcn-ui-mcp-server", "--framework", "svelte"]
    }
  }
}
```

### VS Code with Continue.dev

Add to your Continue configuration (`~/.continue/config.json`):

```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "shadcn-ui",
      "command": "npx",
      "args": [
        "@jpisnice/shadcn-ui-mcp-server",
        "--github-api-key",
        "ghp_your_token_here"
      ]
    }
  ]
}
```

### Cursor IDE

Add to your Cursor settings:

```json
{
  "mcp.servers": {
    "shadcn-ui": {
      "command": "npx",
      "args": [
        "@jpisnice/shadcn-ui-mcp-server",
        "--github-api-key",
        "ghp_your_token_here"
      ]
    }
  }
}
```

### Claude Code

Create a `.claude` configuration file in your project:

```json
{
  "mcpServers": {
    "shadcn-ui": {
      "command": "npx",
      "args": [
        "@jpisnice/shadcn-ui-mcp-server",
        "--framework",
        "react",
        "--github-api-key",
        "ghp_your_token_here"
      ]
    }
  }
}
```

## 💡 Usage Examples

### AI Assistant Prompts

#### Getting Components

```
"Show me the shadcn/ui button component source code"
"Get the card component with TypeScript"
"Show me how to use the dialog component"
"Get all form-related components"
"Show me the input component with all variants"
```

#### Working with Blocks

```
"Get the dashboard-01 block implementation"
"Show me all available calendar blocks"
"Get the login form block with all components"
"List all sidebar variations"
"Show me the products-01 block for an e-commerce site"
```

#### Framework-Specific Requests

```
"Show me the Svelte version of the button component"
"Get the Vue card component"
"Compare the React and Svelte dialog implementations"
"Show me React Native input components"
"Get the Vue version of dashboard-01 block"
```

#### Building Features

```
"Help me build a login form using shadcn/ui"
"Create a dashboard layout with shadcn/ui blocks"
"Build a product listing page with shadcn components"
"Create a calendar interface using shadcn/ui"
"Build a settings page with form components"
```

### Programmatic Usage

```typescript
// In your AI integration code
const response = await mcp.call({
  tool: 'get_component',
  arguments: {
    componentName: 'button'
  }
});

// Get multiple components
const components = ['button', 'card', 'dialog'];
for (const comp of components) {
  const source = await mcp.call({
    tool: 'get_component',
    arguments: { componentName: comp }
  });
  // Process component source...
}

// Get a complete block
const dashboard = await mcp.call({
  tool: 'get_block',
  arguments: {
    blockName: 'dashboard-01',
    includeComponents: true
  }
});

// List available components
const componentList = await mcp.call({
  tool: 'list_components',
  arguments: {}
});
```

## 🐳 Docker Support

### Using the Pre-built Image

```bash
# Build the image
docker build -t shadcn-mcp .

# Run with environment variables
docker run -e GITHUB_API_KEY=ghp_your_token_here \
           -e FRAMEWORK=react \
           shadcn-mcp

# Run with custom framework
docker run -e FRAMEWORK=svelte shadcn-mcp
```

### Docker Compose

```yaml
version: '3.8'
services:
  shadcn-mcp:
    build: .
    environment:
      - GITHUB_API_KEY=ghp_your_token_here
      - FRAMEWORK=react
    restart: unless-stopped
    ports:
      - "3000:3000"
```

### Dockerfile Features

- Multi-stage build with Chainguard base images for security
- Minimal image size (< 50MB)
- Non-root user execution
- ES module support
- Framework selection via environment variables
- Automatic dependency optimization

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub API token for higher rate limits | None | No |
| `GITHUB_API_KEY` | Alternative token variable | None | No |
| `FRAMEWORK` | Framework selection (react, vue, svelte, react-native) | react | No |
| `NODE_ENV` | Node environment | production | No |
| `DEBUG` | Enable debug logging | false | No |

### Command-Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--github-api-key` | GitHub API token | `--github-api-key ghp_xxx` |
| `--framework` | Framework selection | `--framework svelte` |
| `--help` | Show help information | `--help` |
| `--version` | Show version number | `--version` |

## 🚀 Advanced Features

### Circuit Breaker Protection

The server includes circuit breaker protection for external API calls:
- Automatic retry with exponential backoff
- Graceful degradation on API failures
- Rate limit detection and handling
- Fallback to cached data when available

### Caching System

- 15-minute cache for GitHub API responses
- Reduces API calls for repeated requests
- Automatic cache invalidation
- Memory-efficient LRU cache implementation

### Security Features

- Input validation and sanitization
- No-scope GitHub token support
- Runs as non-root user in Docker
- Minimal attack surface with Chainguard images
- Secure handling of environment variables

## 🐛 Troubleshooting

### Common Issues

#### Rate Limiting

**Problem**: "Rate limit exceeded" errors

**Solution**: Add a GitHub token:
```bash
npx @jpisnice/shadcn-ui-mcp-server --github-api-key ghp_your_token_here
```

#### Framework Not Found

**Problem**: Components not available for selected framework

**Solution**: Verify framework support:
- React Native doesn't support blocks
- Some components may be framework-specific
- Check the framework's official repository

#### Docker Build Errors

**Problem**: Permission errors during Docker build

**Solution**: The Dockerfile now uses proper ownership flags:
```dockerfile
COPY --chown=node:node package*.json ./
```

#### ES Module Errors

**Problem**: "require is not defined" error in Docker

**Solution**: The entrypoint script now uses ES module syntax compatible with `"type": "module"`

#### MCP Connection Issues

**Problem**: AI assistant can't connect to MCP server

**Solution**:
1. Verify the server runs standalone
2. Check configuration file syntax
3. Restart your AI tool
4. Review logs for specific errors

### Debug Mode

Enable verbose logging:
```bash
# Set debug environment variable
DEBUG=* npx @jpisnice/shadcn-ui-mcp-server

# Or in Docker
docker run -e DEBUG=* -e GITHUB_API_KEY=ghp_xxx shadcn-mcp
```

### Getting Help

- **Documentation**: Full docs in `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/Jpisnice/shadcn-ui-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jpisnice/shadcn-ui-mcp-server/discussions)
- **Community**: Join our Discord server

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Jpisnice/shadcn-ui-mcp-server.git
cd shadcn-ui-mcp-server

# Install dependencies
npm install

# Run in development mode
npm run dev

# Run tests
npm test

# Build the project
npm run build

# Lint code
npm run lint

# Type check
npm run type-check
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **[shadcn](https://github.com/shadcn)** - For the amazing React UI component library
- **[huntabyte](https://github.com/huntabyte)** - For the excellent Svelte implementation
- **[unovue](https://github.com/unovue)** - For the comprehensive Vue implementation
- **[Founded Labs](https://github.com/founded-labs)** - For the React Native implementation
- **[Anthropic](https://anthropic.com)** - For the Model Context Protocol specification
- **Community Contributors** - For feedback, bug reports, and contributions

---

**Created with ❤️ by [Janardhan Polle](https://github.com/Jpisnice)**

**⭐ Star this repository if you find it helpful!**

**Follow [@jpisnice](https://twitter.com/jpisnice) for updates**