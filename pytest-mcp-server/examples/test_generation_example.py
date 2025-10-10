#!/usr/bin/env python3
"""
Test Generation Example for Pytest MCP Server

This example demonstrates how to use the test generation tools
to analyze code, generate tests, and improve coverage.
"""

import json
import requests
from pathlib import Path

# Configuration
SERVER_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def call_mcp_tool(tool_name: str, data: dict) -> dict:
    """Call an MCP tool and return the response."""
    url = f"{SERVER_URL}/tools/{tool_name}"
    try:
        response = requests.post(url, headers=HEADERS, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling {tool_name}: {e}")
        return {"success": False, "error": str(e)}

def example_code_analysis():
    """Example 1: Analyze code for testing opportunities."""
    print("=" * 60)
    print("EXAMPLE 1: Code Analysis for Test Generation")
    print("=" * 60)

    # Sample Python code to analyze
    sample_code = '''
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")

    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, name: str, price: float, quantity: int = 1):
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        self.items.append({
            "name": name,
            "price": price,
            "quantity": quantity
        })

    def get_total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items)

    def clear(self):
        self.items = []
'''

    # Analyze the code
    response = call_mcp_tool("analyze_code_for_testing", {
        "source_code": sample_code
    })

    if response.get("success"):
        analysis = response["analysis"]
        print(f"File analyzed: {analysis.get('file_path', 'inline code')}")
        print(f"Functions found: {len(analysis['functions'])}")
        print(f"Classes found: {len(analysis['classes'])}")
        print(f"Complexity score: {analysis['complexity_score']}")

        print("\nRecommendations:")
        for rec in analysis.get("recommendations", []):
            print(f"  - {rec}")

        print("\nFunctions discovered:")
        for func in analysis["functions"]:
            print(f"  - {func['name']} (complexity: {func['complexity']})")

        print("\nClasses discovered:")
        for cls in analysis["classes"]:
            print(f"  - {cls['name']} ({len(cls['methods'])} methods)")
    else:
        print(f"Analysis failed: {response.get('error')}")

def example_unit_test_generation():
    """Example 2: Generate unit tests for a function."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Unit Test Generation")
    print("=" * 60)

    # Function to generate tests for
    function_code = '''
def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
'''

    # Generate tests
    response = call_mcp_tool("generate_unit_tests", {
        "source_code": function_code,
        "function_name": "validate_email",
        "framework": "pytest",
        "include_mocks": False,
        "include_integration": False
    })

    if response.get("success"):
        tests = response["tests"]
        print(f"Generated {len(tests)} test cases:")

        for i, test in enumerate(tests, 1):
            print(f"\n{i}. {test['name']}")
            print(f"   Type: {test['test_type']}")
            print(f"   Priority: {test['priority']}")
            print(f"   Description: {test['description']}")
            print("   Code:")
            print("   " + "\n   ".join(test['test_code'].split('\n')))
    else:
        print(f"Test generation failed: {response.get('error')}")

def example_test_case_suggestions():
    """Example 3: Get test case suggestions."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Test Case Suggestions")
    print("=" * 60)

    complex_function = '''
def process_order(order_data: dict, user_id: int, apply_discount: bool = False) -> dict:
    """Process customer order with validation and calculations."""
    if not order_data or not isinstance(order_data, dict):
        raise ValueError("Order data must be a non-empty dictionary")

    if "items" not in order_data or not order_data["items"]:
        raise ValueError("Order must contain items")

    total = 0
    for item in order_data["items"]:
        if not all(key in item for key in ["name", "price", "quantity"]):
            raise ValueError("Each item must have name, price, and quantity")

        if item["price"] <= 0 or item["quantity"] <= 0:
            raise ValueError("Price and quantity must be positive")

        total += item["price"] * item["quantity"]

    if apply_discount and total > 100:
        total *= 0.9  # 10% discount for orders over $100

    return {
        "user_id": user_id,
        "total": round(total, 2),
        "status": "processed",
        "discount_applied": apply_discount and total > 100
    }
'''

    response = call_mcp_tool("suggest_test_cases", {
        "source_code": complex_function,
        "function_name": "process_order"
    })

    if response.get("success"):
        suggestions = response["suggestions"]
        print(f"Found {len(suggestions)} test case suggestions:")

        # Group by test type
        by_type = {}
        for suggestion in suggestions:
            test_type = suggestion["test_type"]
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(suggestion)

        for test_type, tests in by_type.items():
            print(f"\n{test_type.upper()} TESTS:")
            for test in tests:
                print(f"  - {test['name']}")
                print(f"    {test['description']} (Priority: {test['priority']})")
    else:
        print(f"Suggestion failed: {response.get('error')}")

