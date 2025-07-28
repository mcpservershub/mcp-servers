"""Language detection and support for various project types."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect and prepare projects for dependency scanning."""
    
    LANGUAGE_PATTERNS = {
        'python': [
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            'Pipfile',
            'Pipfile.lock',
            'poetry.lock',
            'requirements*.txt',
            'requirements/*.txt'
        ],
        'javascript': [
            'package.json',
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml',
            'bower.json'
        ],
        'java': [
            'pom.xml',
            'build.gradle',
            'build.gradle.kts',
            'settings.gradle',
            '*.jar',
            '*.war',
            '*.ear'
        ],
        'dotnet': [
            '*.csproj',
            '*.vbproj',
            '*.fsproj',
            'packages.config',
            'project.json',
            '*.dll',
            '*.exe',
            'global.json',
            '*.sln'
        ],
        'ruby': [
            'Gemfile',
            'Gemfile.lock',
            '*.gemspec'
        ],
        'go': [
            'go.mod',
            'go.sum',
            'Gopkg.toml',
            'Gopkg.lock',
            'glide.yaml',
            'glide.lock'
        ],
        'php': [
            'composer.json',
            'composer.lock'
        ],
        'rust': [
            'Cargo.toml',
            'Cargo.lock'
        ],
        'cpp': [
            'conanfile.txt',
            'conanfile.py',
            'CMakeLists.txt',
            'vcpkg.json'
        ],
        'swift': [
            'Package.swift',
            'Package.resolved',
            'Podfile',
            'Podfile.lock'
        ],
        'kotlin': [
            'build.gradle.kts',
            '*.kt'
        ],
        'scala': [
            'build.sbt',
            'project/build.properties'
        ],
        'elixir': [
            'mix.exs',
            'mix.lock'
        ],
        'clojure': [
            'project.clj',
            'deps.edn'
        ],
        'perl': [
            'cpanfile',
            'META.json',
            'META.yml'
        ],
        'r': [
            'renv.lock',
            'DESCRIPTION'
        ],
        'dart': [
            'pubspec.yaml',
            'pubspec.lock'
        ],
        'lua': [
            'rockspec',
            '*.rockspec'
        ],
        'haskell': [
            'stack.yaml',
            'package.yaml',
            '*.cabal'
        ]
    }
    
    # Languages with specific analyzer support in Dependency Check
    SUPPORTED_ANALYZERS = {
        'javascript': ['RetireJS', 'NodePackage', 'NodeAudit'],
        'python': ['Python'],
        'ruby': ['Ruby', 'BundleAudit'],
        'java': ['Jar', 'Maven', 'Gradle'],
        'dotnet': ['Assembly', 'Nuspec', 'Nuget'],
        'go': ['Golang'],
        'php': ['Composer'],
        'swift': ['Swift', 'CocoaPods'],
        'elixir': ['Mix'],
        'rust': ['Cargo']
    }
    
    # Additional CLI arguments for specific languages
    # Based on Dependency Check 12.1.3 available flags
    LANGUAGE_ARGS = {
        'javascript': ['--enableRetired'],  # RetireJS analyzer
        'dotnet': [],  # Assembly analyzer is enabled by default
        'ruby': [],  # Bundle audit might be in experimental
        'python': [],  # Python might be in experimental
        'go': [],  # Go analyzer might be in experimental or core
        'swift': [],  # Swift might be in experimental
        'experimental': ['--enableExperimental']
    }
    
    def detect_languages(self, project_path: str) -> List[str]:
        """
        Detect programming languages in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected languages
        """
        detected_languages = []
        path = Path(project_path)
        
        if path.is_file():
            # Single file scan
            file_name = path.name
            for lang, patterns in self.LANGUAGE_PATTERNS.items():
                for pattern in patterns:
                    if self._match_pattern(file_name, pattern):
                        detected_languages.append(lang)
                        break
        else:
            # Directory scan
            for lang, patterns in self.LANGUAGE_PATTERNS.items():
                for pattern in patterns:
                    if self._find_files(path, pattern):
                        detected_languages.append(lang)
                        break
        
        logger.info(f"Detected languages in {project_path}: {detected_languages}")
        return list(set(detected_languages))  # Remove duplicates
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern."""
        if '*' in pattern:
            # Convert simple glob pattern to regex-like matching
            import fnmatch
            return fnmatch.fnmatch(filename, pattern)
        else:
            return filename == pattern
    
    def _find_files(self, directory: Path, pattern: str) -> List[Path]:
        """Find files matching pattern in directory."""
        try:
            if '/' in pattern:
                # Handle patterns with directory separators
                parts = pattern.split('/')
                if parts[0] == '*' or parts[0] == '**':
                    # Recursive search
                    return list(directory.rglob(parts[-1]))
                else:
                    # Specific path
                    return list(directory.glob(pattern))
            else:
                # Simple pattern
                return list(directory.glob(pattern))
        except Exception as e:
            logger.warning(f"Error searching for {pattern}: {str(e)}")
            return []
    
    def get_additional_args(self, languages: List[str], enable_experimental: bool = False) -> List[str]:
        """
        Get additional CLI arguments for detected languages.
        
        Args:
            languages: List of detected languages
            enable_experimental: Whether to enable experimental analyzers
            
        Returns:
            List of additional CLI arguments
        """
        args = []
        
        # Add language-specific arguments
        for lang in languages:
            if lang in self.LANGUAGE_ARGS:
                args.extend(self.LANGUAGE_ARGS[lang])
        
        # Add experimental if needed and not already included
        if enable_experimental and '--enableExperimental' not in args:
            args.append('--enableExperimental')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_args = []
        for arg in args:
            if arg not in seen:
                seen.add(arg)
                unique_args.append(arg)
        
        logger.info(f"Additional arguments for languages {languages}: {unique_args}")
        return unique_args
    
    def get_scan_recommendations(self, project_path: str) -> Dict[str, Any]:
        """
        Get scanning recommendations for a project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dictionary with recommendations
        """
        languages = self.detect_languages(project_path)
        
        recommendations = {
            'detected_languages': languages,
            'supported_languages': [lang for lang in languages if lang in self.SUPPORTED_ANALYZERS],
            'experimental_languages': [lang for lang in languages if lang not in self.SUPPORTED_ANALYZERS],
            'recommended_args': self.get_additional_args(languages),
            'exclude_patterns': []
        }
        
        # Add common exclude patterns
        common_excludes = {
            'python': ['**/venv/**', '**/__pycache__/**', '**/site-packages/**'],
            'javascript': ['**/node_modules/**', '**/bower_components/**'],
            'java': ['**/target/**', '**/build/**'],
            'dotnet': ['**/bin/**', '**/obj/**'],
            'go': ['**/vendor/**'],
            'ruby': ['**/vendor/**'],
            'rust': ['**/target/**']
        }
        
        for lang in languages:
            if lang in common_excludes:
                recommendations['exclude_patterns'].extend(common_excludes[lang])
        
        # Remove duplicate excludes
        recommendations['exclude_patterns'] = list(set(recommendations['exclude_patterns']))
        
        return recommendations