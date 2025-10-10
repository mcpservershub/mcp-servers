"""MCP Tools implementation for Dependency Check operations."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

from .models import (
    ScanProjectArgs,
    UpdateDatabaseArgs,
    CheckVulnerabilitiesArgs,
    GenerateSuppressionArgs,
    GetScanSummaryArgs,
    ScanResult,
    DatabaseUpdateResult,
    VulnerabilityCheckResult,
    VulnerabilityInfo
)
from .scanner import DependencyCheckScanner
from .language_support import LanguageDetector

logger = logging.getLogger(__name__)


class DependencyCheckTools:
    """Implementation of MCP tools for Dependency Check."""
    
    def __init__(self, scanner: Optional[DependencyCheckScanner] = None):
        """Initialize tools with scanner instance."""
        self.scanner = scanner or DependencyCheckScanner()
        self.language_detector = LanguageDetector()
    
    async def scan_project(self, args: ScanProjectArgs) -> Dict[str, Any]:
        """
        Scan a project for vulnerabilities.
        
        Args:
            args: Scan configuration arguments
            
        Returns:
            Scan results dictionary
        """
        logger.info(f"Starting scan for project: {args.path}")
        
        # Detect languages and get recommendations
        recommendations = self.language_detector.get_scan_recommendations(args.path)
        
        # Merge exclude patterns
        exclude_patterns = list(set(
            (args.exclude_patterns or []) + recommendations['exclude_patterns']
        ))
        
        # Get additional language-specific arguments
        additional_args = self.language_detector.get_additional_args(
            recommendations['detected_languages'],
            args.enable_experimental
        )
        
        # Run scan
        result = await self.scanner.scan(
            path=args.path,
            output_format=args.output_format,
            output_file=args.output_file,
            exclude_patterns=exclude_patterns,
            fail_on_cvss=args.fail_on_cvss,
            suppression_files=args.suppression_files,
            enable_experimental=args.enable_experimental,
            nvd_api_key=args.nvd_api_key,
            additional_args=additional_args,
        )
        
        # Add language information to result
        result_dict = result.model_dump()
        result_dict['detected_languages'] = recommendations['detected_languages']
        result_dict['supported_languages'] = recommendations['supported_languages']
        
        logger.info(f"Scan completed. Report saved to: {args.output_file}")
        return result_dict
    
    async def update_database(self, args: UpdateDatabaseArgs) -> Dict[str, Any]:
        """
        Update the vulnerability database.
        
        Args:
            args: Database update configuration
            
        Returns:
            Update result dictionary
        """
        logger.info("Starting vulnerability database update")
        
        result = await self.scanner.update_database(
            nvd_api_key=args.nvd_api_key,
            data_directory=args.data_directory,
            proxy_server=args.proxy_server,
            proxy_port=args.proxy_port,
            connection_timeout=args.connection_timeout,
        )
        
        logger.info(f"Database update completed: {result}")
        return result
    
    async def check_vulnerabilities(self, args: CheckVulnerabilitiesArgs) -> Dict[str, Any]:
        """
        Check for specific vulnerabilities in a scan report.
        
        Args:
            args: Vulnerability check configuration
            
        Returns:
            Check results dictionary
        """
        logger.info(f"Checking vulnerabilities in report: {args.report_path}")
        
        # Read the report
        report_path = Path(args.report_path)
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {args.report_path}")
        
        if not report_path.suffix == '.json':
            raise ValueError("Only JSON format reports are supported for vulnerability checking")
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        found_vulnerabilities = []
        
        # Search through dependencies
        for dependency in report_data.get('dependencies', []):
            for vuln in dependency.get('vulnerabilities', []):
                # Check filters
                cve_id = vuln.get('name', '')
                severity = vuln.get('severity', '').upper()
                cvss_score = None
                
                # Try to get CVSS score
                if 'cvssv3' in vuln:
                    cvss_score = vuln['cvssv3'].get('baseScore')
                elif 'cvssv2' in vuln:
                    cvss_score = vuln['cvssv2'].get('score')
                
                # Apply filters
                if args.cve_ids and cve_id not in args.cve_ids:
                    continue
                
                if args.severity_levels and severity not in args.severity_levels:
                    continue
                
                if cvss_score is not None and cvss_score < args.min_cvss_score:
                    continue
                
                # Add to results
                vuln_info = VulnerabilityInfo(
                    cve_id=cve_id,
                    description=vuln.get('description', ''),
                    severity=severity,
                    cvss_score=cvss_score,
                    cpe_uri=dependency.get('evidenceCollected', {}).get('identifiers', [{}])[0].get('name', ''),
                    affected_file=dependency.get('fileName', '')
                )
                found_vulnerabilities.append(vuln_info)
        
        result = VulnerabilityCheckResult(
            found_vulnerabilities=found_vulnerabilities,
            total_found=len(found_vulnerabilities),
            matches_criteria=len(found_vulnerabilities) > 0
        )
        
        logger.info(f"Found {result.total_found} vulnerabilities matching criteria")
        return result.model_dump()
    
    async def generate_suppression(self, args: GenerateSuppressionArgs) -> Dict[str, Any]:
        """
        Generate suppression rules for false positives.
        
        Args:
            args: Suppression generation configuration
            
        Returns:
            Result dictionary with suppression file path
        """
        logger.info(f"Generating suppression rules from report: {args.report_path}")
        
        # Create suppression XML
        root = ET.Element('suppressions', xmlns='https://jeremylong.github.io/DependencyCheck/dependency-suppression.1.3.xsd')
        
        # Add suppression rule
        suppress = ET.SubElement(root, 'suppress')
        
        # Add notes if provided
        if args.notes:
            notes = ET.SubElement(suppress, 'notes')
            notes.text = args.notes
        
        # Add file path if provided
        if args.file_path:
            file_path = ET.SubElement(suppress, 'filePath')
            file_path.text = args.file_path
        
        # Add CPE if provided
        if args.cpe_uri:
            cpe = ET.SubElement(suppress, 'cpe')
            cpe.text = args.cpe_uri
        
        # Add CVE if provided
        if args.cve_id:
            cve = ET.SubElement(suppress, 'cve')
            cve.text = args.cve_id
        
        # If no specific filters provided, create a template
        if not any([args.file_path, args.cpe_uri, args.cve_id]):
            notes = ET.SubElement(suppress, 'notes')
            notes.text = "Template suppression rule - modify as needed"
            file_path = ET.SubElement(suppress, 'filePath', regex='true')
            file_path.text = ".*\\.(jar|dll|exe)$"
            cve = ET.SubElement(suppress, 'cve')
            cve.text = "CVE-YYYY-NNNNN"
        
        # Pretty print the XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent='  ')
        
        # Remove extra blank lines
        lines = pretty_xml_str.split('\n')
        pretty_xml_str = '\n'.join([line for line in lines if line.strip()])
        
        # Save to file
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(pretty_xml_str)
        
        logger.info(f"Suppression file generated: {args.output_file}")
        
        return {
            "success": True,
            "suppression_file": args.output_file,
            "rules_count": 1,
            "message": f"Suppression file created at {args.output_file}"
        }
    
    async def get_scan_summary(self, args: GetScanSummaryArgs) -> Dict[str, Any]:
        """
        Get a summary of vulnerabilities from a scan report.
        
        Args:
            args: Summary configuration
            
        Returns:
            Summary dictionary
        """
        logger.info(f"Getting scan summary from report: {args.report_path}")
        
        # Read the report
        report_path = Path(args.report_path)
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {args.report_path}")
        
        if not report_path.suffix == '.json':
            raise ValueError("Only JSON format reports are supported for summaries")
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Initialize summary structure
        summary = {
            "report_path": args.report_path,
            "scan_date": report_data.get('reportSchema', {}).get('generatedOn', ''),
            "total_dependencies": len(report_data.get('dependencies', [])),
            "vulnerable_dependencies": 0,
            "total_vulnerabilities": 0,
            "group_by": args.group_by,
            "groups": {}
        }
        
        # Process dependencies
        for dependency in report_data.get('dependencies', []):
            vulnerabilities = dependency.get('vulnerabilities', [])
            if vulnerabilities:
                summary['vulnerable_dependencies'] += 1
                summary['total_vulnerabilities'] += len(vulnerabilities)
                
                # Group vulnerabilities
                if args.group_by == 'severity':
                    for vuln in vulnerabilities:
                        severity = vuln.get('severity', 'UNKNOWN')
                        if severity not in summary['groups']:
                            summary['groups'][severity] = {
                                'count': 0,
                                'vulnerabilities': []
                            }
                        summary['groups'][severity]['count'] += 1
                        summary['groups'][severity]['vulnerabilities'].append({
                            'cve': vuln.get('name', ''),
                            'dependency': dependency.get('fileName', ''),
                            'cvss': self._get_cvss_score(vuln)
                        })
                
                elif args.group_by == 'dependency':
                    dep_name = dependency.get('fileName', 'Unknown')
                    if dep_name not in summary['groups']:
                        summary['groups'][dep_name] = {
                            'count': 0,
                            'vulnerabilities': []
                        }
                    summary['groups'][dep_name]['count'] = len(vulnerabilities)
                    for vuln in vulnerabilities:
                        summary['groups'][dep_name]['vulnerabilities'].append({
                            'cve': vuln.get('name', ''),
                            'severity': vuln.get('severity', ''),
                            'cvss': self._get_cvss_score(vuln)
                        })
                
                elif args.group_by == 'cve':
                    for vuln in vulnerabilities:
                        cve_id = vuln.get('name', 'Unknown')
                        if cve_id not in summary['groups']:
                            summary['groups'][cve_id] = {
                                'severity': vuln.get('severity', ''),
                                'cvss': self._get_cvss_score(vuln),
                                'affected_dependencies': []
                            }
                        summary['groups'][cve_id]['affected_dependencies'].append(
                            dependency.get('fileName', '')
                        )
        
        # Add severity breakdown
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for dependency in report_data.get('dependencies', []):
            for vuln in dependency.get('vulnerabilities', []):
                severity = vuln.get('severity', '').upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        summary['severity_breakdown'] = severity_counts
        
        logger.info(f"Summary generated with {summary['total_vulnerabilities']} vulnerabilities")
        return summary
    
    def _get_cvss_score(self, vulnerability: Dict[str, Any]) -> Optional[float]:
        """Extract CVSS score from vulnerability data."""
        if 'cvssv3' in vulnerability:
            return vulnerability['cvssv3'].get('baseScore')
        elif 'cvssv2' in vulnerability:
            return vulnerability['cvssv2'].get('score')
        return None