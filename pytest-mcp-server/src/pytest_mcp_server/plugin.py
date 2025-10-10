"""
Pytest plugin for MCP server integration.

This plugin automatically captures test results and sends them to the MCP server.
"""

import json
import os
import platform
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import pytest
from _pytest.config import Config
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo

from .models import TestEnvironment


class PytestMCPPlugin:
    """Pytest plugin that integrates with MCP server."""

    def __init__(self, config: Config):
        """Initialize the plugin."""
        self.config = config
        self.session_id: Optional[str] = None
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.session_start_time: Optional[datetime] = None

        # Check if MCP integration is enabled
        self.enabled = config.getoption("--mcp", default=False)
        self.mcp_server_url = config.getoption("--mcp-server", default=None)

        if self.enabled:
            # Try to connect to MCP server
            self._initialize_mcp_connection()

    def _initialize_mcp_connection(self) -> None:
        """Initialize connection to MCP server."""
        try:
            # Import MCP client here to avoid dependency issues when not used
            from mcp.client.stdio import stdio_client, StdioServerParameters

            # Create MCP client (this would need to be configured properly)
            # For now, we'll store results locally and provide them via CLI
            pass
        except ImportError:
            print("Warning: MCP client not available. Test results will be stored locally.")

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session: Session) -> None:
        """Called after the Session object has been created."""
        if not self.enabled:
            return

        self.session_start_time = datetime.now()

        # Gather environment information
        environment = TestEnvironment(
            os=platform.system(),
            python_version=platform.python_version(),
            pytest_version=pytest.__version__,
            platform=platform.platform(),
            architecture=platform.machine()
        )

        # Store environment info for later use
        self._record_session_start(environment)

    def _record_session_start(self, environment: TestEnvironment) -> None:
        """Record session start with MCP server."""
        try:
            # This would call the MCP server's record_session_start tool
            # For now, we'll just log it
            print(f"\n[MCP] Test session started with environment: {environment.dict()}")

            # In a real implementation, you would call:
            # result = self.mcp_client.call_tool("record_session_start", {"environment": environment.dict()})
            # self.session_id = result.get("session_id")
        except Exception as e:
            print(f"[MCP] Warning: Failed to record session start: {e}")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> None:
        """Called when a test report is created."""
        outcome = yield
        if not self.enabled:
            return

        report: TestReport = outcome.get_result()

        # Only process call phase (actual test execution)
        if call.when == "call":
            self._record_test_outcome(item, report)

    def _record_test_outcome(self, item: Item, report: TestReport) -> None:
        """Record individual test outcome."""
        try:
            # Extract test information
            nodeid = item.nodeid
            outcome = self._map_outcome(report.outcome)
            duration = getattr(report, 'duration', 0.0)

            # Extract error information
            error = None
            traceback_str = None
            if report.failed or report.outcome == "error":
                if hasattr(report, 'longrepr') and report.longrepr:
                    traceback_str = str(report.longrepr)
                    # Extract just the error message (last line typically)
                    lines = traceback_str.split('\n')
                    error_lines = [line.strip() for line in lines if line.strip() and not line.startswith(' ')]
                    if error_lines:
                        error = error_lines[-1]

            # Extract captured output
            stdout = None
            stderr = None
            if hasattr(report, 'capstdout') and report.capstdout:
                stdout = report.capstdout
            if hasattr(report, 'capstderr') and report.capstderr:
                stderr = report.capstderr

            # Extract markers and keywords
            markers = [marker.name for marker in item.iter_markers()]
            keywords = list(item.keywords.keys())

            # Get file path and line number
            file_path = str(item.fspath) if hasattr(item, 'fspath') else None
            line_number = getattr(item, 'lineno', None)

            # Store test result
            test_data = {
                "nodeid": nodeid,
                "outcome": outcome,
                "duration": duration,
                "error": error,
                "traceback": traceback_str,
                "stdout": stdout,
                "stderr": stderr,
                "markers": markers,
                "keywords": keywords,
                "file_path": file_path,
                "line_number": line_number
            }

            self.test_results[nodeid] = test_data

            # Record with MCP server
            print(f"[MCP] Test {outcome}: {nodeid} ({duration:.3f}s)")
            if error:
                print(f"[MCP] Error: {error}")

            # In a real implementation, you would call:
            # self.mcp_client.call_tool("record_test_outcome", test_data)

        except Exception as e:
            print(f"[MCP] Warning: Failed to record test outcome for {item.nodeid}: {e}")

    def _map_outcome(self, pytest_outcome: str) -> str:
        """Map pytest outcome to MCP server outcome."""
        mapping = {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped",
            "error": "error",
            "xfail": "xfail",
            "xpass": "xpass"
        }
        return mapping.get(pytest_outcome, pytest_outcome)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        """Called after whole test run finished, right before returning the exit status."""
        if not self.enabled:
            return

        # Calculate session summary
        summary = self._calculate_summary(exitstatus)

        # Record session finish
        self._record_session_finish(summary)

        # Save results to file for inspection
        self._save_results_to_file()

    def _calculate_summary(self, exitstatus: int) -> Dict[str, Any]:
        """Calculate test session summary."""
        outcomes = {}
        total_duration = 0.0

        for test_data in self.test_results.values():
            outcome = test_data["outcome"]
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            total_duration += test_data.get("duration", 0.0)

        summary = {
            "total_tests": len(self.test_results),
            "passed": outcomes.get("passed", 0),
            "failed": outcomes.get("failed", 0),
            "skipped": outcomes.get("skipped", 0),
            "errors": outcomes.get("error", 0),
            "xfailed": outcomes.get("xfail", 0),
            "xpassed": outcomes.get("xpass", 0),
            "exitstatus": exitstatus,
            "duration": total_duration
        }

        return summary

    def _record_session_finish(self, summary: Dict[str, Any]) -> None:
        """Record session finish with MCP server."""
        try:
            print(f"[MCP] Test session finished: {summary}")

            # In a real implementation, you would call:
            # self.mcp_client.call_tool("record_session_finish", {"summary": summary})

        except Exception as e:
            print(f"[MCP] Warning: Failed to record session finish: {e}")

    def _save_results_to_file(self) -> None:
        """Save test results to a JSON file for inspection."""
        try:
            output_file = "mcp_test_results.json"
            data = {
                "session_start_time": self.session_start_time.isoformat() if self.session_start_time else None,
                "session_end_time": datetime.now().isoformat(),
                "test_results": self.test_results,
                "summary": self._calculate_summary(0)  # We don't have access to exitstatus here
            }

            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"[MCP] Test results saved to {output_file}")

        except Exception as e:
            print(f"[MCP] Warning: Failed to save results to file: {e}")


def pytest_addoption(parser) -> None:
    """Add command line options for MCP integration."""
    group = parser.getgroup("mcp", "MCP integration options")
    group.addoption(
        "--mcp",
        action="store_true",
        default=False,
        help="Enable MCP server integration"
    )
    group.addoption(
        "--mcp-server",
        action="store",
        default=None,
        help="MCP server URL or connection string"
    )
    group.addoption(
        "--mcp-session-id",
        action="store",
        default=None,
        help="Custom session ID for MCP integration"
    )


def pytest_configure(config: Config) -> None:
    """Register the MCP plugin."""
    if config.getoption("--mcp"):
        config.pluginmanager.register(PytestMCPPlugin(config), "mcp_plugin")


def pytest_unconfigure(config: Config) -> None:
    """Unregister the MCP plugin."""
    plugin = getattr(config.pluginmanager, "_mcp_plugin", None)
    if plugin:
        config.pluginmanager.unregister(plugin)