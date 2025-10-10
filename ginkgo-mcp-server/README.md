# Ginkgo MCP Server

A comprehensive MCP (Model Context Protocol) Server implementation for the Ginkgo testing framework for Go projects. This server enables developers and AI agents to enhance their workflows with rich test result analysis, intelligent test generation, failure pattern recognition, and systematic debugging assistance.

## Features

### Core Capabilities
- **Function Discovery**: Automatically discover testable functions in Go packages
- **Test Generation**: Generate Ginkgo BDD-style test specs (basic, table-driven, and full suites)
- **Test Execution**: Run Ginkgo tests with comprehensive options and real-time analysis
- **Failure Analysis**: Intelligent pattern recognition for test failures
- **Debugging Support**: Track debugging sessions with step-by-step progress
- **Performance Analysis**: Benchmark execution and performance profiling
- **Coverage Reports**: Generate detailed code coverage reports
- **Similar Failure Detection**: Find historical failures with similar patterns

### Advanced Features
- **AI-Friendly Debugging Prompts**: Generate structured prompts for AI assistants
- **Historical Data Tracking**: Maintain test history and failure patterns
- **Containerized Deployment**: Docker support with multi-stage builds
- **MCP Inspector Integration**: Built-in testing and inspection capabilities
- **BDD-Style Test Generation**: Generate idiomatic Ginkgo specs with Describe, Context, and It blocks

## Prerequisites

- Go 1.24 or later
- Ginkgo v2 installed (`go install github.com/onsi/ginkgo/v2/ginkgo@latest`)
- Docker (optional, for containerized deployment)
- Git (for cloning repositories)

## Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/mcpservershub/mcpservers/ginkgo-mcp
cd ginkgo-mcp-server

# Install dependencies
go mod download

# Build the server
make build

# Or build directly
go build -o ginkgo-mcp-server ./cmd/ginkgo-mcp-server

# Run the server
./bin/ginkgo-mcp-server -work-dir=/path/to/your/go/project
```

### Docker Installation

```bash
# Build the Docker image
docker build -t ginkgo-mcp-server .

# Or use Make
make docker-build

