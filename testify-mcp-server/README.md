# Testify MCP Server

A comprehensive MCP (Model Context Protocol) Server implementation for the Testify testing framework for Go projects. This server enables developers and AI agents to enhance their workflows with rich test result analysis, intelligent test generation, failure pattern recognition, and systematic debugging assistance.

## 🚀 Features

### Core Capabilities
- **🔍 Function Discovery**: Automatically discover testable functions in Go packages
- **🧪 Test Generation**: Generate basic, table-driven, and benchmark tests using testify
- **▶️ Test Execution**: Run tests with comprehensive options and real-time analysis
- **📊 Failure Analysis**: Intelligent pattern recognition for test failures
- **🔧 Debugging Support**: Track debugging sessions with step-by-step progress
- **📈 Performance Analysis**: Benchmark execution and performance profiling
- **📋 Coverage Reports**: Generate detailed code coverage reports
- **🎯 Similar Failure Detection**: Find historical failures with similar patterns

### Advanced Features
- **AI-Friendly Debugging Prompts**: Generate structured prompts for AI assistants
- **Historical Data Tracking**: Maintain test history and failure patterns
- **Containerized Deployment**: Docker support with multi-stage builds
- **MCP Inspector Integration**: Built-in testing and inspection capabilities

## 📋 Prerequisites

- Go 1.24 or later
- Docker (optional, for containerized deployment)
- Git (for cloning repositories)

## 🛠️ Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/mcpservershub/mcpservers/testify-mcp
cd testify-mcp

# Install dependencies
go mod download

# Build the server
go build -o testify-mcp-server ./cmd/testify-mcp-server

# Run the server
./testify-mcp-server -work-dir=/path/to/your/go/project
```

### Docker Installation

```bash
# Build the Docker image
docker build -t testify-mcp-server .

# Run with Docker Compose
docker-compose up -d
```

## 📖 Usage

### Command Line Options

```bash
./testify-mcp-server [options]

Options:
  -work-dir string    Working directory for Go projects (default ".")
  -data-dir string    Directory to store test data and history (default "./data")
  -port int          Port to listen on (0 for stdio) (default 0)
  -debug             Enable debug logging
  -version           Show version and exit
```

### MCP Configuration

#### Standalone Application

```json
{
  "mcpServers": {
    "testify-mcp": {
      "command": "/path/to/testify-mcp-server",
      "args": ["-work-dir", "/path/to/your/go/projects", "-data-dir", "./data"],
      "env": {
        "GO111MODULE": "on"
      }
    }
  }
}
```

#### Docker Container

```json
{
  "mcpServers": {
    "testify-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/your/go/projects:/workspace:rw",
        "-v", "testify-mcp-data:/app/data:rw",
        "testify-mcp-server:latest"
      ]
    }
  }
}
```

## 🔧 Available Tools

### 1. find_testable_functions

Discover all testable functions in a Go package.

**Arguments:**
- `package_path` (string, required): Path to the Go package to analyze

**Example:**
```json
{
  "tool_name": "find_testable_functions",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator"
  }
}
```

### 2. generate_test

Generate a test for a specific function using testify framework.

**Arguments:**
- `package_path` (string, required): Path to the Go package
- `function_name` (string, required): Name of the function to generate test for
- `test_type` (string, optional): Type of test ("basic", "table_driven", "benchmark"), default: "basic"

**Examples:**

Basic test:
```json
{
  "tool_name": "generate_test",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "function_name": "Add",
    "test_type": "basic"
  }
}
```

Table-driven test:
```json
{
  "tool_name": "generate_test",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "function_name": "Divide",
    "test_type": "table_driven"
  }
}
```

Benchmark test:
```json
{
  "tool_name": "generate_test",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "function_name": "ComplexCalculation",
    "test_type": "benchmark"
  }
}
```

### 3. run_tests

Run tests for a specific package and analyze results.

**Arguments:**
- `package_path` (string, required): Path to the Go package to test
- `test_pattern` (string, optional): Pattern to match specific tests
- `with_coverage` (boolean, optional): Include code coverage analysis, default: true
- `verbose` (boolean, optional): Run tests in verbose mode, default: false
- `timeout` (string, optional): Test timeout, default: "5m"

**Example:**
```json
{
  "tool_name": "run_tests",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "with_coverage": true,
    "verbose": true,
    "timeout": "10m"
  }
}
```

### 4. analyze_test_failures

Analyze test failure patterns and generate debugging insights.

**Arguments:**
- `test_results` (string, required): JSON string of test results or path to results file

**Example:**
```json
{
  "tool_name": "analyze_test_failures",
  "args": {
    "test_results": "[{\"test_name\":\"TestDivide\",\"status\":\"failed\",\"error\":\"panic: runtime error: integer divide by zero\"}]"
  }
}
```

### 5. find_similar_failures

Find similar historical test failures for debugging insights.

**Arguments:**
- `test_name` (string, required): Name of the failing test
- `error_message` (string, required): Error message from the failing test
- `limit` (integer, optional): Maximum number of similar failures to return, default: 5

**Example:**
```json
{
  "tool_name": "find_similar_failures",
  "args": {
    "test_name": "TestDivideByZero",
    "error_message": "panic: runtime error: integer divide by zero",
    "limit": 10
  }
}
```

### 6. generate_debugging_prompt

Generate AI-friendly debugging prompts for test failures.

**Arguments:**
- `test_result` (string, required): JSON string of the failing test result
- `include_similar` (boolean, optional): Include similar failures in the prompt, default: true

**Example:**
```json
{
  "tool_name": "generate_debugging_prompt",
  "args": {
    "test_result": "{\"test_name\":\"TestComplexFunction\",\"status\":\"failed\",\"error\":\"assertion failed: expected 10, got 8\"}",
    "include_similar": true
  }
}
```

### 7. start_debugging_session

Start a new debugging session for a failing test.

**Arguments:**
- `test_name` (string, required): Name of the failing test
- `failure_type` (string, required): Type of failure (e.g., "assertion", "panic", "timeout")
- `metadata` (object, optional): Additional metadata about the test failure

**Example:**
```json
{
  "tool_name": "start_debugging_session",
  "args": {
    "test_name": "TestComplexFunction",
    "failure_type": "assertion_failed",
    "metadata": {
      "package": "calculator",
      "line": "42",
      "function": "ComplexFunction"
    }
  }
}
```

### 8. track_debugging_step

Track a debugging step in an active session.

**Arguments:**
- `session_id` (string, required): ID of the debugging session
- `description` (string, required): Description of the debugging step
- `action` (string, required): Action taken during this step
- `result` (string, required): Result of the debugging action
- `data` (object, optional): Additional data for this step

**Example:**
```json
{
  "tool_name": "track_debugging_step",
  "args": {
    "session_id": "abc123def",
    "description": "Analyzed function parameters",
    "action": "parameter_analysis",
    "result": "Found invalid parameter combination",
    "data": {
      "invalid_params": ["a=0", "b=0"],
      "expected_behavior": "should return error"
    }
  }
}
```

### 9. run_benchmarks

Run benchmarks for a Go package and analyze performance.

**Arguments:**
- `package_path` (string, required): Path to the Go package to benchmark
- `bench_time` (string, optional): Time to run each benchmark, default: "1s"
- `count` (integer, optional): Number of times to run each benchmark, default: 1
- `mem_profile` (boolean, optional): Generate memory profile, default: false

**Example:**
```json
{
  "tool_name": "run_benchmarks",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "bench_time": "10s",
    "count": 3,
    "mem_profile": true
  }
}
```

### 10. get_failure_patterns

Get statistics about historical failure patterns.

**Arguments:**
- `limit` (integer, optional): Maximum number of patterns to return, default: 10

**Example:**
```json
{
  "tool_name": "get_failure_patterns",
  "args": {
    "limit": 20
  }
}
```

### 11. generate_coverage_report

Generate detailed code coverage report.

**Arguments:**
- `package_path` (string, required): Path to the Go package
- `output_path` (string, optional): Path to save the coverage report, default: "./coverage"

**Example:**
```json
{
  "tool_name": "generate_coverage_report",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "output_path": "/workspace/myproject/reports/coverage"
  }
}
```

## 🧪 Testing with MCP Inspector

### Using Docker Compose (Recommended)

```bash
# Start the services
docker-compose up -d

