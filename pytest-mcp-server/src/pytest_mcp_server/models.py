"""
Data models for pytest MCP server.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TestOutcome(str, Enum):
    """Test outcome enumeration."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    XFAIL = "xfail"
    XPASS = "xpass"


class TestEnvironment(BaseModel):
    """Test environment information."""

    os: str = Field(..., description="Operating system")
    python_version: str = Field(..., description="Python version")
    pytest_version: Optional[str] = Field(None, description="Pytest version")
    platform: Optional[str] = Field(None, description="Platform information")
    architecture: Optional[str] = Field(None, description="System architecture")

    @validator('python_version')
    def validate_python_version(cls, v: str) -> str:
        """Validate Python version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+', v):
            raise ValueError("Invalid Python version format")
        return v


class TestCase(BaseModel):
    """Individual test case information."""

    nodeid: str = Field(..., description="Unique test node identifier")
    outcome: TestOutcome = Field(..., description="Test outcome")
    duration: float = Field(..., ge=0, description="Test duration in seconds")
    error: Optional[str] = Field(None, description="Error message if test failed")
    traceback: Optional[str] = Field(None, description="Full traceback if available")
    stdout: Optional[str] = Field(None, description="Captured stdout")
    stderr: Optional[str] = Field(None, description="Captured stderr")
    markers: Optional[List[str]] = Field(default_factory=list, description="Test markers")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Test keywords")
    file_path: Optional[str] = Field(None, description="Test file path")
    line_number: Optional[int] = Field(None, description="Test line number")

    @validator('duration')
    def validate_duration(cls, v: float) -> float:
        """Validate test duration is non-negative."""
        if v < 0:
            raise ValueError("Duration must be non-negative")
        return v


class TestSession(BaseModel):
    """Test session information."""

    session_id: str = Field(..., description="Unique session identifier")
    environment: TestEnvironment = Field(..., description="Test environment")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    status: str = Field(default="running", description="Session status")
    test_cases: List[TestCase] = Field(default_factory=list, description="Test cases")

    @validator('status')
    def validate_status(cls, v: str) -> str:
        """Validate session status."""
        valid_statuses = {"running", "finished", "aborted", "error"}
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class TestSummary(BaseModel):
    """Test session summary."""

    total_tests: int = Field(..., ge=0, description="Total number of tests")
    passed: int = Field(..., ge=0, description="Number of passed tests")
    failed: int = Field(..., ge=0, description="Number of failed tests")
    skipped: int = Field(..., ge=0, description="Number of skipped tests")
    errors: int = Field(default=0, ge=0, description="Number of error tests")
    xfailed: int = Field(default=0, ge=0, description="Number of expected failures")
    xpassed: int = Field(default=0, ge=0, description="Number of unexpected passes")
    exitstatus: int = Field(..., description="Exit status code")
    duration: float = Field(..., ge=0, description="Total session duration")

    @validator('total_tests')
    def validate_total_tests(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate that total tests matches sum of outcomes."""
        if 'passed' in values and 'failed' in values and 'skipped' in values:
            errors = values.get('errors', 0)
            xfailed = values.get('xfailed', 0)
            xpassed = values.get('xpassed', 0)
            expected_total = (
                values['passed'] + values['failed'] + values['skipped'] +
                errors + xfailed + xpassed
            )
            if v != expected_total:
                raise ValueError("Total tests must equal sum of all outcomes")
        return v


class FailurePattern(BaseModel):
    """Pattern for similar failures."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    error_type: str = Field(..., description="Type of error")
    error_signature: str = Field(..., description="Error signature/pattern")
    test_cases: List[str] = Field(..., description="Test cases matching this pattern")
    frequency: int = Field(..., ge=1, description="Number of occurrences")
    first_seen: datetime = Field(..., description="First occurrence timestamp")
    last_seen: datetime = Field(..., description="Last occurrence timestamp")


class DebuggingProgress(BaseModel):
    """Debugging progress tracking."""

    failure_id: str = Field(..., description="Failure identifier")
    steps_taken: List[str] = Field(default_factory=list, description="Debugging steps taken")
    hypotheses: List[str] = Field(default_factory=list, description="Current hypotheses")
    resolution_status: str = Field(default="investigating", description="Resolution status")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('resolution_status')
    def validate_resolution_status(cls, v: str) -> str:
        """Validate resolution status."""
        valid_statuses = {"investigating", "hypothesis_formed", "testing_fix", "resolved", "deferred"}
        if v not in valid_statuses:
            raise ValueError(f"Resolution status must be one of {valid_statuses}")
        return v


class FailureAnalysis(BaseModel):
    """Analysis of test failures for AI context."""

    analysis_id: str = Field(..., description="Analysis identifier")
    test_case: TestCase = Field(..., description="Failed test case")
    failure_category: Optional[str] = Field(None, description="Failure category")
    similar_failures: List[str] = Field(default_factory=list, description="Similar failure IDs")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested debugging actions")
    code_context: Optional[str] = Field(None, description="Relevant code context")
    environment_factors: List[str] = Field(default_factory=list, description="Environment factors")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Analysis confidence")
    created_at: datetime = Field(default_factory=datetime.now)


class TestResult(BaseModel):
    """Combined test result with metadata."""

    test_case: TestCase = Field(..., description="Test case information")
    session_id: str = Field(..., description="Session identifier")
    analysis: Optional[FailureAnalysis] = Field(None, description="Failure analysis if applicable")
    debugging_progress: Optional[DebuggingProgress] = Field(None, description="Debugging progress")

    @property
    def is_failure(self) -> bool:
        """Check if this is a failure result."""
        return self.test_case.outcome in [TestOutcome.FAILED, TestOutcome.ERROR]

    @property
    def needs_analysis(self) -> bool:
        """Check if this result needs failure analysis."""
        return self.is_failure and self.analysis is None


# Test Generation Models

class TestFramework(str, Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"


class TestGenerationType(str, Enum):
    """Types of test generation."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    INTEGRATION = "integration"


