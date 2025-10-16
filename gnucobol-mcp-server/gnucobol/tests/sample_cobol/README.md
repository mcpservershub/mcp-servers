# Sample COBOL Programs

This directory contains sample COBOL programs used for testing the GnuCOBOL MCP Server.

## Directory Structure

```
sample_cobol/
├── valid/              # Valid COBOL programs that should compile successfully
└── invalid/            # Invalid COBOL programs for error testing
```

## Valid Programs

### hello.cob
Simple "Hello, World!" program demonstrating basic COBOL structure.
- **Purpose**: Basic syntax validation
- **Features**: IDENTIFICATION DIVISION, PROCEDURE DIVISION, DISPLAY statement
- **Use in tests**: Basic compilation, syntax checking

### calculator.cob
Interactive calculator with arithmetic operations.
- **Purpose**: Test data handling and user input
- **Features**: Working-storage, ACCEPT/DISPLAY, EVALUATE, arithmetic operations
- **Use in tests**: Complex compilation, variable handling, control flow

### file-operations.cob
Sequential file processing demonstration.
- **Purpose**: Test file I/O capabilities
- **Features**: File handling, OPEN/READ/CLOSE, status codes, PERFORM loops
- **Use in tests**: File operations, error handling, iteration

### array-demo.cob
Array and table operations.
- **Purpose**: Test table handling and iteration
- **Features**: OCCURS clause, indexed access, PERFORM VARYING, COMPUTE
- **Use in tests**: Array operations, indexing, calculations

### string-manipulation.cob
String operations and intrinsic functions.
- **Purpose**: Test string handling
- **Features**: STRING statement, UPPER-CASE function, INSPECT
- **Use in tests**: String operations, intrinsic functions

## Invalid Programs

### syntax_error.cob
Contains intentional syntax errors.
- **Errors**: Missing period, invalid commands
- **Use**: Test error detection and reporting

### missing_division.cob
Missing required PROCEDURE DIVISION.
- **Errors**: Incomplete program structure
- **Use**: Test structure validation

### undefined_variable.cob
References undefined variables.
- **Errors**: Undefined identifiers
- **Use**: Test symbol resolution

### type_mismatch.cob
Type mismatches in operations.
- **Errors**: Incompatible data types in operations
- **Use**: Test type checking

### malformed_structure.cob
Structural errors (level numbers, unclosed statements).
- **Errors**: Invalid hierarchical structure, unclosed IF/PERFORM
- **Use**: Test structure parsing

### invalid_picture.cob
Invalid PICTURE clause definitions.
- **Errors**: Malformed PICTURE specifications
- **Use**: Test data definition validation

### missing_period.cob
Missing period terminators throughout.
- **Errors**: Missing statement terminators
- **Use**: Test syntax validation

## Testing with GnuCOBOL

### Compile Valid Programs

```bash
# Hello World
cobc -x valid/hello.cob
./hello

# Calculator
cobc -x valid/calculator.cob
./calculator

# File Operations
cobc -x valid/file-operations.cob
./file-operations

# Array Demo
cobc -x valid/array-demo.cob
./array-demo

# String Manipulation
cobc -x valid/string-manipulation.cob
./string-manipulation
```

### Test Invalid Programs (Should Fail)

```bash
# These should all produce compilation errors
cobc -fsyntax-only invalid/syntax_error.cob
cobc -fsyntax-only invalid/missing_division.cob
cobc -fsyntax-only invalid/undefined_variable.cob
cobc -fsyntax-only invalid/type_mismatch.cob
cobc -fsyntax-only invalid/malformed_structure.cob
cobc -fsyntax-only invalid/invalid_picture.cob
cobc -fsyntax-only invalid/missing_period.cob
```

## Usage in Tests

These samples are used by the test suite in `test_gnucobol_mcp.py`:

```python
# Example: Load valid sample
@pytest.fixture
def sample_valid_hello():
    return (VALID_DIR / "hello.cob").read_text()

# Example: Load invalid sample
@pytest.fixture
def sample_invalid_syntax():
    return (INVALID_DIR / "syntax_error.cob").read_text()
```

## Adding New Samples

When adding new sample programs:

1. **Valid programs**: Add to `valid/` directory
   - Must compile without errors
   - Should demonstrate specific COBOL features
   - Include comments explaining purpose
   - Follow COBOL formatting standards

2. **Invalid programs**: Add to `invalid/` directory
   - Must fail compilation with expected errors
   - Document the intentional errors
   - Name file descriptively (e.g., `missing_end_if.cob`)

3. **Update tests**: Add corresponding test cases in `test_gnucobol_mcp.py`

## COBOL Standards

These samples follow COBOL-85 and COBOL-2002 standards supported by GnuCOBOL.

### Column Formatting
- Columns 1-6: Sequence numbers (optional)
- Column 7: Indicator area (for comments, continuation)
- Columns 8-11: Area A (divisions, sections, paragraphs)
- Columns 12-72: Area B (statements, data definitions)
- Columns 73-80: Identification area (optional)

### Naming Conventions
- Division names: ALL CAPS, end with DIVISION
- Program names: Alphanumeric with hyphens
- Variables: Descriptive, use hyphens not underscores

## License

These sample programs are part of the GnuCOBOL MCP Server test suite and are provided for testing purposes.
