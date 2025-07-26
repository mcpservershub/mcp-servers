"""MCP Server implementation for OWASP Dependency Check using FastMCP."""

import asyncio
import logging
from typing import Any, Dict

from mcp.server import FastMCP
from pydantic import ValidationError

from .models import (
    ScanProjectArgs,
    UpdateDatabaseArgs,
    CheckVulnerabilitiesArgs,
    GenerateSuppressionArgs,
    GetScanSummaryArgs
)
from .tools import DependencyCheckTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP instance
mcp = FastMCP("dependency-check")

# Initialize tools lazily
_dc_tools = None

def get_dc_tools():
    """Get or create DependencyCheckTools instance."""
    global _dc_tools
    if _dc_tools is None:
        _dc_tools = DependencyCheckTools()
    return _dc_tools


@mcp.tool()
async def scan_project(
    path: str,
    output_file: str,
    output_format: str = "JSON",
    exclude_patterns: list[str] | None = None,
    fail_on_cvss: float = 11.0,
    suppression_files: list[str] | None = None,
    enable_experimental: bool = False,
    nvd_api_key: str | None = None
) -> str:
    """
    Scan a project directory or files for known vulnerabilities using OWASP Dependency Check.
    
    Args:
        path: Path to project directory or file(s) to scan
        output_file: Path to the output file where scan results will be saved
        output_format: Output format (JSON, XML, HTML, CSV, SARIF, JUNIT, JENKINS, GITLAB, ALL)
        exclude_patterns: Patterns to exclude from scanning (e.g., '**/node_modules/**')
        fail_on_cvss: CVSS score threshold to fail scan (0-10, default: 11 - never fail)
        suppression_files: Paths to suppression files for false positives
        enable_experimental: Enable experimental analyzers
        nvd_api_key: NVD API key for faster updates
    
    Returns:
        Summary of scan results
    """
    try:
        args = ScanProjectArgs(
            path=path,
            output_file=output_file,
            output_format=output_format,
            exclude_patterns=exclude_patterns,
            fail_on_cvss=fail_on_cvss,
            suppression_files=suppression_files,
            enable_experimental=enable_experimental,
            nvd_api_key=nvd_api_key
        )
        
        result = await get_dc_tools().scan_project(args)
        
        return (
            f"Scan completed successfully. Report saved to: {output_file}\n\n"
            f"Summary:\n"
            f"- Total dependencies: {result['total_dependencies']}\n"
            f"- Vulnerable dependencies: {result['vulnerable_dependencies']}\n"
            f"- Total vulnerabilities: {result['total_vulnerabilities']}\n"
            f"- Critical: {result['critical_count']}\n"
            f"- High: {result['high_count']}\n"
            f"- Medium: {result['medium_count']}\n"
            f"- Low: {result['low_count']}\n"
            f"- Detected languages: {', '.join(result.get('detected_languages', []))}\n"
            f"- Scan time: {result['scan_time_seconds']:.2f} seconds"
        )
    except ValidationError as e:
        error_details = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"Invalid arguments:\n{error_details}"
    except Exception as e:
        logger.error(f"Error in scan_project: {str(e)}", exc_info=True)
        return f"Error executing scan: {str(e)}"


@mcp.tool()
async def update_database(
    nvd_api_key: str | None = None,
    data_directory: str = "/data/dependency-check",
    proxy_server: str | None = None,
    proxy_port: int | None = None,
    connection_timeout: int = 30
) -> str:
    """
    Update the vulnerability database from NVD and other sources.
    
    Args:
        nvd_api_key: NVD API key for faster updates
        data_directory: Directory to store database
        proxy_server: Proxy server URL if needed
        proxy_port: Proxy port
        connection_timeout: Connection timeout in seconds
    
    Returns:
        Update status message
    """
    try:
        args = UpdateDatabaseArgs(
            nvd_api_key=nvd_api_key,
            data_directory=data_directory,
            proxy_server=proxy_server,
            proxy_port=proxy_port,
            connection_timeout=connection_timeout
        )
        
        result = await get_dc_tools().update_database(args)
        
        if result['success']:
            return (
                f"Database update completed successfully.\n"
                f"Last updated: {result['last_updated']}\n"
                f"Update duration: {result['update_duration_seconds']:.2f} seconds"
            )
        else:
            return f"Database update failed: {result['error_message']}"
    except Exception as e:
        logger.error(f"Error in update_database: {str(e)}", exc_info=True)
        return f"Error updating database: {str(e)}"


