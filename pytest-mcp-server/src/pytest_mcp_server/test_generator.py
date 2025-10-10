"""
Test generation engine for creating unit tests.
"""

import ast
import inspect
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .code_analyzer import FunctionInfo, ClassInfo, CodeAnalysis


@dataclass
class GeneratedTest:
    """A generated test case."""
    name: str
    description: str
    test_code: str
    test_type: str  # happy_path, edge_case, error_case, performance
    priority: str   # high, medium, low
    imports: List[str]
    fixtures: List[str]


@dataclass
class TestFile:
    """A complete test file."""
    file_name: str
    imports: List[str]
    fixtures: List[str]
    test_cases: List[GeneratedTest]
    setup_code: Optional[str]
    teardown_code: Optional[str]


class TestGenerator:
    """Generates unit tests from code analysis."""

    def __init__(self):
        """Initialize the test generator."""
        self.test_frameworks = {
            "pytest": {
                "imports": ["import pytest"],
                "assertion": "assert",
                "fixture_decorator": "@pytest.fixture",
                "parametrize_decorator": "@pytest.mark.parametrize",
                "raises": "pytest.raises"
            },
            "unittest": {
                "imports": ["import unittest"],
                "assertion": "self.assertEqual",
                "fixture_decorator": "def setUp(self)",
                "parametrize_decorator": "",
                "raises": "self.assertRaises"
            }
        }

    def generate_tests_for_function(
        self,
        func_info: FunctionInfo,
        framework: str = "pytest",
        include_mocks: bool = True
    ) -> List[GeneratedTest]:
        """Generate test cases for a specific function."""
        if framework not in self.test_frameworks:
            raise ValueError(f"Unsupported framework: {framework}. Use: {list(self.test_frameworks.keys())}")

        tests = []
        fw = self.test_frameworks[framework]

        # Generate basic happy path test
        happy_path_test = self._generate_happy_path_test(func_info, fw)
        tests.append(happy_path_test)

        # Generate edge case tests
        edge_tests = self._generate_edge_case_tests(func_info, fw)
        tests.extend(edge_tests)

        # Generate error handling tests
        error_tests = self._generate_error_tests(func_info, fw)
        tests.extend(error_tests)

        # Generate parametrized tests if multiple similar cases
        param_tests = self._generate_parametrized_tests(func_info, fw)
        tests.extend(param_tests)

        # Generate mock-based tests if requested
        if include_mocks:
            mock_tests = self._generate_mock_tests(func_info, fw)
            tests.extend(mock_tests)

        return tests

    def generate_tests_for_class(
        self,
        class_info: ClassInfo,
        framework: str = "pytest",
        include_integration: bool = True
    ) -> List[GeneratedTest]:
        """Generate test cases for a class."""
        tests = []
        fw = self.test_frameworks[framework]

        # Generate constructor tests
        init_method = next((m for m in class_info.methods if m.name == "__init__"), None)
        if init_method:
            init_tests = self._generate_init_tests(class_info, init_method, fw)
            tests.extend(init_tests)

        # Generate method tests
        for method in class_info.methods:
            if method.name.startswith("__") and method.name != "__init__":
                continue  # Skip magic methods except __init__

            method_tests = self.generate_tests_for_function(method, framework, include_mocks=False)
            # Adapt method tests to work with class instances
            for test in method_tests:
                test.test_code = self._adapt_method_test(test.test_code, class_info.name, method)
                test.name = f"test_{class_info.name.lower()}_{test.name[5:]}"  # Remove 'test_' prefix and add class

            tests.extend(method_tests)

        # Generate integration tests if requested
        if include_integration and len(class_info.methods) > 2:
            integration_tests = self._generate_integration_tests(class_info, fw)
            tests.extend(integration_tests)

        return tests

    def generate_test_file(
        self,
        analysis: CodeAnalysis,
        framework: str = "pytest",
        output_path: Optional[str] = None
    ) -> TestFile:
        """Generate a complete test file from code analysis."""
        fw = self.test_frameworks[framework]
        all_tests = []
        all_imports = set(fw["imports"])
        all_fixtures = []

        # Generate tests for functions
        for func in analysis.functions:
            func_tests = self.generate_tests_for_function(func, framework)
            all_tests.extend(func_tests)

        # Generate tests for classes
        for cls in analysis.classes:
            class_tests = self.generate_tests_for_class(cls, framework)
            all_tests.extend(class_tests)

        # Collect imports and fixtures
        for test in all_tests:
            all_imports.update(test.imports)
            all_fixtures.extend(test.fixtures)

        # Add common testing imports
        all_imports.add("from unittest.mock import Mock, patch, MagicMock")
        if framework == "pytest":
            all_imports.add("import pytest")

        # Determine output file name
        if output_path:
            file_name = output_path
        else:
            source_path = Path(analysis.file_path)
            file_name = f"test_{source_path.stem}.py"

        # Generate setup/teardown if needed
        setup_code = self._generate_setup_code(analysis, framework)
        teardown_code = None

        return TestFile(
            file_name=file_name,
            imports=sorted(list(all_imports)),
            fixtures=list(set(all_fixtures)),
            test_cases=all_tests,
            setup_code=setup_code,
            teardown_code=teardown_code
        )

    def _generate_happy_path_test(self, func_info: FunctionInfo, fw: Dict[str, str]) -> GeneratedTest:
        """Generate a happy path test case."""
        test_name = f"test_{func_info.name}_success"

        # Generate test parameters
        test_params = self._generate_test_parameters(func_info.parameters, "happy")

        # Generate function call
        if func_info.is_method and not func_info.is_async:
            call_code = f"result = instance.{func_info.name}({test_params})"
            setup_code = f"    instance = {func_info.class_name}()" if func_info.class_name else ""
        else:
            call_code = f"result = {func_info.name}({test_params})"
            setup_code = ""

        # Generate assertion
        if func_info.return_annotation:
            assertion = f"{fw['assertion']} result is not None"
            if "int" in func_info.return_annotation.lower():
                assertion = f"{fw['assertion']} isinstance(result, int)"
            elif "str" in func_info.return_annotation.lower():
                assertion = f"{fw['assertion']} isinstance(result, str)"
            elif "bool" in func_info.return_annotation.lower():
                assertion = f"{fw['assertion']} isinstance(result, bool)"
        else:
            assertion = f"{fw['assertion']} result is not None"

        test_code = f"""def {test_name}():
    \"\"\"Test {func_info.name} with valid inputs.\"\"\"
{setup_code}
    {call_code}
    {assertion}"""

        return GeneratedTest(
            name=test_name,
            description=f"Test {func_info.name} with valid inputs",
            test_code=test_code,
            test_type="happy_path",
            priority="high",
            imports=[],
            fixtures=[]
        )

    def _generate_edge_case_tests(self, func_info: FunctionInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate edge case test cases."""
        tests = []

        for param in func_info.parameters:
            if param["name"] == "self":
                continue

            annotation = param.get("annotation", "").lower()
            param_name = param["name"]

            # Numeric edge cases
            if "int" in annotation or "float" in annotation:
                tests.append(self._create_edge_test(
                    func_info, fw, f"zero_{param_name}",
                    f"Test {func_info.name} with zero {param_name}",
                    {param_name: "0"}
                ))
                tests.append(self._create_edge_test(
                    func_info, fw, f"negative_{param_name}",
                    f"Test {func_info.name} with negative {param_name}",
                    {param_name: "-1"}
                ))

            # String edge cases
            elif "str" in annotation:
                tests.append(self._create_edge_test(
                    func_info, fw, f"empty_string_{param_name}",
                    f"Test {func_info.name} with empty string {param_name}",
                    {param_name: '""'}
                ))

            # List edge cases
            elif "list" in annotation:
                tests.append(self._create_edge_test(
                    func_info, fw, f"empty_list_{param_name}",
                    f"Test {func_info.name} with empty list {param_name}",
                    {param_name: "[]"}
                ))

        return tests

    def _generate_error_tests(self, func_info: FunctionInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate error handling test cases."""
        tests = []

        # Test None inputs
        for param in func_info.parameters:
            if param["name"] == "self":
                continue

            test_name = f"test_{func_info.name}_none_{param['name']}"
            param_values = self._generate_test_parameters(func_info.parameters, "happy")
            param_values = param_values.replace(f"{param['name']}=", f"{param['name']}=None #")

            if func_info.is_method:
                call_code = f"instance.{func_info.name}({param_values})"
                setup_code = f"    instance = {func_info.class_name}()" if func_info.class_name else ""
            else:
                call_code = f"{func_info.name}({param_values})"
                setup_code = ""

            test_code = f"""def {test_name}():
    \"\"\"Test {func_info.name} with None {param['name']}.\"\"\"
{setup_code}
    with {fw['raises']}((TypeError, ValueError, AttributeError)):
        {call_code}"""

            tests.append(GeneratedTest(
                name=test_name,
                description=f"Test {func_info.name} with None {param['name']}",
                test_code=test_code,
                test_type="error_case",
                priority="medium",
                imports=[],
                fixtures=[]
            ))

        return tests

    def _generate_parametrized_tests(self, func_info: FunctionInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate parametrized test cases."""
        if fw["parametrize_decorator"] and len(func_info.parameters) > 1:
            # Generate a parametrized test for multiple input combinations
            test_name = f"test_{func_info.name}_parametrized"

            param_names = [p["name"] for p in func_info.parameters if p["name"] != "self"]
            if not param_names:
                return []

            test_cases = [
                f"({self._generate_test_values(func_info.parameters, case)})"
                for case in ["happy", "edge1", "edge2"]
            ]

            if func_info.is_method:
                call_code = f"result = instance.{func_info.name}({', '.join(param_names)})"
                setup_code = f"    instance = {func_info.class_name}()" if func_info.class_name else ""
            else:
                call_code = f"result = {func_info.name}({', '.join(param_names)})"
                setup_code = ""

            test_code = f"""{fw['parametrize_decorator']}("{', '.join(param_names)}", [
    {', '.join(test_cases)}
])
def {test_name}({', '.join(param_names)}):
    \"\"\"Test {func_info.name} with various parameter combinations.\"\"\"
{setup_code}
    {call_code}
    {fw['assertion']} result is not None"""

            return [GeneratedTest(
                name=test_name,
                description=f"Test {func_info.name} with various parameter combinations",
                test_code=test_code,
                test_type="parametrized",
                priority="medium",
                imports=[],
                fixtures=[]
            )]

        return []

    def _generate_mock_tests(self, func_info: FunctionInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate mock-based test cases."""
        tests = []

        # If function likely makes external calls, generate mock tests
        if any(keyword in func_info.name.lower()
               for keyword in ["fetch", "get", "post", "request", "call", "send", "load", "save"]):

            test_name = f"test_{func_info.name}_with_mocks"

            test_code = f"""@patch('builtins.open')
@patch('requests.get')
def {test_name}(mock_get, mock_open):
    \"\"\"Test {func_info.name} with mocked dependencies.\"\"\"
    # Setup mocks
    mock_get.return_value.json.return_value = {{'test': 'data'}}
    mock_open.return_value.__enter__.return_value.read.return_value = 'test data'

    # Call function
    result = {func_info.name}({self._generate_test_parameters(func_info.parameters, "happy")})

    # Verify result and calls
    {fw['assertion']} result is not None
    # Add more specific assertions based on expected behavior"""

            tests.append(GeneratedTest(
                name=test_name,
                description=f"Test {func_info.name} with mocked external dependencies",
                test_code=test_code,
                test_type="mock_test",
                priority="medium",
                imports=["from unittest.mock import patch"],
                fixtures=[]
            ))

        return tests

    def _generate_init_tests(self, class_info: ClassInfo, init_method: FunctionInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate constructor test cases."""
        tests = []

        # Basic initialization test
        test_name = f"test_{class_info.name.lower()}_init"
        init_params = self._generate_test_parameters(init_method.parameters, "happy")

        test_code = f"""def {test_name}():
    \"\"\"Test {class_info.name} initialization.\"\"\"
    instance = {class_info.name}({init_params})
    {fw['assertion']} instance is not None
    {fw['assertion']} isinstance(instance, {class_info.name})"""

        tests.append(GeneratedTest(
            name=test_name,
            description=f"Test {class_info.name} initialization",
            test_code=test_code,
            test_type="happy_path",
            priority="high",
            imports=[],
            fixtures=[]
        ))

        return tests

    def _generate_integration_tests(self, class_info: ClassInfo, fw: Dict[str, str]) -> List[GeneratedTest]:
        """Generate integration tests for class methods."""
        test_name = f"test_{class_info.name.lower()}_integration"

        # Find methods that might work together
        public_methods = [m for m in class_info.methods
                         if not m.name.startswith("_") and m.name != "__init__"]

        if len(public_methods) < 2:
            return []

        method_calls = []
        for method in public_methods[:3]:  # Limit to first 3 methods
            params = self._generate_test_parameters(method.parameters, "happy")
            method_calls.append(f"    result_{method.name} = instance.{method.name}({params})")

        test_code = f"""def {test_name}():
    \"\"\"Test integration of {class_info.name} methods.\"\"\"
    instance = {class_info.name}()
{chr(10).join(method_calls)}

    # Verify the integration works
    {fw['assertion']} instance is not None"""

        return [GeneratedTest(
            name=test_name,
            description=f"Test integration of {class_info.name} methods",
            test_code=test_code,
            test_type="integration",
            priority="medium",
            imports=[],
            fixtures=[]
        )]

    def _create_edge_test(self, func_info: FunctionInfo, fw: Dict[str, str],
                         test_suffix: str, description: str, param_overrides: Dict[str, str]) -> GeneratedTest:
        """Create an edge case test."""
        test_name = f"test_{func_info.name}_{test_suffix}"

        # Generate parameters with overrides
        params = []
        for param in func_info.parameters:
            if param["name"] == "self":
                continue

            if param["name"] in param_overrides:
                params.append(f"{param['name']}={param_overrides[param['name']]}")
            else:
                params.append(f"{param['name']}={self._get_default_value(param)}")

        param_str = ", ".join(params)

        if func_info.is_method:
            call_code = f"result = instance.{func_info.name}({param_str})"
            setup_code = f"    instance = {func_info.class_name}()" if func_info.class_name else ""
        else:
            call_code = f"result = {func_info.name}({param_str})"
            setup_code = ""

        test_code = f"""def {test_name}():
    \"\"\"{description}.\"\"\"
{setup_code}
    {call_code}
    {fw['assertion']} result is not None"""

        return GeneratedTest(
            name=test_name,
            description=description,
            test_code=test_code,
            test_type="edge_case",
            priority="medium",
            imports=[],
            fixtures=[]
        )

    def _generate_test_parameters(self, parameters: List[Dict[str, Any]], scenario: str = "happy") -> str:
        """Generate test parameters for different scenarios."""
        params = []

        for param in parameters:
            if param["name"] == "self":
                continue

            value = self._get_test_value(param, scenario)
            params.append(f"{param['name']}={value}")

        return ", ".join(params)

    def _generate_test_values(self, parameters: List[Dict[str, Any]], scenario: str) -> str:
        """Generate test values (without parameter names) for parametrized tests."""
        values = []

        for param in parameters:
            if param["name"] == "self":
                continue

            value = self._get_test_value(param, scenario)
            values.append(value)

        return ", ".join(values)

    def _get_test_value(self, param: Dict[str, Any], scenario: str) -> str:
        """Get appropriate test value for parameter based on scenario."""
        annotation = param.get("annotation", "").lower()
        default = param.get("default")

        if default and scenario == "happy":
            return default

        if "int" in annotation:
            return {"happy": "42", "edge1": "0", "edge2": "-1"}[scenario] if scenario in ["happy", "edge1", "edge2"] else "1"
        elif "float" in annotation:
            return {"happy": "3.14", "edge1": "0.0", "edge2": "-1.0"}[scenario] if scenario in ["happy", "edge1", "edge2"] else "1.0"
        elif "str" in annotation:
            return {"happy": '"test"', "edge1": '""', "edge2": '"long test string"'}[scenario] if scenario in ["happy", "edge1", "edge2"] else '"test"'
        elif "bool" in annotation:
            return {"happy": "True", "edge1": "False", "edge2": "True"}[scenario] if scenario in ["happy", "edge1", "edge2"] else "True"
        elif "list" in annotation:
            return {"happy": "[1, 2, 3]", "edge1": "[]", "edge2": "list(range(100))"}[scenario] if scenario in ["happy", "edge1", "edge2"] else "[1, 2, 3]"
        elif "dict" in annotation:
            return {"happy": '{"key": "value"}', "edge1": "{}", "edge2": '{"a": 1, "b": 2}'}[scenario] if scenario in ["happy", "edge1", "edge2"] else '{"key": "value"}'
        else:
            return "None"

    def _get_default_value(self, param: Dict[str, Any]) -> str:
        """Get default value for parameter."""
        return self._get_test_value(param, "happy")

    def _adapt_method_test(self, test_code: str, class_name: str, method: FunctionInfo) -> str:
        """Adapt a function test to work with class methods."""
        # Replace function call with method call
        old_call = f"{method.name}("
        new_call = f"instance.{method.name}("
        test_code = test_code.replace(old_call, new_call)

        # Add instance creation
        lines = test_code.split('\n')
        for i, line in enumerate(lines):
            if 'def test_' in line:
                lines.insert(i + 2, f"    instance = {class_name}()")
                break

        return '\n'.join(lines)

    def _generate_setup_code(self, analysis: CodeAnalysis, framework: str) -> Optional[str]:
        """Generate setup code for test file."""
        setup_lines = []

        # Add import for the module being tested
        module_path = Path(analysis.file_path)
        module_name = module_path.stem
        setup_lines.append(f"# Import the module under test")
        setup_lines.append(f"from {module_name} import *")
        setup_lines.append("")

        # Add fixtures for classes
        if analysis.classes and framework == "pytest":
            setup_lines.append("# Fixtures for class testing")
            for cls in analysis.classes:
                setup_lines.append(f"@pytest.fixture")
                setup_lines.append(f"def {cls.name.lower()}_instance():")
                setup_lines.append(f'    """Provide {cls.name} instance for testing."""')
                setup_lines.append(f"    return {cls.name}()")
                setup_lines.append("")

        return "\n".join(setup_lines) if setup_lines else None

    def render_test_file(self, test_file: TestFile) -> str:
        """Render a complete test file as string."""
        lines = []

        # Header comment
        lines.append(f'"""')
        lines.append(f'Generated test file: {test_file.file_name}')
        lines.append(f'Generated on: {datetime.now().isoformat()}')
        lines.append(f'"""')
        lines.append('')

        # Imports
        for imp in test_file.imports:
            lines.append(imp)
        lines.append('')

        # Setup code
        if test_file.setup_code:
            lines.append(test_file.setup_code)
            lines.append('')

        # Fixtures
        for fixture in test_file.fixtures:
            lines.append(fixture)
            lines.append('')

        # Test cases
        for i, test in enumerate(test_file.test_cases):
            if i > 0:
                lines.append('')
            lines.append(test.test_code)

        # Teardown code
        if test_file.teardown_code:
            lines.append('')
            lines.append(test_file.teardown_code)

        return '\n'.join(lines)