# Access MCP Inspector at http://localhost:3000
# The inspector will automatically connect to the testify-mcp-server
```

### Manual Setup

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Start the testify-mcp-server
./testify-mcp-server -port 8080 -work-dir=/path/to/your/project

# Start MCP Inspector
mcp-inspector http://localhost:8080
```

### Testing Individual Tools

1. **Open MCP Inspector** in your browser
2. **Select a tool** from the available tools list
3. **Fill in the arguments** according to the examples above
4. **Execute the tool** and review the results

## 🔧 Development

### Project Structure

```
testify-mcp-server/
├── cmd/
│   └── testify-mcp-server/     # Main server entry point
├── internal/
│   ├── analyzer/               # Test result analysis
│   ├── server/                # MCP server implementation
│   ├── testrunner/            # Test execution engine
│   └── tools/                 # Test generation tools
├── pkg/
│   ├── types/                 # Data structures and types
│   └── utils/                 # Utility functions
├── tests/                     # Comprehensive test suite
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Docker Compose configuration
└── README.md                  # This file
```

### Running Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run specific test suite
go test ./tests/

# Run tests in verbose mode
go test -v ./...
```

### Building for Production

```bash
# Build optimized binary
CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags '-w -s' -o testify-mcp-server ./cmd/testify-mcp-server

# Build Docker image
docker build -t testify-mcp-server:latest .

# Build multi-platform images
docker buildx build --platform linux/amd64,linux/arm64 -t testify-mcp-server:latest .
```

## 🐛 Troubleshooting

### Common Issues

1. **"Package not found" errors**
   - Ensure the `package_path` points to a valid Go module
   - Check that `go.mod` exists in the package directory

2. **"Test execution failed" errors**
   - Verify Go toolchain is properly installed
   - Check that all dependencies are available
   - Ensure proper file permissions

3. **Docker permission issues**
   - Ensure Docker is running with proper permissions
   - Check volume mount paths are accessible

4. **Coverage report generation fails**
   - Verify `go tool cover` is available
   - Check output directory permissions

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
./testify-mcp-server -debug -work-dir=/path/to/project
```

### Logging

The server logs important events and errors to help with debugging:
- Test execution results
- Analysis operations
- File operations
- MCP protocol messages (in debug mode)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- Additional test generation patterns
- Enhanced failure analysis algorithms
- Performance optimizations
- Documentation improvements
- Bug fixes and feature requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Testify](https://github.com/stretchr/testify) - Excellent Go testing framework
- [MCP Go SDK](https://github.com/mark3labs/mcp-go) - Go implementation of MCP
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standardized protocol for AI integrations

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/mcpservershub/mcpservers/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/mcpservershub/mcpservers/discussions)
- 📚 **Documentation**: [Wiki](https://github.com/mcpservershub/mcpservers/wiki)
- 💬 **Community**: [Discord](https://discord.gg/mcpservers)

---

Made with ❤️ for the Go and AI development communities.