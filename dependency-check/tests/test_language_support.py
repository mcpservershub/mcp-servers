"""Tests for language detection and support."""

import pytest
from pathlib import Path
import tempfile
import os

from dependency_check_mcp.language_support import LanguageDetector


class TestLanguageDetector:
    """Test language detection functionality."""
    
    @pytest.fixture
    def detector(self):
        """Create a LanguageDetector instance."""
        return LanguageDetector()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_detect_python_project(self, detector, temp_dir):
        """Test detection of Python projects."""
        # Create Python project files
        Path(temp_dir, "requirements.txt").touch()
        Path(temp_dir, "setup.py").touch()
        
        languages = detector.detect_languages(temp_dir)
        assert "python" in languages
    
    def test_detect_javascript_project(self, detector, temp_dir):
        """Test detection of JavaScript projects."""
        # Create JavaScript project files
        Path(temp_dir, "package.json").touch()
        Path(temp_dir, "yarn.lock").touch()
        
        languages = detector.detect_languages(temp_dir)
        assert "javascript" in languages
    
    def test_detect_multiple_languages(self, detector, temp_dir):
        """Test detection of projects with multiple languages."""
        # Create files for multiple languages
        Path(temp_dir, "package.json").touch()
        Path(temp_dir, "requirements.txt").touch()
        Path(temp_dir, "go.mod").touch()
        
        languages = detector.detect_languages(temp_dir)
        assert "javascript" in languages
        assert "python" in languages
        assert "go" in languages
    
    def test_detect_single_file(self, detector, temp_dir):
        """Test detection when scanning a single file."""
        pom_file = Path(temp_dir, "pom.xml")
        pom_file.touch()
        
        languages = detector.detect_languages(str(pom_file))
        assert "java" in languages
    
    def test_get_additional_args_javascript(self, detector):
        """Test getting additional arguments for JavaScript."""
        args = detector.get_additional_args(["javascript"])
        assert "--enableRetireJS" in args
    
    def test_get_additional_args_dotnet(self, detector):
        """Test getting additional arguments for .NET."""
        args = detector.get_additional_args(["dotnet"])
        assert "--enableAssemblyAnalyzer" in args
    
    def test_get_additional_args_multiple_languages(self, detector):
        """Test getting additional arguments for multiple languages."""
        args = detector.get_additional_args(["javascript", "python", "go"])
        assert "--enableRetireJS" in args
        assert "--enablePython" in args
        assert "--enableGolang" in args
        # Check no duplicates
        assert len(args) == len(set(args))
    
    def test_get_scan_recommendations(self, detector, temp_dir):
        """Test getting scan recommendations."""
        # Create a mixed project
        Path(temp_dir, "package.json").touch()
        Path(temp_dir, "requirements.txt").touch()
        os.makedirs(Path(temp_dir, "node_modules"), exist_ok=True)
        os.makedirs(Path(temp_dir, "venv"), exist_ok=True)
        
        recommendations = detector.get_scan_recommendations(temp_dir)
        
        assert "javascript" in recommendations["detected_languages"]
        assert "python" in recommendations["detected_languages"]
        assert "**/node_modules/**" in recommendations["exclude_patterns"]
        assert "**/venv/**" in recommendations["exclude_patterns"]
        assert "--enableRetireJS" in recommendations["recommended_args"]
        assert "--enablePython" in recommendations["recommended_args"]
    
    def test_match_pattern_exact(self, detector):
        """Test exact pattern matching."""
        assert detector._match_pattern("package.json", "package.json")
        assert not detector._match_pattern("package.json", "pom.xml")
    
    def test_match_pattern_wildcard(self, detector):
        """Test wildcard pattern matching."""
        assert detector._match_pattern("test.jar", "*.jar")
        assert detector._match_pattern("requirements.txt", "requirements*.txt")
        assert not detector._match_pattern("test.jar", "*.war")