@mcp.tool()
async def check_vulnerabilities(
    report_path: str,
    cve_ids: list[str] | None = None,
    min_cvss_score: float = 0.0,
    severity_levels: list[str] | None = None
) -> str:
    """
    Check for specific vulnerabilities or CVEs in scan results.
    
    Args:
        report_path: Path to existing scan report (JSON format)
        cve_ids: Specific CVE IDs to check for
        min_cvss_score: Minimum CVSS score to filter
        severity_levels: Filter by severity levels (LOW, MEDIUM, HIGH, CRITICAL)
    
    Returns:
        Found vulnerabilities matching criteria
    """
    try:
        args = CheckVulnerabilitiesArgs(
            report_path=report_path,
            cve_ids=cve_ids,
            min_cvss_score=min_cvss_score,
            severity_levels=severity_levels
        )
        
        result = await get_dc_tools().check_vulnerabilities(args)
        
        if result['total_found'] == 0:
            return "No vulnerabilities found matching the specified criteria."
        
        text = f"Found {result['total_found']} vulnerabilities matching criteria:\n\n"
        for vuln in result['found_vulnerabilities'][:10]:  # Show first 10
            text += f"- {vuln['cve_id']} ({vuln['severity']})"
            if vuln.get('cvss_score'):
                text += f" - CVSS: {vuln['cvss_score']}"
            text += f"\n  File: {vuln.get('affected_file', 'Unknown')}\n"
        
        if result['total_found'] > 10:
            text += f"\n... and {result['total_found'] - 10} more vulnerabilities"
        
        return text
    except ValidationError as e:
        error_details = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"Invalid arguments:\n{error_details}"
    except Exception as e:
        logger.error(f"Error in check_vulnerabilities: {str(e)}", exc_info=True)
        return f"Error checking vulnerabilities: {str(e)}"


@mcp.tool()
async def generate_suppression(
    report_path: str,
    output_file: str,
    cpe_uri: str | None = None,
    cve_id: str | None = None,
    file_path: str | None = None,
    notes: str | None = None
) -> str:
    """
    Generate suppression rules for false positives.
    
    Args:
        report_path: Path to scan report with false positives
        output_file: Path to save the suppression file
        cpe_uri: CPE URI to suppress
        cve_id: Specific CVE to suppress
        file_path: File path pattern to suppress
        notes: Notes about why this is suppressed
    
    Returns:
        Status of suppression file generation
    """
    try:
        args = GenerateSuppressionArgs(
            report_path=report_path,
            output_file=output_file,
            cpe_uri=cpe_uri,
            cve_id=cve_id,
            file_path=file_path,
            notes=notes
        )
        
        result = await get_dc_tools().generate_suppression(args)
        return f"Suppression file generated successfully: {result['suppression_file']}"
    except ValidationError as e:
        error_details = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"Invalid arguments:\n{error_details}"
    except Exception as e:
        logger.error(f"Error in generate_suppression: {str(e)}", exc_info=True)
        return f"Error generating suppression: {str(e)}"


@mcp.tool()
async def get_scan_summary(
    report_path: str,
    group_by: str = "severity"
) -> str:
    """
    Get a summary of vulnerabilities from a scan report.
    
    Args:
        report_path: Path to scan report
        group_by: Group results by 'severity', 'dependency', or 'cve'
    
    Returns:
        Summary of vulnerabilities
    """
    try:
        args = GetScanSummaryArgs(
            report_path=report_path,
            group_by=group_by
        )
        
        result = await get_dc_tools().get_scan_summary(args)
        
        text = f"Scan Summary:\n"
        text += f"- Total dependencies: {result['total_dependencies']}\n"
        text += f"- Vulnerable dependencies: {result['vulnerable_dependencies']}\n"
        text += f"- Total vulnerabilities: {result['total_vulnerabilities']}\n\n"
        
        text += "Severity breakdown:\n"
        for severity, count in result['severity_breakdown'].items():
            text += f"- {severity}: {count}\n"
        
        text += f"\nGrouped by {result['group_by']}:\n"
        for group_name, group_data in list(result['groups'].items())[:5]:
            if result['group_by'] == 'severity':
                text += f"- {group_name}: {group_data['count']} vulnerabilities\n"
            elif result['group_by'] == 'dependency':
                text += f"- {group_name}: {group_data['count']} vulnerabilities\n"
            elif result['group_by'] == 'cve':
                text += f"- {group_name} ({group_data['severity']}): "
                text += f"{len(group_data['affected_dependencies'])} affected files\n"
        
        if len(result['groups']) > 5:
            text += f"... and {len(result['groups']) - 5} more groups"
        
        return text
    except ValidationError as e:
        error_details = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"Invalid arguments:\n{error_details}"
    except Exception as e:
        logger.error(f"Error in get_scan_summary: {str(e)}", exc_info=True)
        return f"Error getting summary: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Dependency Check MCP Server with FastMCP")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()