"""
Code analysis for test generation.
"""

import ast
import inspect
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .models import TestCase, TestOutcome


@dataclass
class FunctionInfo:
    """Information about a function for test generation."""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    return_annotation: Optional[str]
    source_lines: tuple
    complexity: int
    is_async: bool
    is_method: bool
    class_name: Optional[str]


@dataclass
class ClassInfo:
    """Information about a class for test generation."""
    name: str
    docstring: Optional[str]
    methods: List[FunctionInfo]
    attributes: List[str]
    inheritance: List[str]
    source_lines: tuple


@dataclass
class CodeAnalysis:
    """Complete code analysis result."""
    file_path: str
    imports: List[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    complexity_score: int
    test_recommendations: List[str]


class CodeAnalyzer:
    """Analyzes Python code for test generation."""

    def __init__(self):
        """Initialize the code analyzer."""
        self.complexity_weights = {
            ast.If: 1,
            ast.For: 2,
            ast.While: 2,
            ast.Try: 1,
            ast.ExceptHandler: 1,
            ast.With: 1,
            ast.Assert: 1,
        }

    def analyze_file(self, file_path: Union[str, Path]) -> CodeAnalysis:
        """Analyze a Python file for test generation opportunities."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        # Analyze components
        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree, source_code)
        classes = self._extract_classes(tree, source_code)

        # Calculate complexity
        complexity_score = sum(func.complexity for func in functions)
        complexity_score += sum(sum(method.complexity for method in cls.methods) for cls in classes)

        # Generate recommendations
        recommendations = self._generate_recommendations(functions, classes)

        return CodeAnalysis(
            file_path=str(file_path),
            imports=imports,
            functions=functions,
            classes=classes,
            complexity_score=complexity_score,
            test_recommendations=recommendations
        )

    def analyze_function(self, source_code: str, function_name: Optional[str] = None) -> List[FunctionInfo]:
        """Analyze a specific function or code snippet."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

        functions = self._extract_functions(tree, source_code)

        if function_name:
            functions = [f for f in functions if f.name == function_name]
            if not functions:
                raise ValueError(f"Function '{function_name}' not found in source code")

        return functions

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")

        return imports

    def _extract_functions(self, tree: ast.AST, source_code: str) -> List[FunctionInfo]:
        """Extract function information from AST."""
        functions = []
        source_lines = source_code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip if it's a method (inside a class)
                parent_classes = [n for n in ast.walk(tree)
                                if isinstance(n, ast.ClassDef) and any(
                                    isinstance(child, ast.FunctionDef) and child.name == node.name
                                    for child in ast.walk(n)
                                )]

                if parent_classes:
                    continue  # Will be handled in class extraction

                func_info = self._analyze_function_node(node, source_lines)
                functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST, source_code: str) -> List[ClassInfo]:
        """Extract class information from AST."""
        classes = []
        source_lines = source_code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class_node(node, source_lines)
                classes.append(class_info)

        return classes

    def _analyze_function_node(self, node: ast.FunctionDef, source_lines: List[str]) -> FunctionInfo:
        """Analyze a function AST node."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": None
            }
            parameters.append(param_info)

        # Add defaults
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                param_idx = len(parameters) - len(defaults) + i
                if param_idx >= 0:
                    parameters[param_idx]["default"] = ast.unparse(default)

        # Calculate complexity
        complexity = self._calculate_complexity(node)

        # Extract signature
        signature = self._build_signature(node)

        return FunctionInfo(
            name=node.name,
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_annotation=ast.unparse(node.returns) if node.returns else None,
            source_lines=(node.lineno, node.end_lineno or node.lineno),
            complexity=complexity,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=False,
            class_name=None
        )

    def _analyze_class_node(self, node: ast.ClassDef, source_lines: List[str]) -> ClassInfo:
        """Analyze a class AST node."""
        methods = []
        attributes = []

        # Extract methods
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                method_info = self._analyze_function_node(child, source_lines)
                method_info.is_method = True
                method_info.class_name = node.name
                methods.append(method_info)
            elif isinstance(child, ast.Assign):
                # Extract class attributes
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Extract inheritance
        inheritance = [ast.unparse(base) for base in node.bases]

        return ClassInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            methods=methods,
            attributes=attributes,
            inheritance=inheritance,
            source_lines=(node.lineno, node.end_lineno or node.lineno)
        )

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            complexity += self.complexity_weights.get(type(child), 0)

        return complexity

    def _build_signature(self, node: ast.FunctionDef) -> str:
        """Build function signature string."""
        parts = [node.name, "("]

        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Add defaults
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                arg_idx = len(args) - len(defaults) + i
                if arg_idx >= 0:
                    args[arg_idx] += f" = {ast.unparse(default)}"

        parts.append(", ".join(args))
        parts.append(")")

        if node.returns:
            parts.append(f" -> {ast.unparse(node.returns)}")

        return "".join(parts)

    def _generate_recommendations(self, functions: List[FunctionInfo], classes: List[ClassInfo]) -> List[str]:
        """Generate testing recommendations based on code analysis."""
        recommendations = []

        # Function-based recommendations
        for func in functions:
            if func.complexity > 5:
                recommendations.append(f"Function '{func.name}' has high complexity ({func.complexity}). Consider comprehensive edge case testing.")

            if not func.docstring:
                recommendations.append(f"Function '{func.name}' lacks documentation. Tests can help clarify expected behavior.")

            if len(func.parameters) > 4:
                recommendations.append(f"Function '{func.name}' has many parameters. Test parameter combinations and validation.")

            if func.return_annotation:
                recommendations.append(f"Function '{func.name}' has return type annotation. Test return value types and constraints.")

        # Class-based recommendations
        for cls in classes:
            if len(cls.methods) > 10:
                recommendations.append(f"Class '{cls.name}' has many methods. Consider integration tests for method interactions.")

            if cls.inheritance:
                recommendations.append(f"Class '{cls.name}' uses inheritance. Test superclass method overrides and super() calls.")

            init_methods = [m for m in cls.methods if m.name == "__init__"]
            if init_methods and len(init_methods[0].parameters) > 3:
                recommendations.append(f"Class '{cls.name}' constructor has many parameters. Test object initialization scenarios.")

        # General recommendations
        if len(functions) + sum(len(cls.methods) for cls in classes) > 20:
            recommendations.append("Large codebase detected. Consider organizing tests into multiple files and using fixtures.")

        return recommendations

    def suggest_test_cases(self, func_info: FunctionInfo) -> List[Dict[str, Any]]:
        """Suggest test cases for a specific function."""
        test_cases = []

        # Basic happy path test
        test_cases.append({
            "name": f"test_{func_info.name}_happy_path",
            "description": "Test normal operation with valid inputs",
            "test_type": "happy_path",
            "priority": "high"
        })

        # Edge cases based on parameters
        for param in func_info.parameters:
            param_name = param["name"]

            # Skip 'self' parameter
            if param_name == "self":
                continue

            annotation = param.get("annotation", "").lower()

            if "int" in annotation or "float" in annotation:
                test_cases.extend([
                    {
                        "name": f"test_{func_info.name}_zero_{param_name}",
                        "description": f"Test with zero value for {param_name}",
                        "test_type": "edge_case",
                        "priority": "medium"
                    },
                    {
                        "name": f"test_{func_info.name}_negative_{param_name}",
                        "description": f"Test with negative value for {param_name}",
                        "test_type": "edge_case",
                        "priority": "medium"
                    }
                ])

            elif "str" in annotation:
                test_cases.extend([
                    {
                        "name": f"test_{func_info.name}_empty_{param_name}",
                        "description": f"Test with empty string for {param_name}",
                        "test_type": "edge_case",
                        "priority": "medium"
                    },
                    {
                        "name": f"test_{func_info.name}_none_{param_name}",
                        "description": f"Test with None value for {param_name}",
                        "test_type": "error_case",
                        "priority": "high"
                    }
                ])

            elif "list" in annotation:
                test_cases.extend([
                    {
                        "name": f"test_{func_info.name}_empty_list_{param_name}",
                        "description": f"Test with empty list for {param_name}",
                        "test_type": "edge_case",
                        "priority": "medium"
                    }
                ])

        # Error handling tests
        if func_info.complexity > 3:
            test_cases.append({
                "name": f"test_{func_info.name}_error_handling",
                "description": "Test error conditions and exception handling",
                "test_type": "error_case",
                "priority": "high"
            })

        # Performance test for complex functions
        if func_info.complexity > 7:
            test_cases.append({
                "name": f"test_{func_info.name}_performance",
                "description": "Test function performance with large inputs",
                "test_type": "performance",
                "priority": "low"
            })

        return test_cases