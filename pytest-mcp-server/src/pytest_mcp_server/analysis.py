"""
Failure analysis and debugging assistance for AI agents.
"""

import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    FailureAnalysis,
    FailurePattern,
    TestCase,
    TestResult,
)


class FailureAnalyzer:
    """Analyzes test failures and provides debugging assistance."""

    def __init__(self):
        """Initialize the failure analyzer."""
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.error_categories = {
            "assertion": ["AssertionError", "assert"],
            "import": ["ImportError", "ModuleNotFoundError"],
            "attribute": ["AttributeError"],
            "type": ["TypeError"],
            "value": ["ValueError"],
            "key": ["KeyError"],
            "index": ["IndexError"],
            "timeout": ["TimeoutError", "timeout"],
            "connection": ["ConnectionError", "ConnectTimeout"],
            "file": ["FileNotFoundError", "PermissionError"],
            "syntax": ["SyntaxError"],
            "indentation": ["IndentationError"]
        }

    def analyze_failure(self, test_case: TestCase) -> FailureAnalysis:
        """Analyze a failed test case and provide insights."""
        analysis_id = str(uuid4())

        # Extract error information
        error_info = self._extract_error_info(test_case)

        # Categorize the failure
        failure_category = self._categorize_failure(error_info)

        # Find similar failures
        similar_failures = self._find_similar_patterns(error_info)

        # Generate suggested actions
        suggested_actions = self._generate_suggestions(failure_category, error_info)

        # Extract code context if available
        code_context = self._extract_code_context(test_case)

        # Identify environment factors
        environment_factors = self._identify_environment_factors(test_case)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(error_info, similar_failures)

        return FailureAnalysis(
            analysis_id=analysis_id,
            test_case=test_case,
            failure_category=failure_category,
            similar_failures=similar_failures,
            suggested_actions=suggested_actions,
            code_context=code_context,
            environment_factors=environment_factors,
            confidence_score=confidence_score
        )

    def _extract_error_info(self, test_case: TestCase) -> Dict[str, str]:
        """Extract structured error information from test case."""
        error_info = {
            "type": "unknown",
            "message": test_case.error or "",
            "signature": "",
            "location": ""
        }

        if test_case.error:
            # Extract error type
            error_match = re.search(r'(\w+Error|\w+Exception)', test_case.error)
            if error_match:
                error_info["type"] = error_match.group(1)

            # Extract error message (first line after error type)
            lines = test_case.error.split('\n')
            for line in lines:
                if ':' in line and error_info["type"] in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        error_info["message"] = parts[1].strip()
                        break

        # Create error signature for pattern matching
        error_info["signature"] = self._create_error_signature(error_info)

        # Extract location information
        if test_case.file_path and test_case.line_number:
            error_info["location"] = f"{test_case.file_path}:{test_case.line_number}"

        return error_info

    def _create_error_signature(self, error_info: Dict[str, str]) -> str:
        """Create a signature for error pattern matching."""
        # Normalize error message by removing specific values
        message = error_info["message"]
        # Remove specific numbers, paths, and variable names
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'["\'].*?["\']', 'STR', normalized)
        normalized = re.sub(r'/[^\s]+', 'PATH', normalized)

        signature = f"{error_info['type']}:{normalized}"
        return hashlib.md5(signature.encode()).hexdigest()[:8]

    def _categorize_failure(self, error_info: Dict[str, str]) -> str:
        """Categorize the failure based on error type and message."""
        error_type = error_info["type"].lower()
        error_message = error_info["message"].lower()

        for category, patterns in self.error_categories.items():
            for pattern in patterns:
                if pattern.lower() in error_type or pattern.lower() in error_message:
                    return category

        return "unknown"

    def _find_similar_patterns(self, error_info: Dict[str, str]) -> List[str]:
        """Find similar failure patterns."""
        similar = []
        current_signature = error_info["signature"]

        for pattern_id, pattern in self.failure_patterns.items():
            if pattern.error_signature == current_signature:
                similar.append(pattern_id)
            elif pattern.error_type == error_info["type"]:
                # Similar error type, check message similarity
                if self._calculate_similarity(error_info["message"], pattern.error_signature) > 0.7:
                    similar.append(pattern_id)

        return similar

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _generate_suggestions(self, category: str, error_info: Dict[str, str]) -> List[str]:
        """Generate debugging suggestions based on failure category."""
        suggestions = []

        category_suggestions = {
            "assertion": [
                "Check the expected vs actual values in the assertion",
                "Verify test data setup and preconditions",
                "Review the logic being tested for edge cases",
                "Add debug prints to understand intermediate values"
            ],
            "import": [
                "Check if the module is installed in the environment",
                "Verify the import path and module name",
                "Check for circular imports",
                "Ensure the module is in PYTHONPATH"
            ],
            "attribute": [
                "Verify the object has the expected attribute",
                "Check if the object is None before accessing attributes",
                "Review object initialization and attribute assignment",
                "Check for typos in attribute names"
            ],
            "type": [
                "Verify the types of arguments passed to functions",
                "Check for None values where objects are expected",
                "Review type conversions and casting",
                "Add type hints and use mypy for static analysis"
            ],
            "timeout": [
                "Increase timeout values if operations are legitimately slow",
                "Check for infinite loops or blocking operations",
                "Review async/await usage in asynchronous code",
                "Consider mocking slow external dependencies"
            ],
            "connection": [
                "Check network connectivity and service availability",
                "Verify connection parameters (host, port, credentials)",
                "Review retry logic and error handling",
                "Consider using test doubles for external services"
            ]
        }

        suggestions.extend(category_suggestions.get(category, [
            "Review the error message and traceback carefully",
            "Check test setup and teardown procedures",
            "Verify test environment configuration",
            "Add logging to understand the failure sequence"
        ]))

        # Add specific suggestions based on error message
        error_message = error_info["message"].lower()
        if "none" in error_message:
            suggestions.append("Check for None values - add null checks before operations")
        if "expected" in error_message and "actual" in error_message:
            suggestions.append("Compare expected and actual values to understand the discrepancy")

        return suggestions

    def _extract_code_context(self, test_case: TestCase) -> Optional[str]:
        """Extract relevant code context if available."""
        context_parts = []

        if test_case.file_path:
            context_parts.append(f"Test file: {test_case.file_path}")

        if test_case.line_number:
            context_parts.append(f"Line: {test_case.line_number}")

        if test_case.traceback:
            # Extract key lines from traceback
            lines = test_case.traceback.split('\n')
            relevant_lines = [line.strip() for line in lines if 'File "' in line or '>' in line]
            if relevant_lines:
                context_parts.append("Traceback highlights:")
                context_parts.extend(relevant_lines[:5])  # Limit to 5 most relevant lines

        return '\n'.join(context_parts) if context_parts else None

    def _identify_environment_factors(self, test_case: TestCase) -> List[str]:
        """Identify environmental factors that might affect the test."""
        factors = []

        # Check for common environment-related issues
        if test_case.error:
            error_lower = test_case.error.lower()

            if "permission" in error_lower:
                factors.append("File/directory permissions")
            if "network" in error_lower or "connection" in error_lower:
                factors.append("Network connectivity")
            if "timeout" in error_lower:
                factors.append("System performance/timing")
            if "encoding" in error_lower:
                factors.append("Character encoding")
            if "path" in error_lower or "file" in error_lower:
                factors.append("File system paths")

        # Check markers for environment hints
        for marker in test_case.markers or []:
            if marker in ["slow", "integration", "network", "database"]:
                factors.append(f"Test marked as '{marker}'")

        return factors

    def _calculate_confidence(self, error_info: Dict[str, str], similar_failures: List[str]) -> float:
        """Calculate confidence score for the analysis."""
        confidence = 0.5  # Base confidence

        # Increase confidence based on error information completeness
        if error_info["type"] != "unknown":
            confidence += 0.2
        if error_info["message"]:
            confidence += 0.1
        if error_info["location"]:
            confidence += 0.1

        # Increase confidence if we found similar failures
        if similar_failures:
            confidence += min(0.2, len(similar_failures) * 0.05)

        return min(1.0, confidence)

    def find_similar_failures(
        self,
        error_pattern: Optional[str] = None,
        test_pattern: Optional[str] = None,
        limit: int = 10
    ) -> List[FailurePattern]:
        """Find similar failures based on patterns."""
        results = []

        for pattern in self.failure_patterns.values():
            match_score = 0

            if error_pattern:
                if error_pattern.lower() in pattern.error_signature.lower():
                    match_score += 1
                if error_pattern.lower() in pattern.error_type.lower():
                    match_score += 0.5

            if test_pattern:
                matching_tests = [tc for tc in pattern.test_cases
                                if test_pattern.lower() in tc.lower()]
                if matching_tests:
                    match_score += len(matching_tests) * 0.3

            if match_score > 0:
                results.append((match_score, pattern))

        # Sort by match score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [pattern for _, pattern in results[:limit]]

    def generate_debugging_prompt(self, test_result: TestResult) -> str:
        """Generate a comprehensive debugging prompt for LLMs."""
        test_case = test_result.test_case
        analysis = test_result.analysis

        prompt_parts = [
            "# Test Failure Debugging Assistant\n",
            f"## Failed Test: {test_case.nodeid}\n",
            f"**Outcome:** {test_case.outcome.value}",
            f"**Duration:** {test_case.duration:.3f}s\n"
        ]

        # Add error information
        if test_case.error:
            prompt_parts.extend([
                "## Error Information",
                f"```\n{test_case.error}\n```\n"
            ])

        # Add traceback if available
        if test_case.traceback:
            prompt_parts.extend([
                "## Full Traceback",
                f"```\n{test_case.traceback}\n```\n"
            ])

        # Add captured output
        if test_case.stdout:
            prompt_parts.extend([
                "## Captured Output (stdout)",
                f"```\n{test_case.stdout}\n```\n"
            ])

        if test_case.stderr:
            prompt_parts.extend([
                "## Captured Errors (stderr)",
                f"```\n{test_case.stderr}\n```\n"
            ])

        # Add analysis results
        if analysis:
            prompt_parts.extend([
                "## Failure Analysis",
                f"**Category:** {analysis.failure_category}",
                f"**Confidence:** {analysis.confidence_score:.2f}\n"
            ])

            if analysis.suggested_actions:
                prompt_parts.extend([
                    "### Suggested Debugging Actions:",
                ] + [f"- {action}" for action in analysis.suggested_actions])

            if analysis.code_context:
                prompt_parts.extend([
                    "\n### Code Context:",
                    f"```\n{analysis.code_context}\n```"
                ])

            if analysis.environment_factors:
                prompt_parts.extend([
                    "\n### Environment Factors:",
                ] + [f"- {factor}" for factor in analysis.environment_factors])

            if analysis.similar_failures:
                prompt_parts.extend([
                    f"\n### Similar Failures Found: {len(analysis.similar_failures)}",
                    "Consider reviewing these similar cases for patterns."
                ])

        # Add debugging progress if available
        if test_result.debugging_progress:
            progress = test_result.debugging_progress
            prompt_parts.extend([
                "\n## Debugging Progress",
                f"**Status:** {progress.resolution_status}"
            ])

            if progress.steps_taken:
                prompt_parts.extend([
                    "\n### Steps Already Taken:",
                ] + [f"- {step}" for step in progress.steps_taken])

            if progress.hypotheses:
                prompt_parts.extend([
                    "\n### Current Hypotheses:",
                ] + [f"- {hypothesis}" for hypothesis in progress.hypotheses])

            if progress.notes:
                prompt_parts.extend([
                    f"\n### Notes:\n{progress.notes}"
                ])

        # Add final guidance
        prompt_parts.extend([
            "\n## Debugging Guidance",
            "Please analyze this test failure and provide:",
            "1. Root cause analysis based on the error and context",
            "2. Step-by-step debugging approach",
            "3. Specific code changes or fixes to resolve the issue",
            "4. Prevention strategies to avoid similar failures",
            "\nFocus on actionable, specific recommendations rather than generic advice."
        ])

        return '\n'.join(prompt_parts)