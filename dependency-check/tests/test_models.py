"""Tests for Pydantic models."""

import pytest
from pathlib import Path
import tempfile

from dependency_check_mcp.models import (
    ScanProjectArgs,
    UpdateDatabaseArgs,
    CheckVulnerabilitiesArgs,
    GenerateSuppressionArgs,
    GetScanSummaryArgs,
    VulnerabilityInfo,
    ScanResult
)


class TestScanProjectArgs:
    """Test ScanProjectArgs model validation."""
    
    def test_valid_scan_args(self, tmp_path):
        """Test creating valid scan arguments."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        output_file = tmp_path / "output.json"
        
        args = ScanProjectArgs(
            path=str(project_path),
            output_file=str(output_file),
            output_format="JSON",
            fail_on_cvss=7.0
        )
        
        assert args.path == str(project_path)
        assert args.output_file == str(output_file)
        assert args.output_format == "JSON"
        assert args.fail_on_cvss == 7.0
    
    def test_invalid_path(self, tmp_path):
        """Test validation error for non-existent path."""
        output_file = tmp_path / "output.json"
        
        with pytest.raises(ValueError, match="does not exist"):
            ScanProjectArgs(
                path="/non/existent/path",
                output_file=str(output_file)
            )
    
    def test_invalid_output_dir(self, tmp_path):
        """Test validation error for non-existent output directory."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        
        with pytest.raises(ValueError, match="Output directory"):
            ScanProjectArgs(
                path=str(project_path),
                output_file="/non/existent/dir/output.json"
            )
    
    def test_invalid_cvss_score(self, tmp_path):
        """Test validation error for invalid CVSS score."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        output_file = tmp_path / "output.json"
        
        with pytest.raises(ValueError):
            ScanProjectArgs(
                path=str(project_path),
                output_file=str(output_file),
                fail_on_cvss=12.0  # Invalid: > 11
            )
    
    def test_default_values(self, tmp_path):
        """Test default values for optional fields."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        output_file = tmp_path / "output.json"
        
        args = ScanProjectArgs(
            path=str(project_path),
            output_file=str(output_file)
        )
        
        assert args.output_format == "JSON"
        assert args.fail_on_cvss == 11.0
        assert args.enable_experimental is False
        assert args.exclude_patterns is None
        assert args.suppression_files is None


class TestUpdateDatabaseArgs:
    """Test UpdateDatabaseArgs model validation."""
    
    def test_valid_update_args(self):
        """Test creating valid update arguments."""
        args = UpdateDatabaseArgs(
            nvd_api_key="test-key",
            data_directory="/custom/data",
            connection_timeout=60
        )
        
        assert args.nvd_api_key == "test-key"
        assert args.data_directory == "/custom/data"
        assert args.connection_timeout == 60
    
    def test_default_values(self):
        """Test default values."""
        args = UpdateDatabaseArgs()
        
        assert args.data_directory == "/data/dependency-check"
        assert args.connection_timeout == 30
        assert args.nvd_api_key is None
        assert args.proxy_server is None


class TestCheckVulnerabilitiesArgs:
    """Test CheckVulnerabilitiesArgs model validation."""
    
    def test_valid_check_args(self, tmp_path):
        """Test creating valid check arguments."""
        report_file = tmp_path / "report.json"
        report_file.write_text("{}")
        
        args = CheckVulnerabilitiesArgs(
            report_path=str(report_file),
            cve_ids=["CVE-2021-12345"],
            min_cvss_score=5.0,
            severity_levels=["HIGH", "CRITICAL"]
        )
        
        assert args.report_path == str(report_file)
        assert args.cve_ids == ["CVE-2021-12345"]
        assert args.min_cvss_score == 5.0
        assert args.severity_levels == ["HIGH", "CRITICAL"]
    
    def test_invalid_report_path(self):
        """Test validation error for non-existent report."""
        with pytest.raises(ValueError, match="does not exist"):
            CheckVulnerabilitiesArgs(
                report_path="/non/existent/report.json"
            )


class TestVulnerabilityInfo:
    """Test VulnerabilityInfo model."""
    
    def test_vulnerability_info(self):
        """Test creating vulnerability info."""
        vuln = VulnerabilityInfo(
            cve_id="CVE-2021-12345",
            description="Test vulnerability",
            severity="HIGH",
            cvss_score=8.5,
            cpe_uri="cpe:/a:vendor:product:1.0",
            affected_file="lib.jar"
        )
        
        assert vuln.cve_id == "CVE-2021-12345"
        assert vuln.severity == "HIGH"
        assert vuln.cvss_score == 8.5


class TestScanResult:
    """Test ScanResult model."""
    
    def test_successful_scan_result(self):
        """Test creating successful scan result."""
        result = ScanResult(
            success=True,
            report_path="/output/report.json",
            total_dependencies=50,
            vulnerable_dependencies=5,
            total_vulnerabilities=10,
            critical_count=1,
            high_count=3,
            medium_count=4,
            low_count=2,
            scan_time_seconds=45.5
        )
        
        assert result.success is True
        assert result.total_dependencies == 50
        assert result.vulnerable_dependencies == 5
        assert result.total_vulnerabilities == 10
        assert result.error_message is None
    
    def test_failed_scan_result(self):
        """Test creating failed scan result."""
        result = ScanResult(
            success=False,
            report_path="/output/report.json",
            total_dependencies=0,
            vulnerable_dependencies=0,
            total_vulnerabilities=0,
            scan_time_seconds=2.5,
            error_message="Scan failed: Invalid project"
        )
        
        assert result.success is False
        assert result.error_message == "Scan failed: Invalid project"