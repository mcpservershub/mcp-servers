"""
Tests for storage layer.
"""

import pytest
from datetime import datetime

from pytest_mcp_server.models import (
    TestSession,
    TestResult,
    TestSummary,
    DebuggingProgress,
    FailureAnalysis
)
from pytest_mcp_server.storage import TestStorage


class TestTestStorage:
    """Test TestStorage class."""

    def test_init_memory_db(self):
        """Test initialization with memory database."""
        storage = TestStorage()
        assert storage.db_path == ":memory:"

    def test_init_file_db(self, temp_db):
        """Test initialization with file database."""
        storage = TestStorage(db_path=temp_db)
        assert storage.db_path == temp_db

    def test_store_and_get_session(self, storage, test_environment):
        """Test storing and retrieving sessions."""
        session = TestSession(
            session_id="test-session-123",
            environment=test_environment
        )

        # Store session
        storage.store_session(session)

        # Retrieve session
        retrieved = storage.get_session("test-session-123")
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved.environment.os == session.environment.os
        assert retrieved.status == session.status

    def test_get_nonexistent_session(self, storage):
        """Test getting a non-existent session."""
        result = storage.get_session("nonexistent")
        assert result is None

    def test_current_session(self, storage, test_environment):
        """Test current session tracking."""
        # No current session initially
        assert storage.get_current_session() is None

        # Store session sets it as current
        session = TestSession(
            session_id="current-session",
            environment=test_environment
        )
        storage.store_session(session)

        current = storage.get_current_session()
        assert current is not None
        assert current.session_id == "current-session"

    def test_create_default_session(self, storage):
        """Test creating default session."""
        session = storage.create_default_session()
        assert session.environment.os == "unknown"
        assert session.environment.python_version == "unknown"
        assert session.status == "running"

        # Should be set as current session
        current = storage.get_current_session()
        assert current.session_id == session.session_id

    def test_store_and_get_test_result(self, storage, sample_test_case, test_environment):
        """Test storing and retrieving test results."""
        # Create session first
        session = TestSession(
            session_id="test-session",
            environment=test_environment
        )
        storage.store_session(session)

        # Create and store test result
        result = TestResult(
            test_case=sample_test_case,
            session_id=session.session_id
        )
        storage.store_test_result(result)

        # Retrieve test result
        retrieved = storage.get_test_result(sample_test_case.nodeid)
        assert retrieved is not None
        assert retrieved.test_case.nodeid == sample_test_case.nodeid
        assert retrieved.test_case.outcome == sample_test_case.outcome
        assert retrieved.session_id == session.session_id

    def test_get_session_results(self, storage, sample_test_case, failed_test_case, test_environment):
        """Test getting all results for a session."""
        # Create session
        session = TestSession(
            session_id="test-session",
            environment=test_environment
        )
        storage.store_session(session)

        # Store multiple test results
        result1 = TestResult(
            test_case=sample_test_case,
            session_id=session.session_id
        )
        result2 = TestResult(
            test_case=failed_test_case,
            session_id=session.session_id
        )

        storage.store_test_result(result1)
        storage.store_test_result(result2)

        # Get all results
        results = storage.get_session_results(session.session_id)
        assert len(results) == 2

        nodeids = [r.test_case.nodeid for r in results]
        assert sample_test_case.nodeid in nodeids
        assert failed_test_case.nodeid in nodeids

    def test_store_and_get_session_summary(self, storage, test_environment):
        """Test storing and retrieving session summary."""
        # Create session
        session = TestSession(
            session_id="test-session",
            environment=test_environment
        )
        storage.store_session(session)

        # Create and store summary
        summary = TestSummary(
            total_tests=5,
            passed=3,
            failed=1,
            skipped=1,
            exitstatus=1,
            duration=10.5
        )
        storage.store_session_summary(session.session_id, summary)

        # Retrieve summary
        retrieved = storage.get_session_summary(session.session_id)
        assert retrieved is not None
        assert retrieved.total_tests == 5
        assert retrieved.passed == 3
        assert retrieved.failed == 1
        assert retrieved.exitstatus == 1
        assert retrieved.duration == 10.5

    def test_store_and_get_debugging_progress(self, storage):
        """Test storing and retrieving debugging progress."""
        progress = DebuggingProgress(
            failure_id="failure-123",
            steps_taken=["Checked logs"],
            hypotheses=["Network issue"],
            resolution_status="investigating",
            notes="Initial investigation"
        )

        # Store progress
        storage.store_debugging_progress(progress)

        # Retrieve progress
        retrieved = storage.get_debugging_progress("failure-123")
        assert retrieved is not None
        assert retrieved.failure_id == "failure-123"
        assert len(retrieved.steps_taken) == 1
        assert len(retrieved.hypotheses) == 1
        assert retrieved.resolution_status == "investigating"
        assert retrieved.notes == "Initial investigation"

    def test_get_test_statistics_empty(self, storage):
        """Test getting statistics from empty database."""
        stats = storage.get_test_statistics()
        assert stats["sessions"]["total"] == 0
        assert stats["total_tests"] == 0
        assert stats["test_outcomes"] == {}

    def test_get_test_statistics_with_data(self, storage, sample_test_case, failed_test_case, test_environment):
        """Test getting statistics with data."""
        # Create session
        session1 = TestSession(
            session_id="session-1",
            environment=test_environment,
            status="finished"
        )
        session2 = TestSession(
            session_id="session-2",
            environment=test_environment,
            status="running"
        )
        storage.store_session(session1)
        storage.store_session(session2)

        # Store test results
        result1 = TestResult(
            test_case=sample_test_case,
            session_id=session1.session_id
        )
        result2 = TestResult(
            test_case=failed_test_case,
            session_id=session1.session_id
        )
        storage.store_test_result(result1)
        storage.store_test_result(result2)

        # Get statistics
        stats = storage.get_test_statistics()
        assert stats["sessions"]["total"] == 2
        assert stats["sessions"]["completed"] == 1
        assert stats["sessions"]["active"] == 1
        assert stats["total_tests"] == 2
        assert stats["test_outcomes"]["passed"] == 1
        assert stats["test_outcomes"]["failed"] == 1

    def test_test_result_with_analysis(self, storage, failed_test_case, test_environment):
        """Test storing test result with failure analysis."""
        # Create session
        session = TestSession(
            session_id="test-session",
            environment=test_environment
        )
        storage.store_session(session)

        # Create failure analysis
        analysis = FailureAnalysis(
            analysis_id="analysis-123",
            test_case=failed_test_case,
            failure_category="assertion",
            suggested_actions=["Check values"],
            confidence_score=0.8
        )

        # Create test result with analysis
        result = TestResult(
            test_case=failed_test_case,
            session_id=session.session_id,
            analysis=analysis
        )
        storage.store_test_result(result)

        # Retrieve and verify
        retrieved = storage.get_test_result(failed_test_case.nodeid)
        assert retrieved is not None
        assert retrieved.analysis is not None
        assert retrieved.analysis.failure_category == "assertion"
        assert len(retrieved.analysis.suggested_actions) == 1
        assert retrieved.analysis.confidence_score == 0.8

    def test_update_session(self, storage, test_environment):
        """Test updating existing session."""
        # Create initial session
        session = TestSession(
            session_id="test-session",
            environment=test_environment,
            status="running"
        )
        storage.store_session(session)

        # Update session
        session.status = "finished"
        session.end_time = datetime.now()
        storage.store_session(session)

        # Verify update
        retrieved = storage.get_session(session.session_id)
        assert retrieved.status == "finished"
        assert retrieved.end_time is not None

    def test_replace_test_result(self, storage, sample_test_case, test_environment):
        """Test replacing existing test result."""
        # Create session
        session = TestSession(
            session_id="test-session",
            environment=test_environment
        )
        storage.store_session(session)

        # Store initial result
        result1 = TestResult(
            test_case=sample_test_case,
            session_id=session.session_id
        )
        storage.store_test_result(result1)

        # Store updated result (should replace)
        updated_case = sample_test_case.copy()
        updated_case.duration = 2.0
        result2 = TestResult(
            test_case=updated_case,
            session_id=session.session_id
        )
        storage.store_test_result(result2)

        # Should get the updated version
        retrieved = storage.get_test_result(sample_test_case.nodeid)
        assert retrieved.test_case.duration == 2.0

    def test_concurrent_access(self, storage, test_environment):
        """Test concurrent access to storage."""
        import threading
        import time

        results = []
        errors = []

        def create_session(session_id):
            try:
                session = TestSession(
                    session_id=f"session-{session_id}",
                    environment=test_environment
                )
                storage.store_session(session)
                results.append(session_id)
                time.sleep(0.001)  # Small delay to test concurrency
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert len(set(results)) == 10  # All unique