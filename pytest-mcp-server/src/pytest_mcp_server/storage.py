"""
Storage layer for test data and results.
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from .models import (
    DebuggingProgress,
    TestResult,
    TestSession,
    TestSummary,
    TestEnvironment,
)


class TestStorage:
    """Thread-safe storage for test data."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with SQLite backend."""
        self.db_path = db_path or ":memory:"
        self._lock = threading.RLock()
        self._current_session: Optional[TestSession] = None

        # For in-memory databases, we need to keep a persistent connection
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._use_persistent_connection = True
        else:
            self._conn = None
            self._use_persistent_connection = False

        self._init_database()

    def _get_connection(self):
        """Get database connection."""
        if self._use_persistent_connection:
            return self._conn
        else:
            return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._lock:
            conn = self._get_connection()
            close_connection = not self._use_persistent_connection
            try:
                # Sessions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        environment TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Test results table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS test_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        nodeid TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        duration REAL NOT NULL,
                        error TEXT,
                        traceback TEXT,
                        stdout TEXT,
                        stderr TEXT,
                        markers TEXT,
                        keywords TEXT,
                        file_path TEXT,
                        line_number INTEGER,
                        analysis TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                ''')

                # Session summaries table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS session_summaries (
                        session_id TEXT PRIMARY KEY,
                        total_tests INTEGER NOT NULL,
                        passed INTEGER NOT NULL,
                        failed INTEGER NOT NULL,
                        skipped INTEGER NOT NULL,
                        errors INTEGER DEFAULT 0,
                        xfailed INTEGER DEFAULT 0,
                        xpassed INTEGER DEFAULT 0,
                        exitstatus INTEGER NOT NULL,
                        duration REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                ''')

                # Debugging progress table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS debugging_progress (
                        failure_id TEXT PRIMARY KEY,
                        steps_taken TEXT NOT NULL,
                        hypotheses TEXT NOT NULL,
                        resolution_status TEXT NOT NULL,
                        notes TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                # Create indexes
                conn.execute('CREATE INDEX IF NOT EXISTS idx_test_results_session ON test_results(session_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_test_results_nodeid ON test_results(nodeid)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_test_results_outcome ON test_results(outcome)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)')

                conn.commit()
            finally:
                if close_connection:
                    conn.close()

    def store_session(self, session: TestSession) -> None:
        """Store a test session."""
        with self._lock:
            conn = self._get_connection()
            close_connection = not self._use_persistent_connection
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO sessions
                    (session_id, environment, start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    json.dumps(session.environment.dict()),
                    session.start_time.isoformat(),
                    session.end_time.isoformat() if session.end_time else None,
                    session.status
                ))
                conn.commit()
                self._current_session = session
            finally:
                if close_connection:
                    conn.close()

    def get_session(self, session_id: str) -> Optional[TestSession]:
        """Get a test session by ID."""
        with self._lock:
            conn = self._get_connection()
            close_connection = not self._use_persistent_connection
            try:
                cursor = conn.execute('''
                    SELECT session_id, environment, start_time, end_time, status
                    FROM sessions WHERE session_id = ?
                ''', (session_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return TestSession(
                    session_id=row[0],
                    environment=TestEnvironment(**json.loads(row[1])),
                    start_time=datetime.fromisoformat(row[2]),
                    end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                    status=row[4]
                )
            finally:
                if close_connection:
                    conn.close()

    def get_current_session(self) -> Optional[TestSession]:
        """Get the current active session."""
        return self._current_session

    def create_default_session(self) -> TestSession:
        """Create a default session when none exists."""
        session = TestSession(
            session_id=str(uuid4()),
            environment=TestEnvironment(
                os="unknown",
                python_version="unknown"
            ),
            start_time=datetime.now(),
            status="running"
        )
        self.store_session(session)
        return session

    def store_test_result(self, test_result: TestResult) -> None:
        """Store a test result."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                test_case = test_result.test_case
                conn.execute('''
                    INSERT OR REPLACE INTO test_results
                    (session_id, nodeid, outcome, duration, error, traceback, stdout, stderr,
                     markers, keywords, file_path, line_number, analysis)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_result.session_id,
                    test_case.nodeid,
                    test_case.outcome.value,
                    test_case.duration,
                    test_case.error,
                    test_case.traceback,
                    test_case.stdout,
                    test_case.stderr,
                    json.dumps(test_case.markers),
                    json.dumps(test_case.keywords),
                    test_case.file_path,
                    test_case.line_number,
                    json.dumps(test_result.analysis.dict(), default=str) if test_result.analysis else None
                ))
                conn.commit()
            finally:
                conn.close()

    def get_test_result(self, nodeid: str) -> Optional[TestResult]:
        """Get the most recent test result for a given nodeid."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cursor = conn.execute('''
                    SELECT session_id, nodeid, outcome, duration, error, traceback, stdout, stderr,
                           markers, keywords, file_path, line_number, analysis
                    FROM test_results
                    WHERE nodeid = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (nodeid,))

                row = cursor.fetchone()
                if not row:
                    return None

                from .models import TestCase, TestOutcome

                test_case = TestCase(
                    nodeid=row[1],
                    outcome=TestOutcome(row[2]),
                    duration=row[3],
                    error=row[4],
                    traceback=row[5],
                    stdout=row[6],
                    stderr=row[7],
                    markers=json.loads(row[8]) if row[8] else [],
                    keywords=json.loads(row[9]) if row[9] else [],
                    file_path=row[10],
                    line_number=row[11]
                )

                analysis = None
                if row[12]:
                    from .models import FailureAnalysis
                    analysis_data = json.loads(row[12])
                    analysis = FailureAnalysis(**analysis_data)

                return TestResult(
                    test_case=test_case,
                    session_id=row[0],
                    analysis=analysis
                )
            finally:
                conn.close()

    def get_session_results(self, session_id: str) -> List[TestResult]:
        """Get all test results for a session."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cursor = conn.execute('''
                    SELECT session_id, nodeid, outcome, duration, error, traceback, stdout, stderr,
                           markers, keywords, file_path, line_number, analysis
                    FROM test_results
                    WHERE session_id = ?
                    ORDER BY created_at
                ''', (session_id,))

                results = []
                for row in cursor.fetchall():
                    from .models import TestCase, TestOutcome

                    test_case = TestCase(
                        nodeid=row[1],
                        outcome=TestOutcome(row[2]),
                        duration=row[3],
                        error=row[4],
                        traceback=row[5],
                        stdout=row[6],
                        stderr=row[7],
                        markers=json.loads(row[8]) if row[8] else [],
                        keywords=json.loads(row[9]) if row[9] else [],
                        file_path=row[10],
                        line_number=row[11]
                    )

                    analysis = None
                    if row[12]:
                        from .models import FailureAnalysis
                        analysis_data = json.loads(row[12])
                        analysis = FailureAnalysis(**analysis_data)

                    results.append(TestResult(
                        test_case=test_case,
                        session_id=row[0],
                        analysis=analysis
                    ))

                return results
            finally:
                conn.close()

    def store_session_summary(self, session_id: str, summary: TestSummary) -> None:
        """Store session summary."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO session_summaries
                    (session_id, total_tests, passed, failed, skipped, errors, xfailed, xpassed, exitstatus, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    summary.total_tests,
                    summary.passed,
                    summary.failed,
                    summary.skipped,
                    summary.errors,
                    summary.xfailed,
                    summary.xpassed,
                    summary.exitstatus,
                    summary.duration
                ))
                conn.commit()
            finally:
                conn.close()

    def get_session_summary(self, session_id: str) -> Optional[TestSummary]:
        """Get session summary."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cursor = conn.execute('''
                    SELECT total_tests, passed, failed, skipped, errors, xfailed, xpassed, exitstatus, duration
                    FROM session_summaries WHERE session_id = ?
                ''', (session_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return TestSummary(
                    total_tests=row[0],
                    passed=row[1],
                    failed=row[2],
                    skipped=row[3],
                    errors=row[4],
                    xfailed=row[5],
                    xpassed=row[6],
                    exitstatus=row[7],
                    duration=row[8]
                )
            finally:
                conn.close()

    def store_debugging_progress(self, progress: DebuggingProgress) -> None:
        """Store debugging progress."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO debugging_progress
                    (failure_id, steps_taken, hypotheses, resolution_status, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    progress.failure_id,
                    json.dumps(progress.steps_taken),
                    json.dumps(progress.hypotheses),
                    progress.resolution_status,
                    progress.notes,
                    progress.created_at.isoformat(),
                    progress.updated_at.isoformat()
                ))
                conn.commit()
            finally:
                conn.close()

    def get_debugging_progress(self, failure_id: str) -> Optional[DebuggingProgress]:
        """Get debugging progress."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cursor = conn.execute('''
                    SELECT failure_id, steps_taken, hypotheses, resolution_status, notes, created_at, updated_at
                    FROM debugging_progress WHERE failure_id = ?
                ''', (failure_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return DebuggingProgress(
                    failure_id=row[0],
                    steps_taken=json.loads(row[1]),
                    hypotheses=json.loads(row[2]),
                    resolution_status=row[3],
                    notes=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    updated_at=datetime.fromisoformat(row[6])
                )
            finally:
                conn.close()

    def get_test_statistics(self) -> Dict[str, Any]:
        """Get comprehensive test statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                # Session statistics
                cursor = conn.execute('''
                    SELECT COUNT(*) as total_sessions,
                           COUNT(CASE WHEN status = 'finished' THEN 1 END) as completed_sessions,
                           COUNT(CASE WHEN status = 'running' THEN 1 END) as active_sessions
                    FROM sessions
                ''')
                session_stats = cursor.fetchone()

                # Test statistics
                cursor = conn.execute('''
                    SELECT outcome, COUNT(*) as count
                    FROM test_results
                    GROUP BY outcome
                ''')
                outcome_stats = {row[0]: row[1] for row in cursor.fetchall()}

                # Recent failure patterns
                cursor = conn.execute('''
                    SELECT error, COUNT(*) as count
                    FROM test_results
                    WHERE outcome IN ('failed', 'error') AND error IS NOT NULL
                    GROUP BY error
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                error_patterns = [{"error": row[0], "count": row[1]} for row in cursor.fetchall()]

                # Performance metrics
                cursor = conn.execute('''
                    SELECT AVG(duration) as avg_duration,
                           MAX(duration) as max_duration,
                           MIN(duration) as min_duration
                    FROM test_results
                ''')
                perf_stats = cursor.fetchone()

                return {
                    "sessions": {
                        "total": session_stats[0],
                        "completed": session_stats[1],
                        "active": session_stats[2]
                    },
                    "test_outcomes": outcome_stats,
                    "common_errors": error_patterns,
                    "performance": {
                        "avg_duration": perf_stats[0] or 0.0,
                        "max_duration": perf_stats[1] or 0.0,
                        "min_duration": perf_stats[2] or 0.0
                    },
                    "total_tests": sum(outcome_stats.values())
                }
            finally:
                conn.close()