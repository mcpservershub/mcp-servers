"""
Tests for MCP server functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from pytest_mcp_server.server import create_server


class TestMCPServerTools:
    """Test MCP server tools."""

    @pytest.fixture
    def server(self):
        """Create server instance for testing."""
        return create_server()

    def test_record_session_start_success(self, server, sample_environment_data):
        """Test successful session start recording."""
        # Mock the storage to avoid database operations
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            mock_storage.store_session = MagicMock()

            # Call the tool function directly
            result = server._tools['record_session_start']['func'](sample_environment_data)

            assert result['success'] is True
            assert 'session_id' in result
            assert result['environment'] == sample_environment_data
            mock_storage.store_session.assert_called_once()

    def test_record_session_start_invalid_data(self, server):
        """Test session start with invalid data."""
        invalid_data = {
            "os": "Linux",
            # Missing python_version
        }

        result = server._tools['record_session_start']['func'](invalid_data)

        assert result['success'] is False
        assert 'error' in result
        assert 'Validation error' in result['error']

    def test_record_test_outcome_success(self, server, sample_test_outcome_data):
        """Test successful test outcome recording."""
        with patch('pytest_mcp_server.server.storage') as mock_storage, \
             patch('pytest_mcp_server.server.analyzer') as mock_analyzer:

            # Mock storage methods
            mock_session = MagicMock()
            mock_session.session_id = "test-session"
            mock_storage.get_current_session.return_value = mock_session
            mock_storage.store_test_result = MagicMock()

            # Call the tool
            result = server._tools['record_test_outcome']['func'](**sample_test_outcome_data)

            assert result['success'] is True
            assert result['test_case']['nodeid'] == sample_test_outcome_data['nodeid']
            assert result['test_case']['outcome'] == sample_test_outcome_data['outcome']
            mock_storage.store_test_result.assert_called_once()

    def test_record_test_outcome_failed_test(self, server, sample_failed_test_data):
        """Test recording failed test outcome with analysis."""
        with patch('pytest_mcp_server.server.storage') as mock_storage, \
             patch('pytest_mcp_server.server.analyzer') as mock_analyzer:

            # Mock storage methods
            mock_session = MagicMock()
            mock_session.session_id = "test-session"
            mock_storage.get_current_session.return_value = mock_session
            mock_storage.store_test_result = MagicMock()

            # Mock analyzer
            mock_analysis = MagicMock()
            mock_analysis.dict.return_value = {"analysis_id": "test-analysis"}
            mock_analyzer.analyze_failure.return_value = mock_analysis

            # Call the tool
            result = server._tools['record_test_outcome']['func'](**sample_failed_test_data)

            assert result['success'] is True
            assert 'failure_analysis' in result
            mock_analyzer.analyze_failure.assert_called_once()

    def test_record_test_outcome_no_session(self, server, sample_test_outcome_data):
        """Test recording test outcome when no session exists."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock no current session, but create_default_session works
            mock_storage.get_current_session.return_value = None
            mock_default_session = MagicMock()
            mock_default_session.session_id = "default-session"
            mock_storage.create_default_session.return_value = mock_default_session
            mock_storage.store_test_result = MagicMock()

            result = server._tools['record_test_outcome']['func'](**sample_test_outcome_data)

            assert result['success'] is True
            assert result['session_id'] == "default-session"
            mock_storage.create_default_session.assert_called_once()

    def test_record_test_outcome_invalid_data(self, server):
        """Test recording test outcome with invalid data."""
        invalid_data = {
            "nodeid": "test.py::test_func",
            "outcome": "invalid_outcome",  # Invalid outcome
            "duration": 0.1
        }

        result = server._tools['record_test_outcome']['func'](**invalid_data)

        assert result['success'] is False
        assert 'Validation error' in result['error']

    def test_record_session_finish_success(self, server, sample_session_summary):
        """Test successful session finish recording."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock current session
            mock_session = MagicMock()
            mock_session.session_id = "test-session"
            mock_session.start_time = MagicMock()
            mock_storage.get_current_session.return_value = mock_session
            mock_storage.store_session = MagicMock()
            mock_storage.store_session_summary = MagicMock()

            result = server._tools['record_session_finish']['func'](sample_session_summary)

            assert result['success'] is True
            assert result['session_id'] == "test-session"
            assert 'summary' in result
            mock_storage.store_session.assert_called_once()
            mock_storage.store_session_summary.assert_called_once()

    def test_record_session_finish_no_session(self, server, sample_session_summary):
        """Test session finish when no active session."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            mock_storage.get_current_session.return_value = None

            result = server._tools['record_session_finish']['func'](sample_session_summary)

            assert result['success'] is False
            assert 'No active session found' in result['error']

    def test_get_session_status_current(self, server):
        """Test getting current session status."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock current session
            mock_session = MagicMock()
            mock_session.session_id = "test-session"
            mock_session.dict.return_value = {"session_id": "test-session", "status": "running"}
            mock_storage.get_current_session.return_value = mock_session

            # Mock summary and results
            mock_summary = MagicMock()
            mock_summary.dict.return_value = {"total_tests": 5}
            mock_storage.get_session_summary.return_value = mock_summary
            mock_storage.get_session_results.return_value = []

            result = server._tools['get_session_status']['func']()

            assert result['success'] is True
            assert result['session']['session_id'] == "test-session"
            assert result['summary']['total_tests'] == 5

    def test_get_session_status_specific(self, server):
        """Test getting specific session status."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock specific session
            mock_session = MagicMock()
            mock_session.session_id = "specific-session"
            mock_session.dict.return_value = {"session_id": "specific-session"}
            mock_storage.get_session.return_value = mock_session

            # Mock summary and results
            mock_storage.get_session_summary.return_value = None
            mock_storage.get_session_results.return_value = [MagicMock()]

            result = server._tools['get_session_status']['func']("specific-session")

            assert result['success'] is True
            assert result['session']['session_id'] == "specific-session"
            assert result['test_count'] == 1

    def test_get_session_status_not_found(self, server):
        """Test getting status for non-existent session."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            mock_storage.get_session.return_value = None

            result = server._tools['get_session_status']['func']("nonexistent")

            assert result['success'] is False
            assert 'Session not found' in result['error']

    def test_get_failure_analysis_success(self, server):
        """Test getting failure analysis for a test."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock test result with analysis
            mock_test_result = MagicMock()
            mock_test_result.is_failure = True
            mock_test_result.analysis = MagicMock()
            mock_test_result.analysis.dict.return_value = {"analysis_id": "test-analysis"}
            mock_test_result.test_case.dict.return_value = {"nodeid": "test.py::test_func"}
            mock_storage.get_test_result.return_value = mock_test_result

            result = server._tools['get_failure_analysis']['func']("test.py::test_func")

            assert result['success'] is True
            assert 'analysis' in result
            assert result['analysis']['analysis_id'] == "test-analysis"

    def test_get_failure_analysis_not_failure(self, server):
        """Test getting analysis for non-failed test."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock passing test result
            mock_test_result = MagicMock()
            mock_test_result.is_failure = False
            mock_storage.get_test_result.return_value = mock_test_result

            result = server._tools['get_failure_analysis']['func']("test.py::test_func")

            assert result['success'] is False
            assert 'Test did not fail' in result['error']

    def test_find_similar_failures(self, server):
        """Test finding similar failures."""
        with patch('pytest_mcp_server.server.analyzer') as mock_analyzer:
            # Mock similar failures
            mock_failure = MagicMock()
            mock_failure.dict.return_value = {"pattern_id": "pattern1"}
            mock_analyzer.find_similar_failures.return_value = [mock_failure]

            result = server._tools['find_similar_failures']['func'](
                error_pattern="AssertionError",
                limit=5
            )

            assert result['success'] is True
            assert result['count'] == 1
            assert len(result['similar_failures']) == 1

    def test_track_debugging_progress_add_step(self, server):
        """Test tracking debugging progress by adding step."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Mock existing progress
            mock_progress = MagicMock()
            mock_progress.steps_taken = []
            mock_progress.dict.return_value = {"failure_id": "test-failure"}
            mock_storage.get_debugging_progress.return_value = mock_progress
            mock_storage.store_debugging_progress = MagicMock()

            result = server._tools['track_debugging_progress']['func'](
                failure_id="test-failure",
                action="add_step",
                step_description="Checked logs"
            )

            assert result['success'] is True
            assert len(mock_progress.steps_taken) == 1
            assert mock_progress.steps_taken[0] == "Checked logs"

    def test_track_debugging_progress_new_failure(self, server):
        """Test tracking progress for new failure."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # No existing progress
            mock_storage.get_debugging_progress.return_value = None
            mock_storage.store_debugging_progress = MagicMock()

            result = server._tools['track_debugging_progress']['func'](
                failure_id="new-failure",
                action="add_step",
                step_description="Initial investigation"
            )

            assert result['success'] is True
            # Should create new progress and store it
            mock_storage.store_debugging_progress.assert_called_once()

    def test_generate_debugging_prompt(self, server):
        """Test generating debugging prompt."""
        with patch('pytest_mcp_server.server.storage') as mock_storage, \
             patch('pytest_mcp_server.server.analyzer') as mock_analyzer:

            # Mock test result
            mock_test_result = MagicMock()
            mock_test_result.is_failure = True
            mock_test_result.test_case.dict.return_value = {"nodeid": "test.py::test_func"}
            mock_storage.get_test_result.return_value = mock_test_result

            # Mock generated prompt
            mock_analyzer.generate_debugging_prompt.return_value = "Debug this test..."

            result = server._tools['generate_debugging_prompt']['func']("test.py::test_func")

            assert result['success'] is True
            assert result['debugging_prompt'] == "Debug this test..."
            mock_analyzer.generate_debugging_prompt.assert_called_once_with(mock_test_result)

    def test_get_test_statistics(self, server):
        """Test getting test statistics."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            mock_stats = {
                "sessions": {"total": 5, "completed": 4, "active": 1},
                "total_tests": 100,
                "test_outcomes": {"passed": 80, "failed": 15, "skipped": 5}
            }
            mock_storage.get_test_statistics.return_value = mock_stats

            result = server._tools['get_test_statistics']['func']()

            assert result['success'] is True
            assert result['statistics'] == mock_stats

    def test_server_tool_exception_handling(self, server):
        """Test that server tools handle exceptions properly."""
        with patch('pytest_mcp_server.server.storage') as mock_storage:
            # Make storage raise an exception
            mock_storage.get_current_session.side_effect = Exception("Database error")

            result = server._tools['get_session_status']['func']()

            assert result['success'] is False
            assert 'Internal error' in result['error']
            assert 'Database error' in result['error']