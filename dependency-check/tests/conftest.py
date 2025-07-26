"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
from pathlib import Path
import json


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_scan_report(temp_workspace):
    """Create a sample scan report for testing."""
    report_data = {
        "reportSchema": {
            "generatedOn": "2024-01-15T10:30:00Z"
        },
        "dependencies": [
            {
                "fileName": "commons-collections-3.2.1.jar",
                "evidenceCollected": {
                    "identifiers": [
                        {
                            "name": "cpe:/a:apache:commons_collections:3.2.1"
                        }
                    ]
                },
                "vulnerabilities": [
                    {
                        "name": "CVE-2015-7501",
                        "severity": "CRITICAL",
                        "description": "Remote code execution vulnerability",
                        "cvssv3": {
                            "baseScore": 9.8
                        }
                    },
                    {
                        "name": "CVE-2015-6420",
                        "severity": "HIGH",
                        "description": "Deserialization vulnerability",
                        "cvssv3": {
                            "baseScore": 7.5
                        }
                    }
                ]
            },
            {
                "fileName": "spring-core-4.3.0.jar",
                "evidenceCollected": {
                    "identifiers": [
                        {
                            "name": "cpe:/a:spring:spring_framework:4.3.0"
                        }
                    ]
                },
                "vulnerabilities": [
                    {
                        "name": "CVE-2018-1271",
                        "severity": "MEDIUM",
                        "description": "Directory traversal vulnerability",
                        "cvssv3": {
                            "baseScore": 5.9
                        }
                    }
                ]
            },
            {
                "fileName": "safe-library-1.0.0.jar",
                "evidenceCollected": {
                    "identifiers": [
                        {
                            "name": "cpe:/a:safe:library:1.0.0"
                        }
                    ]
                },
                "vulnerabilities": []
            }
        ]
    }
    
    report_file = temp_workspace / "test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return report_file


@pytest.fixture
def sample_python_project(temp_workspace):
    """Create a sample Python project structure."""
    project_dir = temp_workspace / "python_project"
    project_dir.mkdir()
    
    # Create Python files
    (project_dir / "requirements.txt").write_text("flask==2.0.1\nrequests==2.26.0\n")
    (project_dir / "setup.py").write_text("from setuptools import setup\nsetup(name='test')")
    (project_dir / "app.py").write_text("import flask\napp = flask.Flask(__name__)")
    
    # Create venv directory to test exclusion
    (project_dir / "venv").mkdir()
    (project_dir / "venv" / "lib").mkdir()
    
    return project_dir


@pytest.fixture
def sample_node_project(temp_workspace):
    """Create a sample Node.js project structure."""
    project_dir = temp_workspace / "node_project"
    project_dir.mkdir()
    
    # Create package.json
    package_data = {
        "name": "test-app",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.17.1",
            "lodash": "^4.17.20"
        }
    }
    
    with open(project_dir / "package.json", 'w') as f:
        json.dump(package_data, f, indent=2)
    
    # Create node_modules directory to test exclusion
    (project_dir / "node_modules").mkdir()
    
    return project_dir


@pytest.fixture
def multi_language_project(temp_workspace):
    """Create a project with multiple languages."""
    project_dir = temp_workspace / "multi_project"
    project_dir.mkdir()
    
    # Python files
    (project_dir / "requirements.txt").write_text("django==3.2.0\n")
    
    # Node.js files
    (project_dir / "package.json").write_text('{"name": "frontend", "version": "1.0.0"}')
    
    # Go files
    (project_dir / "go.mod").write_text("module example.com/app\ngo 1.16\n")
    
    # Java files
    (project_dir / "pom.xml").write_text(
        '<?xml version="1.0"?><project><modelVersion>4.0.0</modelVersion></project>'
    )
    
    return project_dir