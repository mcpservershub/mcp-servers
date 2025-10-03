#!/usr/bin/env python3
"""
Example script demonstrating how to use the pytest MCP server programmatically.
"""

import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pytest_mcp_server.models import (
    TestEnvironment, TestSession, TestCase, TestOutcome,
    TestResult, TestSummary
)
from pytest_mcp_server.storage import TestStorage
from pytest_mcp_server.analysis import FailureAnalyzer


def main():
    """Run example demonstrating MCP server usage."""
    print("🧪 Pytest MCP Server Example")
    print("=" * 50)

    # Initialize components
    import tempfile
    import os

    # Use a temporary file for the database so it persists across connections
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = db_file.name
    db_file.close()

    try:
        storage = TestStorage(db_path=db_path)  # File-based database for demo
        analyzer = FailureAnalyzer()
        print("✅ Initialized storage and analyzer")
        print(f"   Using database: {db_path}")

        # Example 1: Record session start
        print("\n📝 Recording session start...")
        environment = TestEnvironment(
        os="Linux",
        python_version="3.12.0",
        pytest_version="8.0.0",
        platform="Linux-x86_64",
        architecture="x86_64"
    )

    session_id = str(uuid4())
    session = TestSession(
        session_id=session_id,
        environment=environment
    )
    storage.store_session(session)
    print(f"   Session ID: {session_id}")
    print(f"   Environment: {environment.os} Python {environment.python_version}")

    # Example 2: Record passing test
    print("\n✅ Recording passing test...")
    passing_test = TestCase(
        nodeid="tests/test_example.py::test_addition",
        outcome=TestOutcome.PASSED,
        duration=0.123,
        markers=["unit", "fast"],
        keywords=["test", "addition"],
        file_path="tests/test_example.py",
        line_number=10
    )

    passing_result = TestResult(
        test_case=passing_test,
        session_id=session_id
    )
    storage.store_test_result(passing_result)
    print(f"   Test recorded: {passing_test.nodeid}")
    print(f"   Outcome: {passing_test.outcome.value}")
    print(f"   Duration: {passing_test.duration:.3f}s")

    # Example 3: Record failing test with analysis
    print("\n❌ Recording failing test...")
    failing_test = TestCase(
        nodeid="tests/test_example.py::test_assertion_failure",
        outcome=TestOutcome.FAILED,
        duration=0.456,
        error="AssertionError: assert 1 == 2",
        traceback="""Traceback (most recent call last):
  File "tests/test_example.py", line 15, in test_assertion_failure
    assert 1 == 2, "This should fail for demonstration"
AssertionError: assert 1 == 2""",
        markers=["unit"],
        keywords=["test", "assertion"],
        file_path="tests/test_example.py",
        line_number=15
    )

    # Analyze the failure
    analysis = analyzer.analyze_failure(failing_test)

    failing_result = TestResult(
        test_case=failing_test,
        session_id=session_id,
        analysis=analysis
    )
    storage.store_test_result(failing_result)

    print(f"   Test recorded: {failing_test.nodeid}")
    print(f"   Outcome: {failing_test.outcome.value}")
    print(f"   Failure category: {analysis.failure_category}")
    print(f"   Confidence: {analysis.confidence_score:.2f}")
    if analysis.suggested_actions:
        print(f"   First suggestion: {analysis.suggested_actions[0]}")

    # Example 4: Get failure analysis details
    print("\n🔍 Detailed failure analysis...")
    retrieved_result = storage.get_test_result(failing_test.nodeid)
    if retrieved_result and retrieved_result.analysis:
        analysis = retrieved_result.analysis
        print(f"   Analysis ID: {analysis.analysis_id}")
        print(f"   Category: {analysis.failure_category}")
        print(f"   Suggestions ({len(analysis.suggested_actions)}):")
        for i, suggestion in enumerate(analysis.suggested_actions[:3], 1):
            print(f"     {i}. {suggestion}")

        if analysis.environment_factors:
            print(f"   Environment factors: {', '.join(analysis.environment_factors)}")

    # Example 5: Generate debugging prompt
    print("\n🤖 Generating debugging prompt for LLM...")
    if retrieved_result:
        prompt = analyzer.generate_debugging_prompt(retrieved_result)
        print(f"   Generated prompt length: {len(prompt)} characters")
        print("   Preview (first 10 lines):")
        lines = prompt.split('\n')[:10]
        for line in lines:
            print(f"     {line}")
        if len(prompt.split('\n')) > 10:
            print("     ... (truncated)")

    # Example 6: Record more tests for statistics
    print("\n📊 Recording additional tests...")
    additional_tests = [
        TestCase(
            nodeid="tests/test_utils.py::test_string_operations",
            outcome=TestOutcome.PASSED,
            duration=0.089
        ),
        TestCase(
            nodeid="tests/test_utils.py::test_list_processing",
            outcome=TestOutcome.PASSED,
            duration=0.134
        ),
        TestCase(
            nodeid="tests/test_api.py::test_connection_timeout",
            outcome=TestOutcome.FAILED,
            duration=5.001,
            error="TimeoutError: Connection timed out after 5 seconds",
            markers=["integration", "slow"]
        ),
        TestCase(
            nodeid="tests/test_integration.py::test_slow_query",
            outcome=TestOutcome.SKIPPED,
            duration=0.001
        )
    ]

    for test_case in additional_tests:
        # Analyze failures
        analysis = None
        if test_case.outcome in [TestOutcome.FAILED, TestOutcome.ERROR]:
            analysis = analyzer.analyze_failure(test_case)

        test_result = TestResult(
            test_case=test_case,
            session_id=session_id,
            analysis=analysis
        )
        storage.store_test_result(test_result)
        print(f"   Recorded: {test_case.nodeid} - {test_case.outcome.value}")

    # Example 7: Record session finish
    print("\n🏁 Recording session finish...")
    session.status = "finished"
    session.end_time = datetime.now()
    storage.store_session(session)

    summary = TestSummary(
        total_tests=6,
        passed=3,
        failed=2,
        skipped=1,
        errors=0,
        exitstatus=1,
        duration=6.304
    )
    storage.store_session_summary(session_id, summary)

    print(f"   Session finished: {session.status}")
    print(f"   Total tests: {summary.total_tests}")
    print(f"   Pass rate: {summary.passed}/{summary.total_tests} ({summary.passed/summary.total_tests*100:.1f}%)")

    # Example 8: Get test statistics
    print("\n📈 Getting test statistics...")
    stats = storage.get_test_statistics()
    print(f"   Total sessions: {stats['sessions']['total']}")
    print(f"   Active sessions: {stats['sessions']['active']}")
    print(f"   Completed sessions: {stats['sessions']['completed']}")
    print(f"   Total tests: {stats['total_tests']}")
    print("   Test outcomes:")
    for outcome, count in stats.get('test_outcomes', {}).items():
        print(f"     {outcome}: {count}")

    # Example 9: Session details
    print("\n📋 Session details...")
    retrieved_session = storage.get_session(session_id)
    session_summary = storage.get_session_summary(session_id)
    session_results = storage.get_session_results(session_id)

    if retrieved_session:
        print(f"   Session ID: {retrieved_session.session_id}")
        print(f"   Status: {retrieved_session.status}")
        print(f"   Duration: {(retrieved_session.end_time - retrieved_session.start_time).total_seconds():.2f}s")
        print(f"   Test count: {len(session_results)}")
        print(f"   Failure count: {sum(1 for r in session_results if r.is_failure)}")

    # Example 10: Show failure analysis for timeout test
    print("\n🔍 Analyzing timeout failure...")
    timeout_result = storage.get_test_result("tests/test_api.py::test_connection_timeout")
    if timeout_result and timeout_result.analysis:
        analysis = timeout_result.analysis
        print(f"   Category: {analysis.failure_category}")
        print(f"   Environment factors: {analysis.environment_factors}")
        print("   Suggestions:")
        for suggestion in analysis.suggested_actions[:2]:
            print(f"     • {suggestion}")

    print("\n🎉 Example completed successfully!")
    print(f"\nSummary:")
    print(f"• Created session with {summary.total_tests} tests")
    print(f"• {summary.passed} passed, {summary.failed} failed, {summary.skipped} skipped")
    print(f"• Generated {len([r for r in session_results if r.analysis])} failure analyses")
    print(f"• Session stored in database with ID: {session_id[:8]}...")

    print("\nNext steps:")
    print("1. Start the MCP server: pytest-mcp-server serve")
    print("2. Use MCP Inspector to interact with the server")
    print("3. Run pytest with --mcp flag to integrate with your tests")
    print("4. Explore the generated debugging prompts and failure analysis")


if __name__ == "__main__":
    main()