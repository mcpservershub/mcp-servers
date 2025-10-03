"""
Test coverage analysis and recommendations.
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass

from .code_analyzer import CodeAnalysis, FunctionInfo, ClassInfo


@dataclass
class CoverageReport:
    """Coverage analysis report."""
    file_path: str
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    coverage_percentage: float
    uncovered_functions: List[str]
    uncovered_branches: List[str]


@dataclass
class CoverageRecommendation:
    """Recommendation for improving test coverage."""
    type: str  # function, branch, edge_case, integration
    target: str  # Function/class name
    description: str
    priority: str  # high, medium, low
    suggested_tests: List[str]
    code_snippet: Optional[str]


class CoverageAnalyzer:
    """Analyzes test coverage and provides recommendations."""

    def __init__(self):
        """Initialize coverage analyzer."""
        self.coverage_tools = ["coverage", "pytest-cov"]

    def analyze_coverage_from_file(self, coverage_file: str) -> List[CoverageReport]:
        """Analyze coverage from a coverage report file."""
        coverage_path = Path(coverage_file)

        if not coverage_path.exists():
            raise FileNotFoundError(f"Coverage file not found: {coverage_file}")

        if coverage_path.suffix == '.json':
            return self._parse_json_coverage(coverage_file)
        elif coverage_path.suffix == '.xml':
            return self._parse_xml_coverage(coverage_file)
        else:
            # Try to parse as text coverage report
            return self._parse_text_coverage(coverage_file)

    def analyze_code_coverage_gaps(
        self,
        source_analysis: CodeAnalysis,
        existing_tests: Optional[List[str]] = None
    ) -> List[CoverageRecommendation]:
        """Analyze code to identify potential coverage gaps."""
        recommendations = []

        # Analyze functions
        for func in source_analysis.functions:
            func_recommendations = self._analyze_function_coverage(func, existing_tests or [])
            recommendations.extend(func_recommendations)

        # Analyze classes
        for cls in source_analysis.classes:
            class_recommendations = self._analyze_class_coverage(cls, existing_tests or [])
            recommendations.extend(class_recommendations)

        # Analyze complex code patterns
        complex_recommendations = self._analyze_complex_patterns(source_analysis)
        recommendations.extend(complex_recommendations)

        return sorted(recommendations, key=lambda x: self._priority_score(x.priority), reverse=True)

    def suggest_missing_tests(
        self,
        coverage_report: CoverageReport,
        source_analysis: CodeAnalysis
    ) -> List[CoverageRecommendation]:
        """Suggest tests for uncovered code areas."""
        recommendations = []

        # Map uncovered lines to functions/classes
        uncovered_elements = self._map_uncovered_lines_to_elements(
            coverage_report.missing_lines,
            source_analysis
        )

        for element_type, element_name, lines in uncovered_elements:
            if element_type == "function":
                func = next((f for f in source_analysis.functions if f.name == element_name), None)
                if func:
                    recommendations.extend(self._suggest_function_tests(func, lines))

            elif element_type == "class":
                cls = next((c for c in source_analysis.classes if c.name == element_name), None)
                if cls:
                    recommendations.extend(self._suggest_class_tests(cls, lines))

        return recommendations

    def generate_coverage_improvement_plan(
        self,
        coverage_reports: List[CoverageReport],
        target_coverage: float = 90.0
    ) -> Dict[str, Any]:
        """Generate a plan to improve test coverage."""
        plan = {
            "current_coverage": self._calculate_overall_coverage(coverage_reports),
            "target_coverage": target_coverage,
            "files_needing_improvement": [],
            "priority_actions": [],
            "estimated_tests_needed": 0
        }

        for report in coverage_reports:
            if report.coverage_percentage < target_coverage:
                gap = target_coverage - report.coverage_percentage
                tests_needed = int((gap / 100) * len(report.uncovered_functions)) + 1

                plan["files_needing_improvement"].append({
                    "file": report.file_path,
                    "current_coverage": report.coverage_percentage,
                    "gap": gap,
                    "tests_needed": tests_needed,
                    "uncovered_functions": report.uncovered_functions[:5]  # Top 5
                })

                plan["estimated_tests_needed"] += tests_needed

        # Generate priority actions
        all_files = sorted(plan["files_needing_improvement"], key=lambda x: x["gap"], reverse=True)
        for file_info in all_files[:3]:  # Top 3 priorities
            plan["priority_actions"].append({
                "action": f"Add tests for {file_info['file']}",
                "impact": f"Improve coverage by ~{file_info['gap']:.1f}%",
                "tests": file_info["tests_needed"]
            })

        return plan

    def _parse_json_coverage(self, coverage_file: str) -> List[CoverageReport]:
        """Parse JSON coverage report."""
        reports = []

        with open(coverage_file, 'r') as f:
            data = json.load(f)

        files_data = data.get('files', {})
        for file_path, file_data in files_data.items():
            summary = file_data.get('summary', {})
            missing_lines = []

            # Extract missing lines from executed_lines
            executed_lines = file_data.get('executed_lines', [])
            missing_lines_data = file_data.get('missing_lines', [])
            if missing_lines_data:
                missing_lines = missing_lines_data

            coverage_percent = summary.get('percent_covered', 0.0)

            report = CoverageReport(
                file_path=file_path,
                total_lines=summary.get('num_statements', 0),
                covered_lines=summary.get('covered_lines', 0),
                missing_lines=missing_lines,
                coverage_percentage=coverage_percent,
                uncovered_functions=[],  # Would need additional parsing
                uncovered_branches=[]
            )
            reports.append(report)

        return reports

    def _parse_xml_coverage(self, coverage_file: str) -> List[CoverageReport]:
        """Parse XML coverage report."""
        # This would require XML parsing - simplified for now
        reports = []

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            for class_elem in root.findall(".//class"):
                filename = class_elem.get('filename', '')
                lines_covered = int(class_elem.get('lines-covered', 0))
                lines_valid = int(class_elem.get('lines-valid', 0))

                coverage_percent = (lines_covered / lines_valid * 100) if lines_valid > 0 else 0

                report = CoverageReport(
                    file_path=filename,
                    total_lines=lines_valid,
                    covered_lines=lines_covered,
                    missing_lines=[],
                    coverage_percentage=coverage_percent,
                    uncovered_functions=[],
                    uncovered_branches=[]
                )
                reports.append(report)

        except Exception as e:
            raise ValueError(f"Failed to parse XML coverage file: {e}")

        return reports

    def _parse_text_coverage(self, coverage_file: str) -> List[CoverageReport]:
        """Parse text coverage report."""
        reports = []

        with open(coverage_file, 'r') as f:
            lines = f.readlines()

        current_file = None
        for line in lines:
            line = line.strip()

            # Look for file paths and coverage percentages
            if line.endswith('.py') and '%' in line:
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[0]
                    try:
                        coverage_percent = float(parts[-1].rstrip('%'))
                        statements = int(parts[1]) if len(parts) > 1 else 0
                        missing = int(parts[2]) if len(parts) > 2 else 0
                        covered = statements - missing

                        report = CoverageReport(
                            file_path=file_path,
                            total_lines=statements,
                            covered_lines=covered,
                            missing_lines=[],
                            coverage_percentage=coverage_percent,
                            uncovered_functions=[],
                            uncovered_branches=[]
                        )
                        reports.append(report)
                    except (ValueError, IndexError):
                        continue

        return reports

    def _analyze_function_coverage(self, func: FunctionInfo, existing_tests: List[str]) -> List[CoverageRecommendation]:
        """Analyze coverage gaps for a specific function."""
        recommendations = []

        # Check if function has any tests
        func_test_patterns = [
            f"test_{func.name}",
            f"test_{func.name.lower()}",
            func.name
        ]

        has_tests = any(
            any(pattern in test for pattern in func_test_patterns)
            for test in existing_tests
        )

        if not has_tests:
            recommendations.append(CoverageRecommendation(
                type="function",
                target=func.name,
                description=f"Function '{func.name}' has no test coverage",
                priority="high",
                suggested_tests=[f"test_{func.name}_basic_functionality"],
                code_snippet=func.signature
            ))

        # Check for complex functions needing comprehensive testing
        if func.complexity > 5:
            recommendations.append(CoverageRecommendation(
                type="branch",
                target=func.name,
                description=f"Complex function '{func.name}' (complexity: {func.complexity}) needs branch coverage",
                priority="high",
                suggested_tests=[
                    f"test_{func.name}_edge_cases",
                    f"test_{func.name}_error_conditions"
                ],
                code_snippet=func.signature
            ))

        # Check for functions with many parameters
        if len(func.parameters) > 3:
            recommendations.append(CoverageRecommendation(
                type="edge_case",
                target=func.name,
                description=f"Function '{func.name}' with {len(func.parameters)} parameters needs parameter combination testing",
                priority="medium",
                suggested_tests=[f"test_{func.name}_parameter_combinations"],
                code_snippet=func.signature
            ))

        return recommendations

    def _analyze_class_coverage(self, cls: ClassInfo, existing_tests: List[str]) -> List[CoverageRecommendation]:
        """Analyze coverage gaps for a specific class."""
        recommendations = []

        # Check if class has test coverage
        class_test_patterns = [
            f"test_{cls.name}",
            f"test_{cls.name.lower()}",
            f"Test{cls.name}"
        ]

        has_class_tests = any(
            any(pattern in test for pattern in class_test_patterns)
            for test in existing_tests
        )

        if not has_class_tests:
            recommendations.append(CoverageRecommendation(
                type="class",
                target=cls.name,
                description=f"Class '{cls.name}' has no test coverage",
                priority="high",
                suggested_tests=[f"test_{cls.name.lower()}_initialization"],
                code_snippet=f"class {cls.name}"
            ))

        # Check for uncovered methods
        for method in cls.methods:
            if method.name.startswith('_') and method.name != '__init__':
                continue  # Skip private methods

            method_has_tests = any(
                f"test_{method.name}" in test or f"{method.name}" in test
                for test in existing_tests
            )

            if not method_has_tests:
                priority = "high" if method.name == "__init__" else "medium"
                recommendations.append(CoverageRecommendation(
                    type="function",
                    target=f"{cls.name}.{method.name}",
                    description=f"Method '{cls.name}.{method.name}' has no test coverage",
                    priority=priority,
                    suggested_tests=[f"test_{cls.name.lower()}_{method.name}"],
                    code_snippet=method.signature
                ))

        return recommendations

    def _analyze_complex_patterns(self, analysis: CodeAnalysis) -> List[CoverageRecommendation]:
        """Analyze complex code patterns that need special testing attention."""
        recommendations = []

        # Check for exception handling patterns
        # This would require AST analysis of the original source
        if analysis.complexity_score > 20:
            recommendations.append(CoverageRecommendation(
                type="integration",
                target="Module",
                description=f"High complexity module (score: {analysis.complexity_score}) needs integration testing",
                priority="medium",
                suggested_tests=["test_module_integration", "test_error_handling_paths"],
                code_snippet=None
            ))

        return recommendations

    def _map_uncovered_lines_to_elements(
        self,
        missing_lines: List[int],
        analysis: CodeAnalysis
    ) -> List[Tuple[str, str, List[int]]]:
        """Map uncovered lines to specific functions or classes."""
        uncovered_elements = []

        for func in analysis.functions:
            func_lines = list(range(func.source_lines[0], (func.source_lines[1] or func.source_lines[0]) + 1))
            uncovered_in_func = [line for line in missing_lines if line in func_lines]
            if uncovered_in_func:
                uncovered_elements.append(("function", func.name, uncovered_in_func))

        for cls in analysis.classes:
            class_lines = list(range(cls.source_lines[0], (cls.source_lines[1] or cls.source_lines[0]) + 1))
            uncovered_in_class = [line for line in missing_lines if line in class_lines]
            if uncovered_in_class:
                uncovered_elements.append(("class", cls.name, uncovered_in_class))

        return uncovered_elements

    def _suggest_function_tests(self, func: FunctionInfo, uncovered_lines: List[int]) -> List[CoverageRecommendation]:
        """Suggest specific tests for uncovered function lines."""
        recommendations = []

        # Basic test if no coverage at all
        if len(uncovered_lines) > 0:
            recommendations.append(CoverageRecommendation(
                type="function",
                target=func.name,
                description=f"Function '{func.name}' has {len(uncovered_lines)} uncovered lines",
                priority="high",
                suggested_tests=[
                    f"test_{func.name}_basic",
                    f"test_{func.name}_edge_cases"
                ],
                code_snippet=func.signature
            ))

        return recommendations

    def _suggest_class_tests(self, cls: ClassInfo, uncovered_lines: List[int]) -> List[CoverageRecommendation]:
        """Suggest specific tests for uncovered class lines."""
        recommendations = []

        recommendations.append(CoverageRecommendation(
            type="class",
            target=cls.name,
            description=f"Class '{cls.name}' has {len(uncovered_lines)} uncovered lines",
            priority="medium",
            suggested_tests=[
                f"test_{cls.name.lower()}_methods",
                f"test_{cls.name.lower()}_edge_cases"
            ],
            code_snippet=f"class {cls.name}"
        ))

        return recommendations

    def _calculate_overall_coverage(self, reports: List[CoverageReport]) -> float:
        """Calculate overall coverage percentage."""
        if not reports:
            return 0.0

        total_lines = sum(report.total_lines for report in reports)
        covered_lines = sum(report.covered_lines for report in reports)

        return (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score."""
        scores = {"high": 3, "medium": 2, "low": 1}
        return scores.get(priority.lower(), 0)

    def run_coverage_analysis(self, source_dir: str, test_dir: str) -> Dict[str, Any]:
        """Run coverage analysis using pytest-cov."""
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                f"--cov={source_dir}",
                "--cov-report=json:coverage.json",
                "--cov-report=term",
                test_dir
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(source_dir).parent
            )

            # Parse coverage results
            coverage_file = Path(source_dir).parent / "coverage.json"
            if coverage_file.exists():
                reports = self.analyze_coverage_from_file(str(coverage_file))
                return {
                    "success": True,
                    "reports": [report.__dict__ for report in reports],
                    "overall_coverage": self._calculate_overall_coverage(reports),
                    "command_output": result.stdout,
                    "errors": result.stderr if result.returncode != 0 else None
                }
            else:
                return {
                    "success": False,
                    "error": "Coverage report not generated",
                    "command_output": result.stdout,
                    "errors": result.stderr
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run coverage analysis: {str(e)}"
            }