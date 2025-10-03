#!/usr/bin/env python3
"""
Basic Usage Examples for Pytest MCP Server Test Generation Tools

This example shows simple usage patterns for each test generation tool.
"""

import json
import requests

# Server configuration
SERVER_URL = "http://localhost:8000"

def analyze_simple_function():
    """Example: Analyze a simple function for testing opportunities."""
    code = """
def add_numbers(a: int, b: int) -> int:
    \"\"\"Add two integers.\"\"\"
    return a + b
    """

    response = requests.post(f"{SERVER_URL}/tools/analyze_code_for_testing",
                           json={"source_code": code})

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            analysis = result["analysis"]
            print("✅ Code Analysis Results:")
            print(f"   Functions: {len(analysis['functions'])}")
            print(f"   Complexity: {analysis['complexity_score']}")
            print(f"   Recommendations: {len(analysis['recommendations'])}")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
    else:
        print(f"❌ Request failed: {response.status_code}")

def generate_simple_tests():
    """Example: Generate tests for a function with error handling."""
    code = """
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
    """

    response = requests.post(f"{SERVER_URL}/tools/generate_unit_tests",
                           json={
                               "source_code": code,
                               "function_name": "divide",
                               "framework": "pytest"
                           })

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            tests = result["tests"]
            print(f"✅ Generated {len(tests)} tests:")
            for test in tests[:2]:  # Show first 2 tests
                print(f"   - {test['name']} ({test['test_type']})")
        else:
            print(f"❌ Test generation failed: {result.get('error')}")
    else:
        print(f"❌ Request failed: {response.status_code}")

def suggest_test_cases():
    """Example: Get test case suggestions for a validation function."""
    code = """
def validate_age(age: int) -> bool:
    return 0 <= age <= 150
    """

    response = requests.post(f"{SERVER_URL}/tools/suggest_test_cases",
                           json={
                               "source_code": code,
                               "function_name": "validate_age"
                           })

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            suggestions = result["suggestions"]
            print(f"✅ Found {len(suggestions)} test suggestions:")
            for suggestion in suggestions[:3]:  # Show first 3
                print(f"   - {suggestion['name']} ({suggestion['priority']} priority)")
        else:
            print(f"❌ Suggestion failed: {result.get('error')}")
    else:
        print(f"❌ Request failed: {response.status_code}")

def generate_test_file_example():
    """Example: Generate a complete test file for a simple class."""
    code = """
class Calculator:
    def add(self, x: int, y: int) -> int:
        return x + y

    def subtract(self, x: int, y: int) -> int:
        return x - y
    """

    response = requests.post(f"{SERVER_URL}/tools/generate_test_file",
                           json={
                               "source_code": code,
                               "framework": "pytest"
                           })

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            test_file = result["test_file"]
            print("✅ Test file generated:")
            print(f"   File: {test_file['file_name']}")
            print(f"   Tests: {test_file['test_count']}")
            print(f"   Coverage: {test_file.get('estimated_coverage', 0):.1f}%")
        else:
            print(f"❌ File generation failed: {result.get('error')}")
    else:
        print(f"❌ Request failed: {response.status_code}")

if __name__ == "__main__":
    print("Pytest MCP Server - Basic Usage Examples")
    print("=" * 50)

    try:
        # Test server connectivity
        health = requests.get(f"{SERVER_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ Server is running\n")
        else:
            print("❌ Server not healthy")
            exit(1)

        # Run examples
        print("1. Analyzing code for testing opportunities...")
        analyze_simple_function()

        print("\n2. Generating unit tests...")
        generate_simple_tests()

        print("\n3. Suggesting test cases...")
        suggest_test_cases()

        print("\n4. Generating test file...")
        generate_test_file_example()

        print("\n🎉 Basic examples completed!")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start with:")
        print("   docker-compose up pytest-mcp-server")
    except Exception as e:
        print(f"❌ Error: {e}")