# Run with Docker Compose
docker-compose up -d
```

## Usage

### Command Line Options

```bash
./ginkgo-mcp-server [options]

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
    "ginkgo-mcp": {
      "command": "/path/to/ginkgo-mcp-server",
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
    "ginkgo-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/your/go/projects:/workspace:rw",
        "-v", "ginkgo-mcp-data:/app/data:rw",
        "ginkgo-mcp-server:latest"
      ]
    }
  }
}
```

## Available Tools

### 1. find_testable_functions

Discover all testable functions in a Go package for Ginkgo test generation.

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

**Response:**
```json
{
  "functions": [
    {
      "function_name": "Add",
      "package_name": "calculator",
      "file_path": "/workspace/myproject/pkg/calculator/calculator.go",
      "line_number": 10,
      "is_public": true,
      "has_tests": false,
      "test_coverage": 0,
      "complexity": 1,
      "signature": "func Add(a int, b int) int",
      "parameters": [
        {"name": "a", "type": "int"},
        {"name": "b", "type": "int"}
      ],
      "return_types": ["int"]
    }
  ],
  "count": 1
}
```

### 2. generate_test

Generate a Ginkgo test spec for a specific function.

**Arguments:**
- `package_path` (string, required): Path to the Go package
- `function_name` (string, required): Name of the function to generate test for
- `test_type` (string, optional): Type of test ("basic", "table_driven", "suite"), default: "basic"

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

Suite generation:
```json
{
  "tool_name": "generate_test",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "function_name": "Add",
    "test_type": "suite"
  }
}
```

**Response (Basic Test):**
```json
{
  "function_name": "Add",
  "test_code": "var _ = Describe(\"Add\", func() {\n\tContext(\"with valid input\", func() {\n\t\tIt(\"should return expected result with valid inputs\", func() {\n\t\t\t// Arrange\n\t\t\ta := 42\n\t\t\tb := 42\n\n\t\t\t// Act\n\t\t\tresult := Add(a, b)\n\n\t\t\t// Assert\n\t\t\tExpect(result).To(Equal(42))\n\t\t})\n\t})\n\n})",
  "test_cases": [...],
  "imports": ["testing", "github.com/onsi/ginkgo/v2", "github.com/onsi/gomega"]
}
```

### 3. run_tests

Run Ginkgo tests for a package and analyze results.

**Arguments:**
- `package_path` (string, required): Path to the Go package to test
- `focus` (string, optional): Focus on specific tests matching this pattern
- `skip` (string, optional): Skip tests matching this pattern
- `with_coverage` (boolean, optional): Include code coverage analysis, default: true
- `verbose` (boolean, optional): Run tests in verbose mode, default: false
- `parallel` (integer, optional): Number of parallel test nodes, default: 1
- `timeout` (string, optional): Test timeout duration, default: "5m"

**Example:**
```json
{
  "tool_name": "run_tests",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "with_coverage": true,
    "verbose": true,
    "parallel": 4,
    "timeout": "10m"
  }
}
```

**Response:**
```json
{
  "suite": {
    "name": "/workspace/myproject/pkg/calculator",
    "total_tests": 10,
    "passed_tests": 8,
    "failed_tests": 2,
    "skipped_tests": 0,
    "pending_tests": 0,
    "duration": "2.5s",
    "coverage": {
      "percentage": 85.5
    },
    "tests": [...]
  },
  "analysis": {
    "success_rate": 80.0,
    "failure_rate": 20.0,
    "insights": ["⚠ High success rate but some failures detected"],
    "patterns": [...]
  }
}
```

### 4. analyze_test_failures

Analyze Ginkgo test failure patterns and generate debugging insights.

**Arguments:**
- `test_results` (string, required): JSON string of test results or path to results file

**Example:**
```json
{
  "tool_name": "analyze_test_failures",
  "args": {
    "test_results": "[{\"spec_name\":\"TestDivide\",\"status\":\"failed\",\"failure_message\":\"Expected not to panic\"}]"
  }
}
```

### 5. find_similar_failures

Find similar historical Ginkgo test failures for debugging insights.

**Arguments:**
- `test_name` (string, required): Name of the failing test spec
- `error_message` (string, required): Error or failure message from the test
- `limit` (integer, optional): Maximum number of similar failures to return, default: 5

**Example:**
```json
{
  "tool_name": "find_similar_failures",
  "args": {
    "test_name": "Divide should handle division by zero",
    "error_message": "Expected not to panic but got: runtime error: integer divide by zero",
    "limit": 10
  }
}
```

### 6. generate_debugging_prompt

Generate AI-friendly debugging prompts for Ginkgo test failures.

**Arguments:**
- `test_result` (string, required): JSON string of the failing test result
- `include_similar` (boolean, optional): Include similar historical failures in the prompt, default: true

**Example:**
```json
{
  "tool_name": "generate_debugging_prompt",
  "args": {
    "test_result": "{\"spec_name\":\"ComplexFunction should handle edge cases\",\"status\":\"failed\",\"failure_message\":\"Expected 10 but got 8\"}",
    "include_similar": true
  }
}
```

### 7. start_debugging_session

Start a new debugging session for a failing Ginkgo test.

**Arguments:**
- `test_name` (string, required): Name of the failing test spec
- `failure_type` (string, required): Type of failure (e.g., "assertion", "panic", "timeout")
- `metadata` (object, optional): Additional metadata about the test failure

**Example:**
```json
{
  "tool_name": "start_debugging_session",
  "args": {
    "test_name": "ComplexFunction should handle edge cases",
    "failure_type": "assertion_failed",
    "metadata": {
      "package": "calculator",
      "file": "calculator_test.go",
      "line": "42"
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
    "session_id": "abc123def456",
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

**Example:**
```json
{
  "tool_name": "run_benchmarks",
  "args": {
    "package_path": "/workspace/myproject/pkg/calculator",
    "bench_time": "10s",
    "count": 3
  }
}
```

### 10. get_failure_patterns

Get statistics about historical Ginkgo test failure patterns.

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

Generate detailed code coverage report for Ginkgo tests.

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

### 12. end_debugging_session

End a debugging session with resolution or abandonment.

**Arguments:**
- `session_id` (string, required): ID of the debugging session
- `status` (string, required): Final status: "resolved" or "abandoned"
- `resolution` (string, optional): Description of the resolution or reason for abandonment

**Example:**
```json
{
  "tool_name": "end_debugging_session",
  "args": {
    "session_id": "abc123def456",
    "status": "resolved",
    "resolution": "Fixed by adding nil check before dereferencing pointer"
  }
}
```

## Testing with MCP Inspector

### Using npx (Recommended)

```bash
# Start the ginkgo-mcp-server
./bin/ginkgo-mcp-server -work-dir=/path/to/your/project -debug

# In another terminal, start MCP Inspector
npx @modelcontextprotocol/inspector ginkgo-mcp-server -work-dir=/path/to/your/project
```

### Using Docker Compose

```bash
# Start the services
docker-compose up -d

# The server will be running and ready to accept MCP commands
# You can test it by connecting your MCP client to stdio
```

### Testing Individual Tools

1. **Start the MCP Inspector**
2. **Select a tool** from the available tools list
3. **Fill in the arguments** according to the examples above
4. **Execute the tool** and review the results

### Example Test Workflow

```bash
# 1. Find testable functions
{
  "tool_name": "find_testable_functions",
  "args": {"package_path": "./pkg/calculator"}
}

# 2. Generate a test for the Add function
{
  "tool_name": "generate_test",
  "args": {
    "package_path": "./pkg/calculator",
    "function_name": "Add",
    "test_type": "table_driven"
  }
}

# 3. Run the tests
{
  "tool_name": "run_tests",
  "args": {
    "package_path": "./pkg/calculator",
    "with_coverage": true,
    "verbose": true
  }
}

# 4. If tests fail, analyze the failures
{
  "tool_name": "analyze_test_failures",
  "args": {
    "test_results": "[...]"
  }
}

# 5. Generate debugging prompt for AI assistance
{
  "tool_name": "generate_debugging_prompt",
  "args": {
    "test_result": "{...}",
    "include_similar": true
  }
}
```

## Development

### Project Structure

```
ginkgo-mcp-server/
├── cmd/
│   └── ginkgo-mcp-server/     # Main server entry point
├── internal/
│   ├── analyzer/               # Test result analysis
│   ├── server/                # MCP server implementation
│   ├── testrunner/            # Test execution engine
│   └── tools/                 # Test generation tools
├── pkg/
│   ├── types/                 # Data structures and types
│   └── utils/                 # Utility functions
├── tests/                     # Comprehensive test suite
├── data/                      # Test data and history
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Docker Compose configuration
├── Makefile                   # Build and test automation
└── README.md                  # This file
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run specific test package
go test ./internal/testrunner/...

# Run tests in verbose mode
go test -v ./...
```

### Building for Production

```bash
# Build optimized binary
make build-prod

# Or manually
CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags '-w -s' -o ginkgo-mcp-server ./cmd/ginkgo-mcp-server

# Build Docker image
make docker-build

# Or manually
docker build -t ginkgo-mcp-server:latest .
```

### Code Quality

```bash
# Format code
make fmt

# Run go vet
make vet

# Run linter (requires golangci-lint)
make lint

# Run all checks
make check
```

## Troubleshooting

### Common Issues

1. **"Package not found" errors**
   - Ensure the `package_path` points to a valid Go module
   - Check that `go.mod` exists in the package directory
   - Verify the working directory is set correctly

2. **"Ginkgo command not found"**
   - Install Ginkgo CLI: `go install github.com/onsi/ginkgo/v2/ginkgo@latest`
   - Ensure `$GOPATH/bin` or `$HOME/go/bin` is in your PATH

3. **"Test execution failed" errors**
   - Verify Go toolchain is properly installed
   - Check that all dependencies are available
   - Ensure proper file permissions
   - Run `go mod tidy` to sync dependencies

4. **Docker permission issues**
   - Ensure Docker is running with proper permissions
   - Check volume mount paths are accessible
   - Verify the workspace directory has read/write permissions

5. **Coverage report generation fails**
   - Verify `go tool cover` is available
   - Check output directory permissions
   - Ensure tests compile and run successfully

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
./ginkgo-mcp-server -debug -work-dir=/path/to/project
```

### Logging

The server logs important events and errors to help with debugging:
- Test execution results
- Analysis operations
- File operations
- MCP protocol messages (in debug mode)

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- Additional Ginkgo test generation patterns
- Enhanced failure analysis algorithms
- Performance optimizations
- Documentation improvements
- Bug fixes and feature requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ginkgo](https://github.com/onsi/ginkgo) - Excellent BDD testing framework for Go
- [Gomega](https://github.com/onsi/gomega) - Ginkgo's preferred matcher library
- [MCP Go SDK](https://github.com/mark3labs/mcp-go) - Go implementation of MCP
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standardized protocol for AI integrations

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/mcpservershub/mcpservers/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/mcpservershub/mcpservers/discussions)
- **Documentation**: [Wiki](https://github.com/mcpservershub/mcpservers/wiki)
- **Community**: [Discord](https://discord.gg/mcpservers)

---

Made with ❤️ for the Go and AI development communities.