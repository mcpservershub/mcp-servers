# GnuCOBOL MCP Server - Test Suite Documentation

## Overview

This comprehensive test suite validates all functionality of the GnuCOBOL MCP Server, including compilation, syntax checking, code analysis, and batch processing capabilities.

## Test Structure

```
tests/
├── test_gnucobol_mcp.py          # Main test suite
├── sample_cobol/                  # Sample COBOL files
│   ├── valid/                     # Valid COBOL programs
│   │   ├── hello.cob              # Simple hello world
│   │   ├── calculator.cob         # Calculator with operations
│   │   ├── file-operations.cob    # File I/O operations
│   │   ├── array-demo.cob         # Array/table handling
│   │   └── string-manipulation.cob # String operations
│   └── invalid/                   # Invalid COBOL (for error testing)
│       ├── syntax_error.cob       # Syntax errors
│       ├── missing_division.cob   # Missing required division
│       ├── undefined_variable.cob # Undefined variable references
│       ├── type_mismatch.cob      # Type mismatches
│       ├── malformed_structure.cob # Structural errors
│       ├── invalid_picture.cob    # Invalid PICTURE clauses
│       └── missing_period.cob     # Missing period terminators
└── README.md                      # This file
```

## Prerequisites

### 1. Install GnuCOBOL

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y gnucobol
```

#### macOS:
```bash
brew install gnucobol
```

#### Verify installation:
```bash
cobc --version
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
# or using uv:
uv pip install -e ".[dev]"
```

## Running Tests

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests with verbose output
pytest tests/test_gnucobol_mcp.py -v

# Run with coverage
pytest tests/test_gnucobol_mcp.py -v --cov=gnucobol_mcp --cov-report=html

# Run with detailed output
pytest tests/test_gnucobol_mcp.py -v -s
```

### Run Specific Test Classes

```bash
# Test only compilation functionality
pytest tests/test_gnucobol_mcp.py::TestCompileCobol -v

# Test only syntax checking
pytest tests/test_gnucobol_mcp.py::TestSyntaxCheck -v

# Test only code analysis
pytest tests/test_gnucobol_mcp.py::TestAnalyzeCode -v

# Test only batch compilation
pytest tests/test_gnucobol_mcp.py::TestBatchCompile -v

# Test only STDIN/STDOUT processing
pytest tests/test_gnucobol_mcp.py::TestStdioProcessing -v

# Test only error handling
pytest tests/test_gnucobol_mcp.py::TestErrorHandling -v

# Test only MCP integration
pytest tests/test_gnucobol_mcp.py::TestMCPIntegration -v
```

### Run Specific Tests

```bash
# Test compilation of valid hello world
pytest tests/test_gnucobol_mcp.py::TestCompileCobol::test_compile_valid_hello_world -v

# Test syntax error detection
pytest tests/test_gnucobol_mcp.py::TestSyntaxCheck::test_syntax_check_invalid_code -v

# Test listing generation
pytest tests/test_gnucobol_mcp.py::TestAnalyzeCode::test_generate_listing -v
```

### Run Tests with Markers

```bash
# Run only MCP-specific tests
pytest tests/test_gnucobol_mcp.py -m mcp -v

# Run only GnuCOBOL tests
pytest tests/test_gnucobol_mcp.py -m gnucobol -v
```

### Continuous Testing

```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/test_gnucobol_mcp.py -- -v
```

## Test Categories

### 1. TestCompileCobol
Tests the `compile_cobol` MCP tool:
- ✅ Compile valid COBOL programs
- ✅ Handle compilation errors gracefully
- ✅ Support STDIN input
- ✅ Generate executables
- ✅ Handle warnings
- ✅ Process empty input

### 2. TestSyntaxCheck
Tests the `syntax_check` MCP tool:
- ✅ Validate correct COBOL syntax
- ✅ Detect syntax errors
- ✅ Identify missing divisions
- ✅ Fast incremental checking
- ✅ Parse and format error messages

### 3. TestAnalyzeCode
Tests the `analyze_code` MCP tool:
- ✅ Generate compiler listings
- ✅ Create symbol tables
- ✅ Generate cross-reference reports
- ✅ Produce full analysis reports
- ✅ Parse listing output

### 4. TestBatchCompile
Tests the `batch_compile` MCP tool:
- ✅ Compile multiple files
- ✅ Handle mixed valid/invalid files
- ✅ Performance with multiple files
- ✅ Error reporting for batch operations

### 5. TestStdioProcessing
Tests STDIN/STDOUT handling:
- ✅ Read source from STDIN
- ✅ Write errors to STDERR
- ✅ Handle large inputs
- ✅ Unicode character support

### 6. TestErrorHandling
Tests error handling and edge cases:
- ✅ Missing compiler detection
- ✅ Timeout handling
- ✅ Invalid compiler options
- ✅ File permission errors
- ✅ Null input handling
- ✅ Malformed COBOL recovery

### 7. TestMCPIntegration
Tests MCP server integration:
- ✅ Tool interface validation
- ✅ Error response format
- ✅ Success response format
- ✅ JSON serialization

## Sample COBOL Programs

### Valid Programs

#### hello.cob
Simple "Hello, World!" program demonstrating basic COBOL structure.

```bash
cobc -x tests/sample_cobol/valid/hello.cob
./hello
```

#### calculator.cob
Interactive calculator with arithmetic operations (+, -, *, /).

