"""
Tests for data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from pytest_mcp_server.models import (
    TestEnvironment,
    TestCase,
    TestOutcome,
    TestSession,
    TestSummary,
    FailureAnalysis,
    DebuggingProgress,
    TestResult,
)


class TestTestEnvironment:
    """Test TestEnvironment model."""

    def test_valid_environment(self):
        """Test creating a valid environment."""
        env = TestEnvironment(
            os="Linux",
            python_version="3.12.0"
        )
        assert env.os == "Linux"
        assert env.python_version == "3.12.0"

    def test_invalid_python_version(self):
        """Test invalid Python version format."""
        with pytest.raises(ValidationError):
            TestEnvironment(
                os="Linux",
                python_version="invalid"
            )

    def test_optional_fields(self):
        """Test optional fields."""
        env = TestEnvironment(
            os="Linux",
            python_version="3.12.0",
            pytest_version="8.0.0",
            platform="Linux-x86_64",
            architecture="x86_64"
        )
        assert env.pytest_version == "8.0.0"
        assert env.platform == "Linux-x86_64"
        assert env.architecture == "x86_64"


class TestTestCase:
    """Test TestCase model."""

    def test_valid_test_case(self):
        """Test creating a valid test case."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.PASSED,
            duration=1.5
        )
        assert test_case.nodeid == "test.py::test_func"
        assert test_case.outcome == TestOutcome.PASSED
        assert test_case.duration == 1.5

    def test_negative_duration(self):
        """Test negative duration validation."""
        with pytest.raises(ValidationError):
            TestCase(
                nodeid="test.py::test_func",
                outcome=TestOutcome.PASSED,
                duration=-1.0
            )

    def test_failed_test_case(self):
        """Test failed test case with error."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.FAILED,
            duration=1.5,
            error="AssertionError: test failed",
            traceback="Full traceback here"
        )
        assert test_case.error == "AssertionError: test failed"
        assert test_case.traceback == "Full traceback here"

    def test_optional_metadata(self):
        """Test optional metadata fields."""
        test_case = TestCase(
            nodeid="test.py::test_func",
            outcome=TestOutcome.PASSED,
            duration=1.5,
            markers=["unit", "fast"],
            keywords=["test"],
            file_path="/path/to/test.py",
            line_number=10
        )
        assert test_case.markers == ["unit", "fast"]
        assert test_case.keywords == ["test"]
        assert test_case.file_path == "/path/to/test.py"
        assert test_case.line_number == 10


class TestTestSession:
    """Test TestSession model."""

    def test_valid_session(self, test_environment):
        """Test creating a valid session."""
        session = TestSession(
            session_id="test-session-123",
            environment=test_environment
        )
        assert session.session_id == "test-session-123"
        assert session.environment == test_environment
        assert session.status == "running"
        assert isinstance(session.start_time, datetime)

    def test_invalid_status(self, test_environment):
        """Test invalid status validation."""
        with pytest.raises(ValidationError):
            TestSession(
                session_id="test-session-123",
                environment=test_environment,
                status="invalid_status"
            )

    def test_finished_session(self, test_environment):
        """Test finished session."""
        end_time = datetime.now()
        session = TestSession(
            session_id="test-session-123",
            environment=test_environment,
            end_time=end_time,
            status="finished"
        )
        assert session.end_time == end_time
        assert session.status == "finished"


class TestTestSummary:
    """Test TestSummary model."""

    def test_valid_summary(self):
        """Test creating a valid summary."""
        summary = TestSummary(
            total_tests=10,
            passed=7,
            failed=2,
            skipped=1,
            exitstatus=1,
            duration=15.5
        )
        assert summary.total_tests == 10
        assert summary.passed == 7
        assert summary.failed == 2
        assert summary.skipped == 1

    def test_negative_values(self):
        """Test negative values validation."""
        with pytest.raises(ValidationError):
            TestSummary(
                total_tests=-1,
                passed=0,
                failed=0,
                skipped=0,
                exitstatus=0,
                duration=0.0
            )

    def test_invalid_total(self):
        """Test invalid total tests validation."""
        with pytest.raises(ValidationError):
            TestSummary(
                total_tests=5,  # Should be 10 (7+2+1)
                passed=7,
                failed=2,
                skipped=1,
                exitstatus=0,
                duration=0.0
            )


class TestDebuggingProgress:
    """Test DebuggingProgress model."""

    def test_valid_progress(self):
        """Test creating valid debugging progress."""
        progress = DebuggingProgress(
            failure_id="failure-123"
        )
        assert progress.failure_id == "failure-123"
        assert progress.resolution_status == "investigating"
        assert isinstance(progress.created_at, datetime)

    def test_invalid_resolution_status(self):
        """Test invalid resolution status."""
        with pytest.raises(ValidationError):
            DebuggingProgress(
                failure_id="failure-123",
                resolution_status="invalid_status"
            )

    def test_progress_with_data(self):
        """Test progress with steps and hypotheses."""
        progress = DebuggingProgress(
            failure_id="failure-123",
            steps_taken=["Checked logs", "Reviewed code"],
            hypotheses=["Network timeout", "Race condition"],
            resolution_status="hypothesis_formed",
            notes="Found potential cause"
        )
        assert len(progress.steps_taken) == 2
        assert len(progress.hypotheses) == 2
        assert progress.resolution_status == "hypothesis_formed"
        assert progress.notes == "Found potential cause"


class TestFailureAnalysis:
    """Test FailureAnalysis model."""

    def test_valid_analysis(self, failed_test_case):
        """Test creating valid failure analysis."""
        analysis = FailureAnalysis(
            analysis_id="analysis-123",
            test_case=failed_test_case
        )
        assert analysis.analysis_id == "analysis-123"
        assert analysis.test_case == failed_test_case
        assert analysis.confidence_score == 0.0

    def test_analysis_with_suggestions(self, failed_test_case):
        """Test analysis with suggestions."""
        analysis = FailureAnalysis(
            analysis_id="analysis-123",
            test_case=failed_test_case,
            failure_category="assertion",
            suggested_actions=["Check expected values", "Review test logic"],
            confidence_score=0.8
        )
        assert analysis.failure_category == "assertion"
        assert len(analysis.suggested_actions) == 2
        assert analysis.confidence_score == 0.8

    def test_invalid_confidence_score(self, failed_test_case):
        """Test invalid confidence score."""
        with pytest.raises(ValidationError):
            FailureAnalysis(
                analysis_id="analysis-123",
                test_case=failed_test_case,
                confidence_score=1.5  # Should be <= 1.0
            )


class TestTestResult:
    """Test TestResult model."""

    def test_valid_result(self, sample_test_case):
        """Test creating valid test result."""
        result = TestResult(
            test_case=sample_test_case,
            session_id="session-123"
        )
        assert result.test_case == sample_test_case
        assert result.session_id == "session-123"
        assert not result.is_failure
        assert not result.needs_analysis

    def test_failed_result(self, failed_test_case):
        """Test failed test result."""
        result = TestResult(
            test_case=failed_test_case,
            session_id="session-123"
        )
        assert result.is_failure
        assert result.needs_analysis

    def test_result_with_analysis(self, failed_test_case):
        """Test result with failure analysis."""
        analysis = FailureAnalysis(
            analysis_id="analysis-123",
            test_case=failed_test_case
        )
        result = TestResult(
            test_case=failed_test_case,
            session_id="session-123",
            analysis=analysis
        )
        assert result.is_failure
        assert not result.needs_analysis  # Has analysis, doesn't need one