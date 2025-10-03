# Test Generation Examples

This directory contains practical examples demonstrating how to use the Pytest MCP Server's test generation tools.

## Prerequisites

1. **Start the MCP Server:**
   ```bash
   docker-compose up pytest-mcp-server
   ```

2. **Install Python dependencies (for running examples):**
   ```bash
   pip install requests
   ```

3. **Verify server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Simple examples showing how to use each test generation tool:

- Code analysis for testing opportunities
- Unit test generation with error handling
- Test case suggestions for validation functions
- Complete test file generation

**Run:**
```bash
cd examples
python basic_usage.py
```

**Expected Output:**
```
Pytest MCP Server - Basic Usage Examples
==================================================
✅ Server is running

1. Analyzing code for testing opportunities...
✅ Code Analysis Results:
   Functions: 1
   Complexity: 1
   Recommendations: 1

2. Generating unit tests...
✅ Generated 3 tests:
   - test_divide_happy_path (happy_path)
   - test_divide_zero_b (error_case)

3. Suggesting test cases...
✅ Found 5 test suggestions:
   - test_validate_age_happy_path (high priority)
   - test_validate_age_zero_age (medium priority)
   - test_validate_age_negative_age (medium priority)

4. Generating test file...
✅ Test file generated:
   File: test_calculator.py
   Tests: 6
   Coverage: 85.0%

🎉 Basic examples completed!
```

### 2. Comprehensive Example (`test_generation_example.py`)

Detailed examples covering all aspects of test generation:

- **Example 1:** Code analysis with complex functions and classes
- **Example 2:** Unit test generation with mocks and frameworks
- **Example 3:** Test case suggestions for complex business logic
- **Example 4:** Complete test file generation with utilities
- **Example 5:** Test coverage analysis and improvement planning

**Run:**
```bash
cd examples
python test_generation_example.py
```

**Features Demonstrated:**
- Function complexity analysis
- Class method testing
- Error condition testing
- Mock integration
- Coverage gap identification
- Test prioritization

## Test Generation Workflow

### Step 1: Analyze Your Code
```python
import requests

response = requests.post("http://localhost:8000/tools/analyze_code_for_testing", json={
    "source_code": "def my_function(x): return x * 2"
})
```

### Step 2: Generate Unit Tests
```python
response = requests.post("http://localhost:8000/tools/generate_unit_tests", json={
    "source_code": "def divide(a, b): return a / b",
    "function_name": "divide",
    "framework": "pytest",
    "include_mocks": True
})
```

### Step 3: Get Test Suggestions
```python
response = requests.post("http://localhost:8000/tools/suggest_test_cases", json={
    "source_code": "def validate_email(email): ...",
    "function_name": "validate_email"
})
```

### Step 4: Generate Complete Test File
```python
response = requests.post("http://localhost:8000/tools/generate_test_file", json={
    "source_code": "class Calculator: ...",
    "framework": "pytest"
})
```

### Step 5: Analyze Coverage
```python
response = requests.post("http://localhost:8000/tools/analyze_test_coverage", json={
    "source_dir": "/src",
    "test_dir": "/tests"
})
```

## Integration with Development Workflow

### 1. Pre-commit Hook
Add test generation to your pre-commit hooks:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Generate tests for new functions
git diff --cached --name-only "*.py" | while read file; do
    curl -X POST http://localhost:8000/tools/analyze_code_for_testing \
         -H "Content-Type: application/json" \
         -d '{"file_path": "'$file'"}' | jq '.analysis.recommendations[]'
done
```

### 2. CI/CD Integration
```yaml
# .github/workflows/tests.yml
- name: Generate Missing Tests
  run: |
    python examples/generate_missing_tests.py
    git add tests/
    git commit -m "Auto-generate missing tests" || true
```

### 3. IDE Integration
Create a VS Code task or vim command:

```json
{
    "label": "Generate Tests",
    "type": "shell",
    "command": "python",
    "args": ["examples/basic_usage.py"],
    "group": "test"
}
```

## Troubleshooting

### Server Not Running
```
❌ Cannot connect to server. Start with:
   docker-compose up pytest-mcp-server
```

**Solution:**
```bash
cd /path/to/pytest-mcp-server
docker-compose up -d pytest-mcp-server
```

### Tool Errors
If a tool returns an error, check the server logs:

```bash
docker-compose logs pytest-mcp-server
```

### Missing Dependencies
Install Python requests library:

```bash
pip install requests
```

## Customization

### Modify Examples
You can modify the examples to work with your own code:

1. Replace the `sample_code` variables with your actual code
2. Update server URL if running on different host/port
3. Adjust test frameworks (pytest/unittest)
4. Configure mock preferences

### Create New Examples
Follow the pattern in existing examples:

1. Import `requests` for HTTP calls
2. Define server URL and headers
3. Create helper function for MCP tool calls
4. Handle errors gracefully
5. Print results in a user-friendly format

## Next Steps

1. **Try with your own code:** Replace example code with your project files
2. **Integrate with CI/CD:** Add test generation to your pipeline
3. **Use MCP Inspector:** Visual tool testing at http://localhost:5173
4. **Customize templates:** Modify test generation templates for your needs
5. **Scale up:** Use for larger codebases with batch processing

## Support

- **Documentation:** See main [README.md](../README.md)
- **MCP Inspector:** http://localhost:5173
- **Server Health:** http://localhost:8000/health
- **Available Tools:** http://localhost:8000/tools

Happy testing! 🧪