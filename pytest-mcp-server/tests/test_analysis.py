"""
Tests for failure analysis functionality.
"""

import pytest
from datetime import datetime

from pytest_mcp_server.analysis import FailureAnalyzer
from pytest_mcp_server.models import (
    TestCase,
    TestOutcome,
    TestResult,
    FailureAnalysis,
    DebuggingProgress
)


class TestFailureAnalyzer:
    """Test FailureAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a failure analyzer instance."""
        return FailureAnalyzer()

    @pytest.fixture
    def assertion_failure_case(self):
        """Create a test case with assertion failure."""
        return TestCase(
            nodeid="test_assertions.py::test_equality",
            outcome=TestOutcome.FAILED,
            duration=0.123,
            error="AssertionError: assert 1 == 2",
            traceback="Traceback (most recent call last):\n  File 'test.py', line 5, in test_equality\n    assert 1 == 2\nAssertionError: assert 1 == 2",
            file_path="test_assertions.py",
            line_number=5
        )

    @pytest.fixture
    def import_error_case(self):
        """Create a test case with import error."""
        return TestCase(
            nodeid="test_imports.py::test_missing_module",
            outcome=TestOutcome.ERROR,
            duration=0.001,
            error="ModuleNotFoundError: No module named 'nonexistent'",
            traceback="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    import nonexistent\nModuleNotFoundError: No module named 'nonexistent'",
            file_path="test_imports.py",
            line_number=1
        )

    def test_analyze_assertion_failure(self, analyzer, assertion_failure_case):
        """Test analyzing assertion failure."""
        analysis = analyzer.analyze_failure(assertion_failure_case)

        assert isinstance(analysis, FailureAnalysis)
        assert analysis.test_case == assertion_failure_case
        assert analysis.failure_category == "assertion"
        assert analysis.confidence_score > 0.5
        assert len(analysis.suggested_actions) > 0
        assert any("assertion" in action.lower() for action in analysis.suggested_actions)

    def test_analyze_import_error(self, analyzer, import_error_case):
        """Test analyzing import error."""
        analysis = analyzer.analyze_failure(import_error_case)

        assert analysis.failure_category == "import"
        assert len(analysis.suggested_actions) > 0
        assert any("module" in action.lower() or "import" in action.lower()
                  for action in analysis.suggested_actions)

    def test_extract_error_info_assertion(self, analyzer, assertion_failure_case):
        """Test extracting error info from assertion failure."""
        error_info = analyzer._extract_error_info(assertion_failure_case)

        assert error_info["type"] == "AssertionError"
        assert "assert 1 == 2" in error_info["message"]
        assert error_info["signature"] != ""
        assert "test_assertions.py:5" in error_info["location"]

    def test_extract_error_info_import_error(self, analyzer, import_error_case):
        """Test extracting error info from import error."""
        error_info = analyzer._extract_error_info(import_error_case)

        assert error_info["type"] == "ModuleNotFoundError"
        assert "nonexistent" in error_info["message"]

    def test_categorize_failure_assertion(self, analyzer):
        """Test categorizing assertion failures."""
        error_info = {
            "type": "AssertionError",
            "message": "assert 1 == 2",
            "signature": "test_sig"
        }
        category = analyzer._categorize_failure(error_info)
        assert category == "assertion"

    def test_categorize_failure_import(self, analyzer):
        """Test categorizing import failures."""
        error_info = {
            "type": "ModuleNotFoundError",
            "message": "No module named 'test'",
            "signature": "test_sig"
        }
        category = analyzer._categorize_failure(error_info)
        assert category == "import"

    def test_categorize_failure_unknown(self, analyzer):
        """Test categorizing unknown failures."""
        error_info = {
            "type": "UnknownError",
            "message": "Something went wrong",
            "signature": "test_sig"
        }
        category = analyzer._categorize_failure(error_info)
        assert category == "unknown"

    def test_create_error_signature(self, analyzer):
        """Test creating error signatures."""
        error_info = {
            "type": "AssertionError",
            "message": "assert 123 == 456"
        }
        signature1 = analyzer._create_error_signature(error_info)

        # Same error with different numbers should have same signature
        error_info2 = {
            "type": "AssertionError",
            "message": "assert 789 == 101"
        }
        signature2 = analyzer._create_error_signature(error_info2)

        assert signature1 == signature2
        assert len(signature1) == 8  # MD5 hash truncated to 8 chars

    def test_generate_suggestions_assertion(self, analyzer):
        """Test generating suggestions for assertion errors."""
        suggestions = analyzer._generate_suggestions("assertion", {
            "type": "AssertionError",
            "message": "assert 1 == 2"
        })

        assert len(suggestions) > 0
        assert any("assertion" in s.lower() for s in suggestions)
        assert any("expected" in s.lower() or "actual" in s.lower() for s in suggestions)

    def test_generate_suggestions_import(self, analyzer):
        """Test generating suggestions for import errors."""
        suggestions = analyzer._generate_suggestions("import", {
            "type": "ImportError",
            "message": "No module named 'test'"
        })

        assert len(suggestions) > 0
        assert any("module" in s.lower() or "install" in s.lower() for s in suggestions)

    def test_generate_suggestions_with_none_message(self, analyzer):
        """Test generating suggestions when None is mentioned in error."""
        suggestions = analyzer._generate_suggestions("type", {
            "type": "TypeError",
            "message": "NoneType object has no attribute 'test'"
        })

        assert len(suggestions) > 0
        assert any("none" in s.lower() and "null" in s.lower() for s in suggestions)

    def test_extract_code_context(self, analyzer, assertion_failure_case):
        """Test extracting code context."""
        context = analyzer._extract_code_context(assertion_failure_case)

        assert context is not None
        assert "test_assertions.py" in context
        assert "Line: 5" in context
        assert "Traceback highlights:" in context

    def test_extract_code_context_minimal(self, analyzer):
        """Test extracting code context with minimal info."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.FAILED,
            duration=0.1,
            error="Error occurred"
        )
        context = analyzer._extract_code_context(test_case)
        assert context is None  # No file path, line number, or traceback

    def test_identify_environment_factors(self, analyzer):
        """Test identifying environment factors."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.FAILED,
            duration=0.1,
            error="PermissionError: Access denied",
            markers=["slow", "integration"]
        )

        factors = analyzer._identify_environment_factors(test_case)

        assert len(factors) > 0
        assert any("permission" in f.lower() for f in factors)
        assert any("slow" in f for f in factors)
        assert any("integration" in f for f in factors)

    def test_calculate_confidence_complete_info(self, analyzer):
        """Test confidence calculation with complete error info."""
        error_info = {
            "type": "AssertionError",
            "message": "assert failed",
            "location": "test.py:10"
        }
        similar_failures = ["failure1", "failure2"]

        confidence = analyzer._calculate_confidence(error_info, similar_failures)

        assert confidence > 0.5
        assert confidence <= 1.0

    def test_calculate_confidence_minimal_info(self, analyzer):
        """Test confidence calculation with minimal error info."""
        error_info = {
            "type": "unknown",
            "message": "",
            "location": ""
        }
        similar_failures = []

        confidence = analyzer._calculate_confidence(error_info, similar_failures)

        assert confidence == 0.5  # Base confidence only

    def test_calculate_similarity(self, analyzer):
        """Test text similarity calculation."""
        text1 = "assert value equals expected"
        text2 = "assert expected equals value"

        similarity = analyzer._calculate_similarity(text1, text2)

        assert 0 < similarity <= 1
        assert similarity > 0.5  # Should be quite similar

        # Completely different texts
        similarity2 = analyzer._calculate_similarity("hello world", "foo bar")
        assert similarity2 < similarity

    def test_generate_debugging_prompt_complete(self, analyzer, assertion_failure_case):
        """Test generating comprehensive debugging prompt."""
        analysis = FailureAnalysis(
            analysis_id="test-analysis",
            test_case=assertion_failure_case,
            failure_category="assertion",
            suggested_actions=["Check expected values", "Review test logic"],
            confidence_score=0.8
        )

        progress = DebuggingProgress(
            failure_id="test-failure",
            steps_taken=["Reviewed code", "Checked logs"],
            hypotheses=["Logic error", "Data issue"],
            resolution_status="investigating"
        )

        test_result = TestResult(
            test_case=assertion_failure_case,
            session_id="test-session",
            analysis=analysis,
            debugging_progress=progress
        )

        prompt = analyzer.generate_debugging_prompt(test_result)

        assert "# Test Failure Debugging Assistant" in prompt
        assert assertion_failure_case.nodeid in prompt
        assert "AssertionError" in prompt
        assert "assertion" in prompt  # failure category
        assert "Check expected values" in prompt  # suggested actions
        assert "Reviewed code" in prompt  # debugging steps
        assert "Logic error" in prompt  # hypotheses

    def test_generate_debugging_prompt_minimal(self, analyzer):
        """Test generating debugging prompt with minimal info."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.FAILED,
            duration=0.1
        )

        test_result = TestResult(
            test_case=test_case,
            session_id="test-session"
        )

        prompt = analyzer.generate_debugging_prompt(test_result)

        assert "# Test Failure Debugging Assistant" in prompt
        assert test_case.nodeid in prompt
        assert "failed" in prompt

    def test_find_similar_failures_empty(self, analyzer):
        """Test finding similar failures when none exist."""
        results = analyzer.find_similar_failures(
            error_pattern="NonexistentError",
            limit=5
        )
        assert len(results) == 0

    def test_find_similar_failures_with_patterns(self, analyzer):
        """Test finding similar failures with existing patterns."""
        from pytest_mcp_server.models import FailurePattern

        # Add some failure patterns
        pattern1 = FailurePattern(
            pattern_id="pattern1",
            error_type="AssertionError",
            error_signature="assert_failure_sig",
            test_cases=["test1.py::test_a", "test2.py::test_b"],
            frequency=2,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        analyzer.failure_patterns["pattern1"] = pattern1

        # Search for similar failures
        results = analyzer.find_similar_failures(
            error_pattern="assert",
            limit=5
        )

        assert len(results) > 0
        assert results[0].pattern_id == "pattern1"