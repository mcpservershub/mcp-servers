#!/usr/bin/env python3
"""Example client demonstrating Dependency Check MCP Server usage."""

import asyncio
import json
import os
from pathlib import Path


async def example_usage():
    """Demonstrate various MCP tools usage."""
    
    # Note: This is a conceptual example. In real usage, you would use
    # an actual MCP client library to connect to the server.
    
    print("=== Dependency Check MCP Server Example ===\n")
    
    # Example 1: Update vulnerability database
    print("1. Updating vulnerability database...")
    update_request = {
        "tool": "update_database",
        "arguments": {
            "nvd_api_key": os.getenv("NVD_API_KEY"),
            "data_directory": "/data/dependency-check"
        }
    }
    print(f"Request: {json.dumps(update_request, indent=2)}")
    print("Response: Database updated successfully\n")
    
    # Example 2: Scan a Python project
    print("2. Scanning Python project...")
    scan_request = {
        "tool": "scan_project",
        "arguments": {
            "path": "/workspace/python-app",
            "output_file": "/output/python-app-scan.json",
            "output_format": "JSON",
            "exclude_patterns": ["**/venv/**", "**/__pycache__/**"],
            "fail_on_cvss": 7.0,
            "enable_experimental": False
        }
    }
    print(f"Request: {json.dumps(scan_request, indent=2)}")
    print("Response: Scan completed. Found 3 vulnerable dependencies with 8 total vulnerabilities\n")
    
    # Example 3: Check for specific vulnerabilities
    print("3. Checking for critical vulnerabilities...")
    check_request = {
        "tool": "check_vulnerabilities",
        "arguments": {
            "report_path": "/output/python-app-scan.json",
            "severity_levels": ["CRITICAL", "HIGH"],
            "min_cvss_score": 8.0
        }
    }
    print(f"Request: {json.dumps(check_request, indent=2)}")
    print("Response: Found 2 critical vulnerabilities matching criteria\n")
    
    # Example 4: Generate suppression file
    print("4. Generating suppression file for false positives...")
    suppression_request = {
        "tool": "generate_suppression",
        "arguments": {
            "report_path": "/output/python-app-scan.json",
            "output_file": "/suppressions/python-app-suppressions.xml",
            "cve_id": "CVE-2021-12345",
            "notes": "False positive - this CVE doesn't apply to our usage pattern"
        }
    }
    print(f"Request: {json.dumps(suppression_request, indent=2)}")
    print("Response: Suppression file created successfully\n")
    
    # Example 5: Get scan summary
    print("5. Getting scan summary...")
    summary_request = {
        "tool": "get_scan_summary",
        "arguments": {
            "report_path": "/output/python-app-scan.json",
            "group_by": "severity"
        }
    }
    print(f"Request: {json.dumps(summary_request, indent=2)}")
    print("Response: Summary by severity - CRITICAL: 2, HIGH: 3, MEDIUM: 2, LOW: 1\n")
    
    # Example 6: Scan multiple project types
    print("6. Scanning multi-language project...")
    multi_scan_request = {
        "tool": "scan_project",
        "arguments": {
            "path": "/workspace/fullstack-app",
            "output_file": "/output/fullstack-scan.html",
            "output_format": "HTML",
            "exclude_patterns": [
                "**/node_modules/**",
                "**/venv/**",
                "**/vendor/**",
                "**/target/**"
            ]
        }
    }
    print(f"Request: {json.dumps(multi_scan_request, indent=2)}")
    print("Response: Detected languages: Python, JavaScript, Java. Scan completed.\n")


def create_sample_projects():
    """Create sample project structures for demonstration."""
    
    # Create directories
    workspace = Path("./example_workspace")
    workspace.mkdir(exist_ok=True)
    
    # Python project
    python_proj = workspace / "python-app"
    python_proj.mkdir(exist_ok=True)
    (python_proj / "requirements.txt").write_text("""
flask==2.0.1
requests==2.26.0
django==3.1.0
sqlalchemy==1.3.20
""")
    (python_proj / "app.py").write_text("# Sample Python app")
    
    # Node.js project
    node_proj = workspace / "node-app"
    node_proj.mkdir(exist_ok=True)
    (node_proj / "package.json").write_text(json.dumps({
        "name": "sample-app",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.17.1",
            "lodash": "^4.17.20",
            "axios": "^0.21.1"
        }
    }, indent=2))
    
    # Multi-language project
    multi_proj = workspace / "fullstack-app"
    multi_proj.mkdir(exist_ok=True)
    (multi_proj / "requirements.txt").write_text("django==3.2.0")
    (multi_proj / "package.json").write_text('{"name": "frontend", "version": "1.0.0"}')
    (multi_proj / "pom.xml").write_text("""<?xml version="1.0"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>backend</artifactId>
    <version>1.0.0</version>
</project>
""")
    
    print(f"Created sample projects in: {workspace.absolute()}")


if __name__ == "__main__":
    print("Creating sample project structures...")
    create_sample_projects()
    print("\nRunning example MCP tool calls...\n")
    asyncio.run(example_usage())
    print("\n=== Example completed ===")