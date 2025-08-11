"""Tests for Hurl MCP Server."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from hurl_mcp.server import (
    run_hurl_command,
    run_hurl,
    run_hurl_test,
    run_hurl_with_variables,
    validate_hurl,
    create_hurl_file
)


class TestRunHurlCommand:
    """Test run_hurl_command function."""
    
    @patch('subprocess.run')
    def test_successful_command(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr=""
        )
        
        result = run_hurl_command(["test.hurl"])
        
        assert result["success"] is True
        assert result["stdout"] == "Success"
        assert result["stderr"] == ""
        assert result["returncode"] == 0
        
        # Check that hurl was prepended
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["hurl", "test.hurl"]
    
    @patch('subprocess.run')
    def test_failed_command(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error occurred"
        )
        
        result = run_hurl_command(["test.hurl"])
        
        assert result["success"] is False
        assert result["stderr"] == "Error occurred"
        assert result["returncode"] == 1
    
    @patch('subprocess.run')
    def test_hurl_not_found(self, mock_run):
        """Test when hurl is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = run_hurl_command(["test.hurl"])
        
        assert result["success"] is False
        assert "not found" in result["stderr"]
        assert result["returncode"] == -1


class TestRunHurl:
    """Test run_hurl function."""
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_basic_run(self, mock_run):
        """Test basic hurl execution."""
        mock_run.return_value = {
            "success": True,
            "stdout": "Response body",
            "stderr": "",
            "returncode": 0
        }
        
        result = run_hurl("test.hurl")
        
        mock_run.assert_called_once_with(["test.hurl"])
        assert result["success"] is True
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_run_with_output_file(self, mock_run):
        """Test hurl execution with output file."""
        mock_run.return_value = {
            "success": True,
            "stdout": "Response body",
            "stderr": "",
            "returncode": 0
        }
        
        result = run_hurl("test.hurl", output_file="/tmp/output.txt")
        
        expected_args = ["--output", "/tmp/output.txt", "test.hurl"]
        mock_run.assert_called_once_with(expected_args)
        assert result["success"] is True
        assert result["output_file"] == "/tmp/output.txt"
        assert "Output saved to" in result["message"]
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_run_with_options(self, mock_run):
        """Test hurl execution with various options."""
        mock_run.return_value = {
            "success": True,
            "stdout": "Response",
            "stderr": "",
            "returncode": 0
        }
        
        result = run_hurl(
            "test.hurl",
            verbose=True,
            insecure=True,
            location=True,
            max_time=30
        )
        
        expected_args = [
            "--verbose",
            "--insecure",
            "--location",
            "--max-time", "30",
            "test.hurl"
        ]
        mock_run.assert_called_once_with(expected_args)
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_json_output(self, mock_run):
        """Test JSON output parsing."""
        json_output = {"entries": [{"response": {"status": 200}}]}
        mock_run.return_value = {
            "success": True,
            "stdout": json.dumps(json_output),
            "stderr": "",
            "returncode": 0
        }
        
        result = run_hurl("test.hurl", output_format="json")
        
        assert "--json" in mock_run.call_args[0][0]
        assert result["parsed_output"] == json_output


class TestRunHurlTest:
    """Test run_hurl_test function."""
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_test_mode(self, mock_run):
        """Test hurl in test mode."""
        mock_run.return_value = {
            "success": True,
            "stdout": "Tests passed",
            "stderr": "",
            "returncode": 0
        }
        
        result = run_hurl_test("tests/")
        
        assert "--test" in mock_run.call_args[0][0]
        assert "tests/" in mock_run.call_args[0][0]
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_with_reports(self, mock_run):
        """Test with various report formats."""
        mock_run.return_value = {"success": True, "stdout": "", "stderr": "", "returncode": 0}
        
        # Test HTML report
        run_hurl_test("test.hurl", report_format="html", report_path="/tmp/report")
        assert "--report-html" in mock_run.call_args[0][0]
        
        # Test JSON report
        run_hurl_test("test.hurl", report_format="json", report_path="/tmp/report")
        assert "--report-json" in mock_run.call_args[0][0]
        
        # Test JUnit report
        run_hurl_test("test.hurl", report_format="junit", report_path="/tmp/report.xml")
        assert "--report-junit" in mock_run.call_args[0][0]
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_parallel_execution(self, mock_run):
        """Test parallel execution options."""
        mock_run.return_value = {"success": True, "stdout": "", "stderr": "", "returncode": 0}
        
        run_hurl_test("tests/", parallel=True, jobs=4)
        
        args = mock_run.call_args[0][0]
        assert "--parallel" in args
        assert "--jobs" in args
        assert "4" in args


class TestRunHurlWithVariables:
    """Test run_hurl_with_variables function."""
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_with_variables(self, mock_run):
        """Test with variable dictionary."""
        mock_run.return_value = {"success": True, "stdout": "", "stderr": "", "returncode": 0}
        
        variables = {
            "base_url": "https://api.example.com",
            "api_key": "secret123"
        }
        
        run_hurl_with_variables("test.hurl", variables)
        
        args = mock_run.call_args[0][0]
        assert "--variable" in args
        assert "base_url=https://api.example.com" in args
        assert "api_key=secret123" in args


class TestValidateHurl:
    """Test validate_hurl function."""
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_valid_hurl(self, mock_run):
        """Test valid hurl content."""
        mock_run.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }
        
        hurl_content = """
GET https://example.com
HTTP 200
"""
        
        result = validate_hurl(hurl_content)
        
        assert result["valid"] is True
        assert result["errors"] is None
    
    @patch('hurl_mcp.server.run_hurl_command')
    def test_invalid_hurl(self, mock_run):
        """Test invalid hurl content."""
        mock_run.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "error: parsing error at line 2",
            "returncode": 1
        }
        
        result = validate_hurl("INVALID CONTENT")
        
        assert result["valid"] is False
        assert "error:" in result["errors"]


class TestCreateHurlFile:
    """Test create_hurl_file function."""
    
    def test_create_file(self):
        """Test creating a hurl file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.hurl"
            content = "GET https://example.com\nHTTP 200"
            
            result = create_hurl_file(str(file_path), content)
            
            assert result["success"] is True
            assert file_path.exists()
            assert file_path.read_text() == content
    
    def test_create_file_with_subdirs(self):
        """Test creating file in non-existent subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "test.hurl"
            content = "GET https://example.com"
            
            result = create_hurl_file(str(file_path), content)
            
            assert result["success"] is True
            assert file_path.exists()
    
    @patch('pathlib.Path.write_text')
    def test_create_file_error(self, mock_write):
        """Test error handling when creating file."""
        mock_write.side_effect = PermissionError("No permission")
        
        result = create_hurl_file("/invalid/path.hurl", "content")
        
        assert result["success"] is False
        assert "Failed to create" in result["message"]