"""Pydantic models for Dependency Check MCP Server."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class ScanProjectArgs(BaseModel):
    """Arguments for the scan_project tool."""
    
    path: str = Field(..., description="Path to project directory or file(s) to scan")
    output_format: Literal["JSON", "XML", "HTML", "CSV", "SARIF", "JUNIT", "JENKINS", "GITLAB", "ALL"] = Field(
        default="JSON",
        description="Output format for the scan report"
    )
    output_file: str = Field(
        ...,
        description="Path to the output file where scan results will be saved"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="Patterns to exclude from scanning"
    )
    fail_on_cvss: float = Field(
        default=11.0,
        description="CVSS score threshold to fail scan (0-10, default: 11 - never fail)",
        ge=0,
        le=11
    )
    suppression_files: Optional[List[str]] = Field(
        default=None,
        description="Paths to suppression files for false positives"
    )
    enable_experimental: bool = Field(
        default=False,
        description="Enable experimental analyzers"
    )
    nvd_api_key: Optional[str] = Field(
        default=None,
        description="NVD API key for faster updates"
    )
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Ensure path exists."""
        if not Path(v).exists():
            raise ValueError(f"Path '{v}' does not exist")
        return v
    
    @field_validator('output_file')
    @classmethod
    def validate_output_file(cls, v):
        """Ensure output directory exists."""
        output_path = Path(v)
        output_dir = output_path.parent
        if not output_dir.exists():
            raise ValueError(f"Output directory '{output_dir}' does not exist")
        return v


class UpdateDatabaseArgs(BaseModel):
    """Arguments for the update_database tool."""
    
    nvd_api_key: Optional[str] = Field(
        default=None,
        description="NVD API key for faster updates"
    )
    data_directory: str = Field(
        default="/data/dependency-check",
        description="Directory to store database"
    )
    proxy_server: Optional[str] = Field(
        default=None,
        description="Proxy server URL if needed"
    )
    proxy_port: Optional[int] = Field(
        default=None,
        description="Proxy port"
    )
    connection_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds",
        gt=0
    )


class CheckVulnerabilitiesArgs(BaseModel):
    """Arguments for the check_vulnerabilities tool."""
    
    report_path: str = Field(..., description="Path to existing scan report (JSON format)")
    cve_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific CVE IDs to check for"
    )
    min_cvss_score: float = Field(
        default=0.0,
        description="Minimum CVSS score to filter",
        ge=0,
        le=10
    )
    severity_levels: Optional[List[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]]] = Field(
        default=None,
        description="Filter by severity levels"
    )
    
    @field_validator('report_path')
    @classmethod
    def validate_report_path(cls, v):
        """Ensure report file exists."""
        if not Path(v).exists():
            raise ValueError(f"Report file '{v}' does not exist")
        return v


class GenerateSuppressionArgs(BaseModel):
    """Arguments for the generate_suppression tool."""
    
    report_path: str = Field(..., description="Path to scan report with false positives")
    output_file: str = Field(..., description="Path to save the suppression file")
    cpe_uri: Optional[str] = Field(default=None, description="CPE URI to suppress")
    cve_id: Optional[str] = Field(default=None, description="Specific CVE to suppress")
    file_path: Optional[str] = Field(default=None, description="File path pattern to suppress")
    notes: Optional[str] = Field(default=None, description="Notes about why this is suppressed")
    
    @field_validator('report_path')
    @classmethod
    def validate_report_path(cls, v):
        """Ensure report file exists."""
        if not Path(v).exists():
            raise ValueError(f"Report file '{v}' does not exist")
        return v


class GetScanSummaryArgs(BaseModel):
    """Arguments for the get_scan_summary tool."""
    
    report_path: str = Field(..., description="Path to scan report")
    group_by: Literal["severity", "dependency", "cve"] = Field(
        default="severity",
        description="Group results by severity, dependency, or CVE"
    )
    
    @field_validator('report_path')
    @classmethod
    def validate_report_path(cls, v):
        """Ensure report file exists."""
        if not Path(v).exists():
            raise ValueError(f"Report file '{v}' does not exist")
        return v


class VulnerabilityInfo(BaseModel):
    """Information about a vulnerability."""
    
    cve_id: str
    description: str
    severity: str
    cvss_score: Optional[float] = None
    cpe_uri: Optional[str] = None
    affected_file: Optional[str] = None


class ScanResult(BaseModel):
    """Result of a scan operation."""
    
    success: bool
    report_path: str
    total_dependencies: int
    vulnerable_dependencies: int
    total_vulnerabilities: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_time_seconds: float
    error_message: Optional[str] = None


class DatabaseUpdateResult(BaseModel):
    """Result of database update operation."""
    
    success: bool
    last_updated: str
    update_duration_seconds: float
    error_message: Optional[str] = None


class VulnerabilityCheckResult(BaseModel):
    """Result of vulnerability check."""
    
    found_vulnerabilities: List[VulnerabilityInfo]
    total_found: int
    matches_criteria: bool