@dataclass
class FunctionAnalysis:
    """Analysis of a function for test generation."""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    complexity: int
    is_async: bool
    suggested_test_count: int


@dataclass
class ClassAnalysis:
    """Analysis of a class for test generation."""
    name: str
    methods: List[FunctionAnalysis]
    attributes: List[str]
    inheritance: List[str]
    suggested_test_count: int


class CodeAnalysisResult(BaseModel):
    """Result of code analysis for test generation."""

    file_path: str = Field(..., description="Path to the analyzed file")
    functions: List[Dict[str, Any]] = Field(default_factory=list, description="Analyzed functions")
    classes: List[Dict[str, Any]] = Field(default_factory=list, description="Analyzed classes")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    complexity_score: int = Field(default=0, description="Overall complexity score")
    recommendations: List[str] = Field(default_factory=list, description="Testing recommendations")
    estimated_test_count: int = Field(default=0, description="Estimated number of tests needed")


class TestGenerationRequest(BaseModel):
    """Request for test generation."""

    source_code: Optional[str] = Field(None, description="Source code to generate tests for")
    file_path: Optional[str] = Field(None, description="Path to source file")
    function_name: Optional[str] = Field(None, description="Specific function to test")
    class_name: Optional[str] = Field(None, description="Specific class to test")
    framework: TestFramework = Field(TestFramework.PYTEST, description="Test framework to use")
    generation_type: TestGenerationType = Field(TestGenerationType.FUNCTION, description="Type of test generation")
    include_mocks: bool = Field(True, description="Include mock-based tests")
    include_integration: bool = Field(False, description="Include integration tests")
    coverage_target: float = Field(default=80.0, ge=0.0, le=100.0, description="Target coverage percentage")

    @validator('source_code')
    def validate_source_code(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate that either source_code or file_path is provided."""
        if not v and not values.get('file_path'):
            raise ValueError("Either source_code or file_path must be provided")
        return v


class GeneratedTest(BaseModel):
    """A generated test case."""

    name: str = Field(..., description="Test function name")
    description: str = Field(..., description="Test description")
    test_code: str = Field(..., description="Generated test code")
    test_type: str = Field(..., description="Type of test (happy_path, edge_case, error_case)")
    priority: str = Field(..., description="Test priority (high, medium, low)")
    framework: TestFramework = Field(..., description="Test framework used")
    estimated_runtime: float = Field(default=0.1, description="Estimated test runtime in seconds")

    @validator('test_type')
    def validate_test_type(cls, v: str) -> str:
        """Validate test type."""
        valid_types = {"happy_path", "edge_case", "error_case", "integration", "performance", "mock_test", "parametrized"}
        if v not in valid_types:
            raise ValueError(f"Test type must be one of {valid_types}")
        return v

    @validator('priority')
    def validate_priority(cls, v: str) -> str:
        """Validate priority."""
        valid_priorities = {"high", "medium", "low"}
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


class GeneratedTestSuite(BaseModel):
    """A complete generated test suite."""

    file_name: str = Field(..., description="Test file name")
    source_file: Optional[str] = Field(None, description="Original source file")
    framework: TestFramework = Field(..., description="Test framework used")
    imports: List[str] = Field(default_factory=list, description="Required imports")
    fixtures: List[str] = Field(default_factory=list, description="Test fixtures")
    setup_code: Optional[str] = Field(None, description="Setup code")
    teardown_code: Optional[str] = Field(None, description="Teardown code")
    tests: List[GeneratedTest] = Field(..., description="Generated test cases")
    estimated_coverage: float = Field(default=0.0, description="Estimated code coverage")
    generation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Generation metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    @property
    def test_count(self) -> int:
        """Get total number of tests."""
        return len(self.tests)

    @property
    def high_priority_tests(self) -> List[GeneratedTest]:
        """Get high priority tests."""
        return [test for test in self.tests if test.priority == "high"]

    @property
    def estimated_runtime(self) -> float:
        """Get estimated total runtime."""
        return sum(test.estimated_runtime for test in self.tests)


class CoverageAnalysis(BaseModel):
    """Coverage analysis result."""

    file_path: str = Field(..., description="Path to analyzed file")
    total_lines: int = Field(..., ge=0, description="Total lines of code")
    covered_lines: int = Field(..., ge=0, description="Lines covered by tests")
    missing_lines: List[int] = Field(default_factory=list, description="Line numbers not covered")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Coverage percentage")
    uncovered_functions: List[str] = Field(default_factory=list, description="Functions without coverage")
    recommendations: List[str] = Field(default_factory=list, description="Coverage improvement recommendations")

    @validator('covered_lines')
    def validate_covered_lines(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate covered lines doesn't exceed total."""
        if 'total_lines' in values and v > values['total_lines']:
            raise ValueError("Covered lines cannot exceed total lines")
        return v


class TestCaseRecommendation(BaseModel):
    """Recommendation for a specific test case."""

    test_name: str = Field(..., description="Recommended test name")
    description: str = Field(..., description="Test description")
    test_type: str = Field(..., description="Type of test recommended")
    priority: str = Field(..., description="Priority level")
    reasoning: str = Field(..., description="Why this test is recommended")
    example_code: Optional[str] = Field(None, description="Example test code")
    target_function: Optional[str] = Field(None, description="Function being tested")
    target_class: Optional[str] = Field(None, description="Class being tested")