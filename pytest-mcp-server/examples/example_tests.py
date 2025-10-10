"""
Example test file to demonstrate pytest MCP server functionality.
"""

import pytest
import time
import requests
from typing import List


class TestBasicExamples:
    """Basic test examples for MCP server demonstration."""

    def test_simple_pass(self):
        """A simple passing test."""
        assert 1 + 1 == 2

    def test_simple_fail(self):
        """A simple failing test for failure analysis."""
        assert 1 + 1 == 3, "Math doesn't work as expected"

    def test_with_duration(self):
        """Test that takes some time to complete."""
        time.sleep(0.1)
        assert True

    @pytest.mark.slow
    def test_slow_operation(self):
        """A test marked as slow."""
        time.sleep(0.5)
        result = sum(range(1000))
        assert result == 499500

    @pytest.mark.skip(reason="Demonstrating skipped test")
    def test_skipped_example(self):
        """This test is skipped."""
        assert False  # This won't run


class TestDataProcessing:
    """Tests for data processing functionality."""

    def test_list_processing(self):
        """Test list operations."""
        data = [1, 2, 3, 4, 5]
        result = [x * 2 for x in data]
        expected = [2, 4, 6, 8, 10]
        assert result == expected

    def test_string_manipulation(self):
        """Test string operations."""
        text = "Hello World"
        result = text.lower().replace(" ", "_")
        assert result == "hello_world"

    def test_dictionary_operations(self):
        """Test dictionary operations."""
        data = {"a": 1, "b": 2, "c": 3}
        result = {k: v * 2 for k, v in data.items()}
        expected = {"a": 2, "b": 4, "c": 6}
        assert result == expected


class TestErrorScenarios:
    """Tests that demonstrate various error types for analysis."""

    def test_assertion_error(self):
        """Test that fails with AssertionError."""
        expected = 10
        actual = 5 + 3
        assert actual == expected, f"Expected {expected}, but got {actual}"

    def test_type_error(self):
        """Test that fails with TypeError."""
        result = None
        # This will cause AttributeError, not TypeError, but demonstrates error analysis
        assert result.upper() == "TEST"

    def test_index_error(self):
        """Test that fails with IndexError."""
        data = [1, 2, 3]
        assert data[10] == 1  # Index out of range

    def test_key_error(self):
        """Test that fails with KeyError."""
        data = {"a": 1, "b": 2}
        assert data["nonexistent"] == 1

    def test_value_error(self):
        """Test that fails with ValueError."""
        result = int("not_a_number")
        assert result == 0

    def test_custom_exception(self):
        """Test that fails with custom exception."""

        class CustomError(Exception):
            pass

        raise CustomError("This is a custom error for testing")


class TestWithFixtures:
    """Tests using fixtures to demonstrate test setup."""

    @pytest.fixture
    def sample_data(self):
        """Provide sample data for tests."""
        return {
            "users": [
                {"id": 1, "name": "Alice", "age": 25},
                {"id": 2, "name": "Bob", "age": 30},
                {"id": 3, "name": "Charlie", "age": 35}
            ]
        }

    def test_user_count(self, sample_data):
        """Test user count from fixture."""
        users = sample_data["users"]
        assert len(users) == 3

    def test_user_names(self, sample_data):
        """Test user names extraction."""
        users = sample_data["users"]
        names = [user["name"] for user in users]
        expected = ["Alice", "Bob", "Charlie"]
        assert names == expected

    def test_average_age_calculation(self, sample_data):
        """Test average age calculation - this will fail."""
        users = sample_data["users"]
        ages = [user["age"] for user in users]
        average_age = sum(ages) / len(ages)
        # Intentionally wrong assertion to demonstrate failure analysis
        assert average_age == 25.0, f"Expected average age 25.0, got {average_age}"


@pytest.mark.integration
class TestIntegrationExamples:
    """Integration test examples."""

    @pytest.mark.skip(reason="No external service available for demo")
    def test_api_call(self):
        """Test API call - skipped for demo."""
        response = requests.get("https://httpbin.org/json")
        assert response.status_code == 200
        data = response.json()
        assert "slideshow" in data

    def test_file_operations(self, tmp_path):
        """Test file operations using temporary directory."""
        test_file = tmp_path / "test.txt"
        content = "Hello, MCP Server!"

        # Write content
        test_file.write_text(content)

        # Read and verify
        read_content = test_file.read_text()
        assert read_content == content

    def test_complex_calculation(self):
        """Test complex calculation that might fail."""
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)

        # This will pass
        assert fibonacci(5) == 5

        # This will fail - intentional for demonstration
        assert fibonacci(6) == 7, "Fibonacci calculation error"


@pytest.mark.parametrize("input_val,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
    (5, 24),  # This will fail - should be 25
])
def test_parametrized_square(input_val, expected):
    """Parametrized test for square function."""
    def square(x):
        return x * x

    result = square(input_val)
    assert result == expected, f"Square of {input_val} should be {expected}, got {result}"


class TestEnvironmentFactors:
    """Tests that might be affected by environment factors."""

    def test_platform_dependent(self):
        """Test that might behave differently on different platforms."""
        import platform
        system = platform.system()

        if system == "Windows":
            expected_path_sep = "\\"
        else:
            expected_path_sep = "/"

        import os
        # This might fail if running on unexpected platform
        assert os.path.sep == expected_path_sep

    def test_timing_sensitive(self):
        """Test that might fail due to timing issues."""
        import time
        start = time.time()
        time.sleep(0.05)  # Sleep for 50ms
        end = time.time()

        duration = end - start
        # This might fail due to system load or timing variations
        assert 0.04 <= duration <= 0.06, f"Expected ~0.05s, got {duration:.3f}s"

    def test_resource_dependent(self):
        """Test that might fail due to resource constraints."""
        import psutil

        # Get available memory
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        # This might fail on systems with low memory
        assert available_gb > 1.0, f"Need at least 1GB available memory, got {available_gb:.2f}GB"