```bash
cobc -x tests/sample_cobol/valid/calculator.cob
./calculator
```

#### file-operations.cob
File I/O operations demonstrating sequential file processing.

```bash
cobc -x tests/sample_cobol/valid/file-operations.cob
```

#### array-demo.cob
Array/table operations with OCCURS clause.

```bash
cobc -x tests/sample_cobol/valid/array-demo.cob
./array-demo
```

#### string-manipulation.cob
String operations including concatenation and case conversion.

```bash
cobc -x tests/sample_cobol/valid/string-manipulation.cob
./string-manipulation
```

### Invalid Programs

All files in `sample_cobol/invalid/` directory are designed to fail compilation for testing error handling:

- **syntax_error.cob**: Missing periods and invalid commands
- **missing_division.cob**: Missing PROCEDURE DIVISION
- **undefined_variable.cob**: References to undefined variables
- **type_mismatch.cob**: Type mismatches in operations
- **malformed_structure.cob**: Invalid level numbers and unclosed statements
- **invalid_picture.cob**: Invalid PICTURE clause definitions
- **missing_period.cob**: Missing period terminators

## Testing Individual COBOL Files

### Syntax Check Only
```bash
cobc -fsyntax-only tests/sample_cobol/valid/hello.cob
```

### Compile to Executable
```bash
cobc -x tests/sample_cobol/valid/hello.cob -o hello
./hello
```

### Generate Listing
```bash
cobc -t tests/sample_cobol/valid/calculator.cob -o calculator.lst
cat calculator.lst
```

### Generate Symbol Table
```bash
cobc -t -ftsymbols tests/sample_cobol/valid/calculator.cob
```

### Generate Cross-Reference
```bash
cobc -t -Xref tests/sample_cobol/valid/calculator.cob
```

### Full Analysis
```bash
cobc -t -ftsymbols -Xref tests/sample_cobol/valid/calculator.cob -o analysis.lst
cat analysis.lst
```

## Expected Test Results

### Successful Test Run
```
tests/test_gnucobol_mcp.py::TestCompileCobol::test_compile_valid_hello_world PASSED      [  5%]
tests/test_gnucobol_mcp.py::TestCompileCobol::test_compile_valid_calculator PASSED       [ 10%]
tests/test_gnucobol_mcp.py::TestCompileCobol::test_compile_invalid_syntax PASSED         [ 15%]
tests/test_gnucobol_mcp.py::TestCompileCobol::test_compile_from_stdin PASSED             [ 20%]
tests/test_gnucobol_mcp.py::TestSyntaxCheck::test_syntax_check_valid_code PASSED         [ 25%]
tests/test_gnucobol_mcp.py::TestSyntaxCheck::test_syntax_check_invalid_code PASSED       [ 30%]
...
================================== XX passed in X.XXs ==================================
```

### Test Failure
If tests fail, check:
1. GnuCOBOL is properly installed: `cobc --version`
2. Virtual environment is activated
3. All dependencies are installed: `pip list | grep pytest`
4. Sample COBOL files exist in `tests/sample_cobol/`

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test GnuCOBOL MCP Server

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install GnuCOBOL
        run: sudo apt-get install -y gnucobol

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/test_gnucobol_mcp.py -v --cov=gnucobol_mcp

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Performance Benchmarks

Expected test execution times (approximate):
- TestCompileCobol: ~2-5 seconds
- TestSyntaxCheck: ~1-2 seconds
- TestAnalyzeCode: ~3-5 seconds
- TestBatchCompile: ~5-10 seconds
- TestStdioProcessing: ~2-3 seconds
- TestErrorHandling: ~1-2 seconds
- TestMCPIntegration: <1 second

Total: ~15-30 seconds (depending on system)

## Troubleshooting

### GnuCOBOL Not Found
```
Error: cobc: command not found
```
**Solution**: Install GnuCOBOL using your package manager.

### Import Errors
```
ModuleNotFoundError: No module named 'pytest'
```
**Solution**: Install dev dependencies: `pip install -e ".[dev]"`

### Sample Files Not Found
```
FileNotFoundError: tests/sample_cobol/valid/hello.cob
```
**Solution**: Ensure all sample files were created properly.

### Compilation Timeouts
```
subprocess.TimeoutExpired
```
**Solution**: Increase timeout values in tests or check system performance.

### Permission Errors
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Ensure write permissions in test directory and /tmp.

## Coverage Goals

Target coverage: ≥ 90%

Generate coverage report:
```bash
pytest tests/test_gnucobol_mcp.py --cov=gnucobol_mcp --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Contributing

When adding new tests:
1. Follow existing test structure and naming conventions
2. Add docstrings describing what the test validates
3. Include both positive and negative test cases
4. Update this README with new test information
5. Ensure all tests pass before submitting PR

## Next Steps

After running tests successfully:
1. Review test coverage report
2. Proceed to MCP Inspector testing (see MCP_INSPECTOR_GUIDE.md)
3. Test with real COBOL projects
4. Integration testing with MCP clients

## References

- [GnuCOBOL Documentation](https://gnucobol.sourceforge.io/)
- [GnuCOBOL Compiler Options](https://gnucobol.sourceforge.io/doc/gnucobol.html)
- [pytest Documentation](https://docs.pytest.org/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## License

This test suite is part of the GnuCOBOL MCP Server project.
