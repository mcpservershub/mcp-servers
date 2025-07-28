"""Dependency Check CLI wrapper for scanning operations."""

import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess

from .models import ScanResult

logger = logging.getLogger(__name__)


class DependencyCheckScanner:
    """Wrapper for Dependency Check CLI operations."""
    
    def __init__(self, dependency_check_home: Optional[str] = None):
        """Initialize scanner with Dependency Check installation path."""
        self.dc_home = dependency_check_home or os.environ.get(
            "DEPENDENCY_CHECK_HOME", "/opt/dependency-check"
        )
        self.dc_binary = self._find_binary()
        
    def _find_binary(self) -> str:
        """Find the dependency-check binary."""
        possible_paths = [
            Path(self.dc_home) / "bin" / "dependency-check.sh",
            Path(self.dc_home) / "bin" / "dependency-check.bat",
            Path("/usr/local/bin/dependency-check"),
            Path("/usr/bin/dependency-check"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
                
        # Try to find in PATH
        dc_in_path = shutil.which("dependency-check")
        if dc_in_path:
            return dc_in_path
            
        raise RuntimeError(
            f"Dependency Check binary not found. Searched in: {possible_paths}"
        )
    
    async def scan(
        self,
        path: str,
        output_format: str,
        output_file: str,
        exclude_patterns: Optional[List[str]] = None,
        fail_on_cvss: float = 11.0,
        suppression_files: Optional[List[str]] = None,
        enable_experimental: bool = False,
        nvd_api_key: Optional[str] = None,
        additional_args: Optional[List[str]] = None,
    ) -> ScanResult:
        """
        Run a dependency check scan.
        
        Args:
            path: Path to scan
            output_format: Output format
            output_file: Output file path
            exclude_patterns: Patterns to exclude
            fail_on_cvss: CVSS threshold
            suppression_files: Suppression file paths
            enable_experimental: Enable experimental analyzers
            nvd_api_key: NVD API key
            additional_args: Additional CLI arguments
            
        Returns:
            ScanResult with scan details
        """
        start_time = time.time()
        
        # Check if binary exists and is executable
        if not Path(self.dc_binary).exists():
            logger.error(f"Dependency Check binary not found at: {self.dc_binary}")
            return ScanResult(
                success=False,
                report_path=output_file,
                total_dependencies=0,
                vulnerable_dependencies=0,
                total_vulnerabilities=0,
                scan_time_seconds=time.time() - start_time,
                error_message=f"Dependency Check binary not found at: {self.dc_binary}",
            )
        
        # Check if binary is executable
        if not os.access(self.dc_binary, os.X_OK):
            logger.error(f"Dependency Check binary not executable: {self.dc_binary}")
            return ScanResult(
                success=False,
                report_path=output_file,
                total_dependencies=0,
                vulnerable_dependencies=0,
                total_vulnerabilities=0,
                scan_time_seconds=time.time() - start_time,
                error_message=f"Dependency Check binary not executable: {self.dc_binary}",
            )
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build command
        cmd = [self.dc_binary]
        
        # Required arguments
        cmd.extend(["--scan", path])
        cmd.extend(["--format", output_format])
        # Use the full output path directly
        cmd.extend(["--out", str(output_path)])
        cmd.extend(["--project", output_path.stem])
        
        # Add prettyPrint for better output
        if output_format in ["JSON", "XML"]:
            cmd.append("--prettyPrint")
        
        # Add data directory if specified
        if os.environ.get("DEPENDENCY_CHECK_DATA"):
            cmd.extend(["--data", os.environ.get("DEPENDENCY_CHECK_DATA")])
        
        # Optional arguments
        if fail_on_cvss < 11:
            cmd.extend(["--failOnCVSS", str(fail_on_cvss)])
            
        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])
                
        if suppression_files:
            for supp_file in suppression_files:
                cmd.extend(["--suppression", supp_file])
                
        if enable_experimental:
            cmd.append("--enableExperimental")
            
        if nvd_api_key:
            cmd.extend(["--nvdApiKey", nvd_api_key])
        
        # Check if database exists to decide on auto-update
        data_dir = Path(os.environ.get("DEPENDENCY_CHECK_DATA", str(Path.home() / ".dependency-check" / "data")))
        db_file = Path(data_dir) / "odc.mv.db"
        has_database = db_file.exists()
        
        # Disable auto-update if running in container (should be done separately)
        # or if database already exists (to speed up scans)
        if os.environ.get("DISABLE_AUTO_UPDATE", "false").lower() == "true" or has_database:
            cmd.append("--noupdate")
            
        if additional_args:
            cmd.extend(additional_args)
        
        # Run scan
        logger.info(f"Running dependency check scan: {' '.join(cmd)}")
        
        try:
            # Log full command for debugging
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            # For long-running scans, we need to handle timeouts better
            # First check if this is the first run (database needs downloading)
            first_run = not data_dir.exists() or not any(data_dir.iterdir()) if data_dir.exists() else True
            
            if first_run:
                logger.warning("First run detected. Dependency Check will download vulnerability databases.")
                logger.warning("This can take 5-30 minutes depending on your connection speed.")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "JAVA_OPTS": "-Xmx4G"}  # Increase memory for large scans
            )
            
            # Use a longer timeout for first run or large scans
            timeout = 1800 if first_run else 600  # 30 minutes for first run, 10 minutes otherwise
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Scan timed out after {timeout} seconds")
                process.terminate()
                await process.wait()
                return ScanResult(
                    success=False,
                    report_path=output_file,
                    total_dependencies=0,
                    vulnerable_dependencies=0,
                    total_vulnerabilities=0,
                    scan_time_seconds=timeout,
                    error_message=f"Scan timed out after {timeout} seconds. Try increasing timeout or scanning smaller directories.",
                )
            
            scan_time = time.time() - start_time
            
            # Log output for debugging
            if stdout:
                logger.debug(f"Stdout: {stdout.decode()[:500]}...")
            if stderr:
                logger.debug(f"Stderr: {stderr.decode()[:500]}...")
            
            logger.info(f"Scan completed with return code: {process.returncode}")
            
            if process.returncode != 0 and fail_on_cvss < 11:
                # Check if it failed due to CVSS threshold
                if "One or more dependencies were identified with vulnerabilities" in stderr.decode():
                    logger.warning(f"Scan found vulnerabilities above CVSS threshold {fail_on_cvss}")
                else:
                    error_msg = stderr.decode() if stderr else stdout.decode()
                    logger.error(f"Scan failed: {error_msg}")
                    return ScanResult(
                        success=False,
                        report_path=output_file,
                        total_dependencies=0,
                        vulnerable_dependencies=0,
                        total_vulnerabilities=0,
                        scan_time_seconds=scan_time,
                        error_message=error_msg,
                    )
            
            # Check if output file was created
            # When using --out with a file path, dependency-check creates the exact file
            expected_files = [
                output_file
            ]
            
            actual_output_file = None
            for file_path in expected_files:
                if Path(file_path).exists():
                    actual_output_file = file_path
                    break
            
            if not actual_output_file:
                logger.error(f"Output file not created. Checked: {expected_files}")
                logger.error(f"Stdout: {stdout.decode() if stdout else 'No stdout'}")
                logger.error(f"Stderr: {stderr.decode() if stderr else 'No stderr'}")
                
                # List files in output directory
                if output_path.parent.exists():
                    logger.error(f"Files in output directory: {list(output_path.parent.iterdir())}")
                
                # Return minimal success result if no output file
                return ScanResult(
                    success=False,
                    report_path=output_file,
                    total_dependencies=0,
                    vulnerable_dependencies=0,
                    total_vulnerabilities=0,
                    scan_time_seconds=scan_time,
                    error_message="Scan completed but no output file was generated. The scan may have failed silently.",
                )
            
            # Copy to expected location if different
            if str(actual_output_file) != output_file:
                shutil.copy2(actual_output_file, output_file)
                logger.info(f"Copied output from {actual_output_file} to {output_file}")
            
            # Parse results if JSON format
            result = self._parse_scan_results(output_file, output_format)
            result.scan_time_seconds = scan_time
            result.report_path = output_file
            result.success = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")
            return ScanResult(
                success=False,
                report_path=output_file,
                total_dependencies=0,
                vulnerable_dependencies=0,
                total_vulnerabilities=0,
                scan_time_seconds=time.time() - start_time,
                error_message=str(e),
            )
    
    def _parse_scan_results(self, output_file: str, output_format: str) -> ScanResult:
        """Parse scan results from output file."""
        if output_format != "JSON":
            # For non-JSON formats, return basic info
            return ScanResult(
                success=True,
                report_path=output_file,
                total_dependencies=0,
                vulnerable_dependencies=0,
                total_vulnerabilities=0,
                scan_time_seconds=0,
            )
        
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            total_deps = len(data.get("dependencies", []))
            vulnerable_deps = 0
            total_vulns = 0
            critical = high = medium = low = 0
            
            for dep in data.get("dependencies", []):
                vulns = dep.get("vulnerabilities", [])
                if vulns:
                    vulnerable_deps += 1
                    total_vulns += len(vulns)
                    
                    for vuln in vulns:
                        severity = vuln.get("severity", "").upper()
                        if severity == "CRITICAL":
                            critical += 1
                        elif severity == "HIGH":
                            high += 1
                        elif severity == "MEDIUM":
                            medium += 1
                        elif severity == "LOW":
                            low += 1
            
            return ScanResult(
                success=True,
                report_path=output_file,
                total_dependencies=total_deps,
                vulnerable_dependencies=vulnerable_deps,
                total_vulnerabilities=total_vulns,
                critical_count=critical,
                high_count=high,
                medium_count=medium,
                low_count=low,
                scan_time_seconds=0,
            )
            
        except Exception as e:
            logger.warning(f"Could not parse scan results: {str(e)}")
            return ScanResult(
                success=True,
                report_path=output_file,
                total_dependencies=0,
                vulnerable_dependencies=0,
                total_vulnerabilities=0,
                scan_time_seconds=0,
            )
    
    async def update_database(
        self,
        nvd_api_key: Optional[str] = None,
        data_directory: Optional[str] = None,
        proxy_server: Optional[str] = None,
        proxy_port: Optional[int] = None,
        connection_timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Update the vulnerability database.
        
        Args:
            nvd_api_key: NVD API key
            data_directory: Data directory path
            proxy_server: Proxy server
            proxy_port: Proxy port
            connection_timeout: Connection timeout
            
        Returns:
            Update result dictionary
        """
        start_time = time.time()
        
        cmd = [self.dc_binary, "--updateonly"]
        
        if nvd_api_key:
            cmd.extend(["--nvdApiKey", nvd_api_key])
            
        if data_directory:
            cmd.extend(["--data", data_directory])
            
        if proxy_server:
            cmd.extend(["--proxyserver", proxy_server])
            
        if proxy_port:
            cmd.extend(["--proxyport", str(proxy_port)])
            
        if connection_timeout:
            cmd.extend(["--connectiontimeout", str(connection_timeout)])
        
        logger.info(f"Updating vulnerability database: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "JAVA_OPTS": "-Xmx4G"}
            )
            
            # Database updates can take a very long time
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=3600  # 1 hour timeout for database updates
                )
            except asyncio.TimeoutError:
                logger.error("Database update timed out after 1 hour")
                process.terminate()
                await process.wait()
                return {
                    "success": False,
                    "last_updated": "",
                    "update_duration_seconds": 3600,
                    "error_message": "Database update timed out after 1 hour",
                }
            
            update_time = time.time() - start_time
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.error(f"Database update failed: {error_msg}")
                return {
                    "success": False,
                    "last_updated": "",
                    "update_duration_seconds": update_time,
                    "error_message": error_msg,
                }
            
            return {
                "success": True,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "update_duration_seconds": update_time,
                "error_message": None,
            }
            
        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            return {
                "success": False,
                "last_updated": "",
                "update_duration_seconds": time.time() - start_time,
                "error_message": str(e),
            }