def example_test_file_generation():
    """Example 4: Generate a complete test file."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Complete Test File Generation")
    print("=" * 60)

    # Source code for a utility module
    utility_code = '''
class MathUtils:
    """Mathematical utility functions."""

    @staticmethod
    def fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n < 0:
            raise ValueError("n must be non-negative")
        if n <= 1:
            return n
        return MathUtils.fibonacci(n - 1) + MathUtils.fibonacci(n - 2)

    @staticmethod
    def is_prime(n: int) -> bool:
        """Check if number is prime."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False

        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor."""
        while b:
            a, b = b, a % b
        return abs(a)

def format_number(num: float, precision: int = 2) -> str:
    """Format number with specified precision."""
    if not isinstance(num, (int, float)):
        raise TypeError("Number must be int or float")
    if precision < 0:
        raise ValueError("Precision must be non-negative")

    return f"{num:.{precision}f}"
'''

    response = call_mcp_tool("generate_test_file", {
        "source_code": utility_code,
        "framework": "pytest",
        "include_mocks": True,
        "include_integration": False
    })

    if response.get("success"):
        test_file = response["test_file"]
        print(f"Generated test file: {test_file['file_name']}")
        print(f"Framework: {test_file['framework']}")
        print(f"Test count: {test_file['test_count']}")
        print(f"Estimated coverage: {test_file['estimated_coverage']:.1f}%")
        print(f"Estimated runtime: {test_file['estimated_runtime']:.2f}s")

        print(f"\nImports required:")
        for imp in test_file["imports"]:
            print(f"  {imp}")

        print("\nGenerated test code preview (first 20 lines):")
        lines = test_file["test_code"].split('\n')
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:2}: {line}")

        if len(lines) > 20:
            print(f"... and {len(lines) - 20} more lines")
    else:
        print(f"Test file generation failed: {response.get('error')}")

def example_coverage_analysis():
    """Example 5: Analyze test coverage (simulated)."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Test Coverage Analysis")
    print("=" * 60)

    # This would normally use real coverage data
    print("Note: This example uses simulated coverage data.")
    print("In real usage, you would:")
    print("1. Run: pytest --cov=src --cov-report=json")
    print("2. Use the generated coverage.json file")

    # Simulate coverage analysis
    response = call_mcp_tool("analyze_test_coverage", {
        "source_dir": "/app/src",
        "test_dir": "/app/tests"
    })

    # This will likely fail without real coverage data, but demonstrates the concept
    if response.get("success"):
        if "coverage_reports" in response:
            reports = response["coverage_reports"]
            print(f"Analyzed {len(reports)} files:")

            for report in reports:
                print(f"\nFile: {report['file_path']}")
                print(f"  Coverage: {report['coverage_percentage']:.1f}%")
                print(f"  Lines: {report['covered_lines']}/{report['total_lines']}")
                if report.get("uncovered_functions"):
                    print(f"  Uncovered functions: {', '.join(report['uncovered_functions'])}")

        if "improvement_plan" in response:
            plan = response["improvement_plan"]
            print(f"\nImprovement Plan:")
            print(f"  Current coverage: {plan['current_coverage']:.1f}%")
            print(f"  Target coverage: {plan['target_coverage']:.1f}%")
            print(f"  Tests needed: {plan['estimated_tests_needed']}")

            if plan.get("priority_actions"):
                print("  Priority actions:")
                for action in plan["priority_actions"]:
                    print(f"    - {action['action']} ({action['impact']})")
    else:
        print(f"Coverage analysis result: {response.get('error', 'No coverage data available')}")
        print("This is expected in this demo environment.")

def main():
    """Run all test generation examples."""
    print("Pytest MCP Server - Test Generation Examples")
    print("=" * 60)
    print("Make sure the MCP server is running at http://localhost:8000")
    print()

    try:
        # Check server connectivity
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not accessible. Please start the Docker container:")
            print("   docker-compose up pytest-mcp-server")
            return
        print("✅ Server is running and accessible")
        print()

    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please start the Docker container:")
        print("   docker-compose up pytest-mcp-server")
        return

    # Run all examples
    try:
        example_code_analysis()
        example_unit_test_generation()
        example_test_case_suggestions()
        example_test_file_generation()
        example_coverage_analysis()

        print("\n" + "=" * 60)
        print("🎉 All test generation examples completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Try the MCP Inspector at http://localhost:5173")
        print("2. Use your own code with these tools")
        print("3. Integrate with your development workflow")
        print("4. See README.md for complete tool documentation")

    except KeyboardInterrupt:
        print("\n\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()