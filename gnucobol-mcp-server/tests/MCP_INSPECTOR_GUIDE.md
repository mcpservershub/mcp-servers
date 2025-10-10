# GnuCOBOL MCP Server - MCP Inspector Testing Guide

## Overview

This guide provides step-by-step instructions for testing the GnuCOBOL MCP Server using the MCP Inspector tool. The MCP Inspector allows you to interactively test MCP tools, view their responses, and validate the server implementation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installing MCP Inspector](#installing-mcp-inspector)
3. [Starting the MCP Server](#starting-the-mcp-server)
4. [Connecting MCP Inspector](#connecting-mcp-inspector)
5. [Testing MCP Tools](#testing-mcp-tools)
6. [Test Scenarios](#test-scenarios)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Testing](#advanced-testing)

## Prerequisites

### 1. GnuCOBOL Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y gnucobol

# macOS
brew install gnucobol

# Verify installation
cobc --version
```

### 2. Python Environment
```bash
# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install GnuCOBOL MCP Server
pip install -e .
```

### 3. Node.js and npm
MCP Inspector requires Node.js:
```bash
# Check if Node.js is installed
node --version
npm --version

# Install Node.js if needed
# Ubuntu/Debian:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS:
brew install node
```

## Installing MCP Inspector

### Option 1: Using npx (Recommended)
```bash
# No installation needed, run directly
npx @modelcontextprotocol/inspector
```

### Option 2: Global Installation
```bash
# Install globally
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector
```

### Option 3: Local Installation
```bash
# Create a directory for inspector
mkdir -p ~/mcp-testing
cd ~/mcp-testing

# Install locally
npm install @modelcontextprotocol/inspector

# Run inspector
npx @modelcontextprotocol/inspector
```

## Starting the MCP Server

### Method 1: Direct Python Execution
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server in STDIO mode
python -m gnucobol_mcp
```

### Method 2: Using uv
```bash
uv run python -m gnucobol_mcp
```

### Method 3: Using the installed script
```bash
gnucobol-mcp
```

The server should start and wait for STDIO input. You should see output like:
```
GnuCOBOL MCP Server v0.1.0 started
Running in STDIO mode...
```

## Connecting MCP Inspector

### Step 1: Launch MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```

This will open your web browser at `http://localhost:5173` (or similar).

### Step 2: Configure Connection

In the MCP Inspector web interface:

1. **Server Type**: Select "STDIO"
2. **Command**: Enter the path to your Python interpreter and server module:
   ```
   /path/to/.venv/bin/python -m gnucobol_mcp
   ```
   Or use the absolute path:
   ```
   /home/santosh/gnucobol/.venv/bin/python -m gnucobol_mcp
   ```

3. **Arguments**: Leave empty or add any server arguments

4. Click "Connect"

### Step 3: Verify Connection

Once connected, you should see:
- ✅ Connection status: "Connected"
- 📋 List of available tools in the sidebar
- 🟢 Server health indicator

Expected tools:
- `compile_cobol`
- `syntax_check`
- `analyze_code`
- `batch_compile`

## Testing MCP Tools

### 1. Testing `compile_cobol`

#### Test 1.1: Compile Valid Hello World

**Tool**: `compile_cobol`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO-WORLD.\n\n       PROCEDURE DIVISION.\n           DISPLAY \"Hello, World!\".\n           STOP RUN.",
  "output_name": "hello",
  "compile_options": ["-x"]
}
```

**Expected Response**:
```json
{
  "success": true,
  "executable": "/path/to/hello",
  "output": "Compilation successful",
  "warnings": [],
  "returncode": 0
}
```

#### Test 1.2: Compile Invalid Code

**Tool**: `compile_cobol`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. INVALID.\n\n       PROCEDURE DIVISION.\n           INVALID-COMMAND.\n           STOP RUN.",
  "output_name": "invalid",
  "compile_options": ["-x"]
}
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Compilation failed",
  "stderr": "... error messages ...",
  "returncode": 1
}
```

#### Test 1.3: Compile with Warnings

**Tool**: `compile_cobol`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. WARNINGS.\n\n       DATA DIVISION.\n       WORKING-STORAGE SECTION.\n       01 UNUSED-VAR PIC X(10).\n       01 USED-VAR PIC X(10).\n\n       PROCEDURE DIVISION.\n           DISPLAY USED-VAR.\n           STOP RUN.",
  "output_name": "warnings",
  "compile_options": ["-x", "-Wall"]
}
```

**Expected Response**:
```json
{
  "success": true,
  "executable": "/path/to/warnings",
  "warnings": ["... warning messages ..."],
  "returncode": 0
}
```

### 2. Testing `syntax_check`

#### Test 2.1: Check Valid Syntax

**Tool**: `syntax_check`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. VALID-SYNTAX.\n\n       PROCEDURE DIVISION.\n           DISPLAY \"Valid COBOL\".\n           STOP RUN."
}
```

**Expected Response**:
```json
{
  "success": true,
  "valid": true,
  "errors": [],
  "message": "Syntax is valid"
}
```

#### Test 2.2: Detect Syntax Errors

**Tool**: `syntax_check`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. SYNTAX-ERROR.\n\n       PROCEDURE DIVISION.\n           DISPLAY \"Missing period\"\n           INVALID-STATEMENT.\n           STOP RUN."
}
```

**Expected Response**:
```json
{
  "success": true,
  "valid": false,
  "errors": [
    {
      "line": 6,
      "message": "syntax error, unexpected IDENTIFIER",
      "severity": "error"
    }
  ],
  "message": "Syntax errors found"
}
```

#### Test 2.3: Empty Source Code

**Tool**: `syntax_check`

**Input Arguments**:
```json
{
  "source_code": ""
}
```

**Expected Response**:
```json
{
  "success": false,
  "valid": false,
  "error": "Empty source code provided"
}
```

### 3. Testing `analyze_code`

#### Test 3.1: Generate Basic Analysis

**Tool**: `analyze_code`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. ANALYSIS-TEST.\n\n       DATA DIVISION.\n       WORKING-STORAGE SECTION.\n       01 COUNTER PIC 9(5) VALUE 0.\n       01 NAME    PIC X(20) VALUE \"John\".\n\n       PROCEDURE DIVISION.\n           DISPLAY \"Name: \" NAME.\n           DISPLAY \"Counter: \" COUNTER.\n           STOP RUN.",
  "options": {
    "listing": true
  }
}
```

**Expected Response**:
```json
{
  "success": true,
  "listing": "... compiler listing ...",
  "has_symbols": false,
  "has_xref": false
}
```

#### Test 3.2: Full Analysis with Symbol Table

**Tool**: `analyze_code`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. FULL-ANALYSIS.\n\n       DATA DIVISION.\n       WORKING-STORAGE SECTION.\n       01 VAR1 PIC 9(5).\n       01 VAR2 PIC X(10).\n\n       PROCEDURE DIVISION.\n           MOVE 12345 TO VAR1.\n           MOVE \"TEST\" TO VAR2.\n           DISPLAY VAR1 VAR2.\n           STOP RUN.",
  "options": {
    "listing": true,
    "symbols": true,
    "xref": true
  }
}
```

**Expected Response**:
```json
{
  "success": true,
  "listing": "... full analysis report ...",
  "symbols": [
    {
      "name": "VAR1",
      "type": "numeric",
      "picture": "9(5)",
      "level": "01"
    },
    {
      "name": "VAR2",
      "type": "alphanumeric",
      "picture": "X(10)",
      "level": "01"
    }
  ],
  "has_symbols": true,
  "has_xref": true
}
```

#### Test 3.3: Cross-Reference Report

**Tool**: `analyze_code`

**Input Arguments**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. XREF-TEST.\n\n       DATA DIVISION.\n       WORKING-STORAGE SECTION.\n       01 COUNTER PIC 9(3) VALUE 0.\n\n       PROCEDURE DIVISION.\n           MOVE 10 TO COUNTER.\n           ADD 5 TO COUNTER.\n           DISPLAY COUNTER.\n           STOP RUN.",
  "options": {
    "xref": true
  }
}
```

**Expected Response**:
```json
{
  "success": true,
  "xref": {
    "COUNTER": {
      "defined": [7],
      "modified": [10, 11],
      "referenced": [12]
    }
  },
  "has_xref": true
}
```

### 4. Testing `batch_compile`

#### Test 4.1: Compile Multiple Valid Files

**Tool**: `batch_compile`

**Input Arguments**:
```json
{
  "files": [
    {
      "name": "prog1.cob",
      "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PROG1.\n       PROCEDURE DIVISION.\n           DISPLAY \"Program 1\".\n           STOP RUN."
    },
    {
      "name": "prog2.cob",
      "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PROG2.\n       PROCEDURE DIVISION.\n           DISPLAY \"Program 2\".\n           STOP RUN."
    },
    {
      "name": "prog3.cob",
      "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PROG3.\n       PROCEDURE DIVISION.\n           DISPLAY \"Program 3\".\n           STOP RUN."
    }
  ],
  "compile_options": ["-fsyntax-only"]
}
```

**Expected Response**:
```json
{
  "success": true,
  "results": [
    {
      "file": "prog1.cob",
      "success": true,
      "message": "Compilation successful"
    },
    {
      "file": "prog2.cob",
      "success": true,
      "message": "Compilation successful"
    },
    {
      "file": "prog3.cob",
      "success": true,
      "message": "Compilation successful"
    }
  ],
  "total": 3,
  "successful": 3,
  "failed": 0
}
```

#### Test 4.2: Batch with Mixed Valid/Invalid Files

**Tool**: `batch_compile`

**Input Arguments**:
```json
{
  "files": [
    {
      "name": "valid.cob",
      "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. VALID.\n       PROCEDURE DIVISION.\n           DISPLAY \"Valid\".\n           STOP RUN."
    },
    {
      "name": "invalid.cob",
      "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. INVALID.\n       PROCEDURE DIVISION.\n           INVALID-COMMAND.\n           STOP RUN."
    }
  ],
  "compile_options": ["-fsyntax-only"],
  "continue_on_error": true
}
```

**Expected Response**:
```json
{
  "success": true,
  "results": [
    {
      "file": "valid.cob",
      "success": true,
      "message": "Compilation successful"
    },
    {
      "file": "invalid.cob",
      "success": false,
      "error": "... error messages ..."
    }
  ],
  "total": 2,
  "successful": 1,
  "failed": 1
}
```

## Test Scenarios

### Scenario 1: First-Time Developer

**Goal**: Validate a simple COBOL program

1. Use `syntax_check` with a hello world program
2. If valid, use `compile_cobol` to create executable
3. Verify compilation success

### Scenario 2: Code Review

**Goal**: Analyze code quality and structure

1. Use `analyze_code` with full analysis options
2. Review symbol table for variable usage
3. Check cross-reference for unused variables
4. Review listing for potential issues

### Scenario 3: Batch Processing

**Goal**: Compile multiple COBOL files

1. Use `batch_compile` with multiple source files
2. Review results for each file
3. Identify and fix failing files
4. Re-run batch compilation

### Scenario 4: Error Diagnosis

**Goal**: Debug compilation errors

1. Use `syntax_check` to identify syntax errors
2. Review error messages with line numbers
3. Fix errors in source code
4. Verify with another syntax check
5. Compile with `compile_cobol`

### Scenario 5: Migration Testing

**Goal**: Test legacy COBOL code

1. Use `analyze_code` to understand code structure
2. Use `syntax_check` to identify compatibility issues
3. Use `compile_cobol` with different compiler options
4. Review warnings and errors

## Troubleshooting

### Inspector Cannot Connect

**Problem**: "Connection failed" or "Server not responding"

**Solutions**:
1. Verify server is running: `ps aux | grep gnucobol`
2. Check Python path in inspector configuration
3. Ensure virtual environment is activated
4. Try absolute paths instead of relative paths

### Tools Not Appearing

**Problem**: No tools shown in inspector sidebar

**Solutions**:
1. Verify server implements `@app.tool()` decorators
2. Check server logs for initialization errors
3. Restart inspector and server
4. Clear browser cache

### Compilation Errors

**Problem**: Unexpected compilation failures

**Solutions**:
1. Verify GnuCOBOL is installed: `cobc --version`
2. Test compilation manually: `echo "..." | cobc -fsyntax-only -`
3. Check COBOL source formatting (column positions)
4. Review error messages in server logs

### Unicode/Encoding Issues

**Problem**: Characters appear garbled

**Solutions**:
1. Ensure source code is UTF-8 encoded
2. Check locale settings: `locale`
3. Use ASCII characters in COBOL for compatibility

### Timeout Errors

**Problem**: "Operation timed out"

**Solutions**:
1. Reduce complexity of COBOL code
2. Increase timeout in server configuration
3. Check system resources (CPU, memory)
4. Test with simpler programs first

## Advanced Testing

### Performance Testing

Test server performance with varying load:

```javascript
// Use inspector console or custom script
const results = [];
for (let i = 0; i < 100; i++) {
  const start = Date.now();
  const result = await callTool('syntax_check', {
    source_code: generateCobolProgram(i)
  });
  results.push({
    iteration: i,
    duration: Date.now() - start,
    success: result.success
  });
}
console.table(results);
```

### Stress Testing

Test with large COBOL programs:

```json
{
  "source_code": "... 10,000+ lines of COBOL ..."
}
```

### Edge Cases

Test boundary conditions:
- Empty source code
- Maximum length source code
- Special characters
- Unicode characters
- Extremely nested structures
- Very long variable names

### Integration Testing

Test with real COBOL projects:
1. Clone a COBOL repository
2. Use `batch_compile` on all `.cob` files
3. Review compilation results
4. Verify error reporting

## Validation Checklist

Use this checklist to ensure comprehensive testing:

- [ ] All tools appear in inspector
- [ ] Each tool accepts correct input format
- [ ] Valid COBOL compiles successfully
- [ ] Invalid COBOL produces appropriate errors
- [ ] Error messages include line numbers
- [ ] Syntax check is faster than compilation
- [ ] Listing generation includes source code
- [ ] Symbol table shows all variables
- [ ] Cross-reference tracks variable usage
- [ ] Batch compilation handles multiple files
- [ ] Batch compilation continues on error (if configured)
- [ ] Empty input handled gracefully
- [ ] Large programs process successfully
- [ ] Unicode characters don't crash server
- [ ] Timeouts work as expected
- [ ] Response format is consistent
- [ ] JSON responses are well-formed

## Best Practices

1. **Start Simple**: Begin with hello world, then increase complexity
2. **Test Incrementally**: Test each tool individually before combining
3. **Use Sample Files**: Leverage the `tests/sample_cobol/` directory
4. **Document Issues**: Record unexpected behavior for debugging
5. **Version Control**: Track changes to test cases
6. **Automate**: Create scripts for repetitive tests
7. **Monitor Resources**: Watch CPU and memory usage during tests
8. **Review Logs**: Check server logs for detailed error information

## Next Steps

After completing MCP Inspector testing:
1. ✅ Document any issues found
2. ✅ Create bug reports with reproducible test cases
3. ✅ Test with real-world COBOL projects
4. ✅ Integrate with Claude Desktop or other MCP clients
5. ✅ Performance tune based on test results
6. ✅ Add new test scenarios based on user feedback

## Resources

- [MCP Inspector Documentation](https://modelcontextprotocol.io/docs/tools/inspector)
- [GnuCOBOL Documentation](https://gnucobol.sourceforge.io/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Sample COBOL Programs](./sample_cobol/)

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review server logs
3. Test with sample COBOL files
4. Verify GnuCOBOL installation
5. Check MCP Inspector version compatibility

---

**Happy Testing!** 🧪
