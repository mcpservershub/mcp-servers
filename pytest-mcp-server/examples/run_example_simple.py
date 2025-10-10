#!/usr/bin/env python3
"""
Simple example demonstrating the pytest MCP server components.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pytest_mcp_server.models import (
    TestEnvironment, TestSession, TestCase, TestOutcome,
    TestResult, TestSummary
)
from pytest_mcp_server.storage import TestStorage
from pytest_mcp_server.analysis import FailureAnalyzer


def main():
    """Simple demonstration of MCP server functionality."""
    print("🧪 Pytest MCP Server - Simple Demo")
    print("=" * 40)

    # Use a temporary file-based database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize components
        print("📦 Initializing components...")
        storage = TestStorage(db_path=db_path)
        analyzer = FailureAnalyzer()
        print(f"   Database: {os.path.basename(db_path)}")

        # Create a test environment
        print("\n🌍 Creating test environment...")
        environment = TestEnvironment(
            os="Linux",
            python_version="3.12.0"
        )
        print(f"   OS: {environment.os}")
        print(f"   Python: {environment.python_version}")

        # Create and store a test session
        print("\n📝 Creating test session...")
        from uuid import uuid4
        session = TestSession(
            session_id=str(uuid4()),
            environment=environment
        )
        storage.store_session(session)
        print(f"   Session ID: {session.session_id[:8]}...")

        # Create and analyze a failing test
        print("\n❌ Creating failing test...")
        failing_test = TestCase(
            nodeid="test_demo.py::test_assertion",
            outcome=TestOutcome.FAILED,
            duration=0.123,
            error="AssertionError: assert 1 == 2",
            traceback="Traceback...\nAssertionError: assert 1 == 2"
        )

        # Analyze the failure
        print("\n🔍 Analyzing failure...")
        analysis = analyzer.analyze_failure(failing_test)
        print(f"   Category: {analysis.failure_category}")
        print(f"   Confidence: {analysis.confidence_score:.2f}")
        print(f"   Suggestions: {len(analysis.suggested_actions)}")

        # Store the test result with analysis
        test_result = TestResult(
            test_case=failing_test,
            session_id=session.session_id,
            analysis=analysis
        )
        storage.store_test_result(test_result)

        # Generate a debugging prompt
        print("\n🤖 Generating debugging prompt...")
        prompt = analyzer.generate_debugging_prompt(test_result)
        print(f"   Prompt length: {len(prompt)} characters")
        print("   Preview:")
        lines = prompt.split('\n')[:5]
        for line in lines:
            print(f"     {line}")
        print("     ...")

        # Finish the session
        print("\n🏁 Finishing session...")
        session.status = "finished"
        from datetime import datetime
        session.end_time = datetime.now()
        storage.store_session(session)

        summary = TestSummary(
            total_tests=1,
            passed=0,
            failed=1,
            skipped=0,
            exitstatus=1,
            duration=0.123
        )
        storage.store_session_summary(session.session_id, summary)

        # Get statistics
        print("\n📊 Getting statistics...")
        stats = storage.get_test_statistics()
        print(f"   Sessions: {stats['sessions']['total']}")
        print(f"   Tests: {stats['total_tests']}")
        print(f"   Outcomes: {dict(stats['test_outcomes'])}")

        print("\n✅ Demo completed successfully!")
        print("\nThe MCP server provides these capabilities:")
        print("• Test session management")
        print("• Failure analysis and categorization")
        print("• AI-powered debugging suggestions")
        print("• Test statistics and metrics")
        print("• Debugging prompt generation for LLMs")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass


if __name__ == "__main__":
    main()