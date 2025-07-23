"""Renovate MCP Server implementation using FastMCP."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("renovate-mcp-server")

# Valid platforms supported by Renovate
VALID_PLATFORMS = ["github", "gitlab", "bitbucket", "azure", "gitea", "local"]

# Valid log levels
VALID_LOG_LEVELS = ["debug", "info", "warn", "error"]

# Valid schedule types
VALID_SCHEDULE_TYPES = ["immediate", "hourly", "daily", "custom"]

# Valid dashboard actions
VALID_DASHBOARD_ACTIONS = ["view", "refresh"]


def validate_repository_format(repository: str) -> bool:
    """Validate repository name format (owner/repo)."""
    pattern = r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$'
    return bool(re.match(pattern, repository))


def validate_cron_expression(cron: str) -> bool:
    """Basic validation for cron expression format."""
    # Simple validation - check if it has 5 fields
    parts = cron.strip().split()
    return len(parts) == 5


def check_renovate_installed() -> bool:
    """Check if Renovate CLI is installed."""
    return shutil.which("npx") is not None


def validate_repository_or_path(value: str, platform: str) -> Dict[str, Any]:
    """
    Validate repository format or path based on platform.
    
    Args:
        value: Repository name (owner/repo) or path
        platform: Platform type (github, gitlab, local, etc.)
    
    Returns:
        Dict with validation result and type
    """
    if platform.lower() == "local":
        # For local platform, validate as path
        path = Path(value).resolve()
        if not path.exists():
            return {
                "valid": False,
                "error": f"Path not found: {value}",
                "type": "path"
            }
        if not path.is_dir():
            return {
                "valid": False,
                "error": f"Path is not a directory: {value}",
                "type": "path"
            }
        return {
            "valid": True,
            "type": "path",
            "resolved_path": str(path)
        }
    else:
        # For remote platforms, validate repository format
        if not validate_repository_format(value):
            return {
                "valid": False,
                "error": f"Invalid repository format: {value}. Expected format: owner/repo",
                "type": "repository"
            }
        return {
            "valid": True,
            "type": "repository"
        }


@mcp.tool()
async def run_renovate(
    repositories: List[str],
    platform: str = "github",
    token: Optional[str] = None,
    dry_run: Union[bool, str] = False,
    autodiscover: bool = False,
    config_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute Renovate on specified repositories.
    
    Args:
        repositories: List of repository names (e.g., ["owner/repo"])
        platform: Repository platform (github, gitlab, bitbucket, etc.)
        token: Authentication token (uses RENOVATE_TOKEN env var if not provided)
        dry_run: Run in dry-run mode (boolean or "extract"/"lookup"/"full")
        autodiscover: Automatically discover repositories
        config_file: Path to Renovate config file
    
    Returns:
        Execution result with status and logs
    """
    # Input validation
    if not check_renovate_installed():
        return {
            "status": "error",
            "message": "Renovate CLI is not installed. Please install it with: npm install -g renovate"
        }
    
    if not isinstance(repositories, list):
        return {
            "status": "error",
            "message": "repositories must be a list of repository names"
        }
    
    if platform.lower() not in VALID_PLATFORMS:
        return {
            "status": "error",
            "message": f"Invalid platform '{platform}'. Valid platforms: {', '.join(VALID_PLATFORMS)}"
        }
    
    # Validate repository formats when not using autodiscover
    if not autodiscover and repositories and platform.lower() != "local":
        invalid_repos = [r for r in repositories if not validate_repository_format(r)]
        if invalid_repos:
            return {
                "status": "error",
                "message": f"Invalid repository format: {', '.join(invalid_repos)}. Expected format: owner/repo"
            }
    
    # For local platform, validate paths
    if platform.lower() == "local":
        if len(repositories) != 1:
            return {
                "status": "error",
                "message": "Local platform requires exactly one directory path"
            }
        
        validation = validate_repository_or_path(repositories[0], platform)
        if not validation["valid"]:
            return {
                "status": "error",
                "message": validation["error"]
            }
    
    # Validate config file if provided
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            return {
                "status": "error",
                "message": f"Config file not found: {config_file}"
            }
        if not config_path.is_file():
            return {
                "status": "error",
                "message": f"Config path is not a file: {config_file}"
            }
    
    cmd = ["npx", "renovate"]
    
    # Platform configuration
    cmd.extend(["--platform", platform.lower()])
    
    # Authentication (not required for local platform)
    if platform.lower() != "local":
        if token:
            if not token.strip():
                return {
                    "status": "error",
                    "message": "Token provided but is empty"
                }
            cmd.extend(["--token", token])
        elif not os.environ.get("RENOVATE_TOKEN"):
            return {
                "status": "error",
                "message": "No authentication token provided. Set RENOVATE_TOKEN env var or provide token parameter."
            }
    
    # Dry run mode
    if dry_run:
        if isinstance(dry_run, bool):
            cmd.extend(["--dry-run", "full"])
        elif isinstance(dry_run, str) and dry_run in ["extract", "lookup", "full"]:
            cmd.extend(["--dry-run", dry_run])
        else:
            return {
                "status": "error",
                "message": "Invalid dry_run value. Use boolean or 'extract'/'lookup'/'full'"
            }
    
    try:
        # Handle local platform differently
        if platform.lower() == "local":
            # Local platform doesn't support autodiscover
            if autodiscover:
                return {
                    "status": "error",
                    "message": "Local platform does not support autodiscover mode"
                }
            
            # Get the directory path
            target_dir = validation.get("resolved_path", repositories[0])
            original_cwd = os.getcwd()
            
            # Config file
            if config_file:
                cmd.extend(["--config-file", config_file])
            
            try:
                # Change to target directory for local platform
                os.chdir(target_dir)
                
                # Clean environment to avoid npm config warnings
                clean_env = os.environ.copy()
                clean_env["NODE_ENV"] = "production"
                for key in list(clean_env.keys()):
                    if key.startswith("npm_config_") or key.startswith("NPM_CONFIG_"):
                        clean_env.pop(key, None)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30 minutes timeout
                    env=clean_env
                )
            finally:
                # Always restore directory
                try:
                    os.chdir(original_cwd)
                except Exception:
                    pass
        else:
            # Remote platforms
            # Autodiscover mode
            if autodiscover:
                cmd.append("--autodiscover")
                if repositories:
                    # Use repositories as filter
                    cmd.extend(["--autodiscover-filter", " ".join(repositories)])
            else:
                if not repositories:
                    return {
                        "status": "error",
                        "message": "Either provide repositories list or enable autodiscover"
                    }
                # Manual repository specification
                cmd.extend(repositories)
            
            # Config file
            if config_file:
                cmd.extend(["--config-file", config_file])
            
            # Clean environment to avoid npm config warnings
            clean_env = os.environ.copy()
            clean_env["NODE_ENV"] = "production"
            for key in list(clean_env.keys()):
                if key.startswith("npm_config_") or key.startswith("NPM_CONFIG_"):
                    clean_env.pop(key, None)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
                env=clean_env
            )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "stdout": result.stdout[-50000:] if len(result.stdout) > 50000 else result.stdout,  # Limit output size
            "stderr": result.stderr[-10000:] if len(result.stderr) > 10000 else result.stderr,
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Renovate execution timed out after 30 minutes"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "npx command not found. Please ensure Node.js and npm are installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute Renovate: {str(e)}",
            "error_type": type(e).__name__
        }


@mcp.tool()
async def check_config(
    config_file_path: str,
    repository: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate Renovate configuration file.
    
    Args:
        config_file_path: Path to the configuration file
        repository: Optional repository to validate against
    
    Returns:
        Validation result with any errors or warnings
    """
    # Input validation
    if not config_file_path:
        return {
            "status": "error",
            "message": "config_file_path is required"
        }
    
    config_path = Path(config_file_path)
    if not config_path.exists():
        return {
            "status": "error",
            "message": f"Configuration file not found: {config_file_path}"
        }
    
    if not config_path.is_file():
        return {
            "status": "error",
            "message": f"Path is not a file: {config_file_path}"
        }
    
    # Check file extension
    valid_extensions = ['.json', '.json5', '.yaml', '.yml']
    if config_path.suffix.lower() not in valid_extensions:
        return {
            "status": "warning",
            "message": f"Unusual file extension '{config_path.suffix}'. Expected one of: {', '.join(valid_extensions)}"
        }
    
    # Validate repository format if provided
    if repository and not validate_repository_format(repository):
        return {
            "status": "error",
            "message": f"Invalid repository format: {repository}. Expected format: owner/repo"
        }
    
    # Try to parse the config file to check basic validity
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            if config_path.suffix.lower() in ['.json', '.json5']:
                json.loads(content)  # Basic JSON validation
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON in config file: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read config file: {str(e)}"
        }
    
    cmd = ["npx", "renovate-config-validator", str(config_path)]
    
    if repository:
        cmd.extend(["--repository", repository])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "NODE_ENV": "production"}
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "valid": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
            "file_path": str(config_path.absolute())
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Config validation timed out after 60 seconds"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "renovate-config-validator not found. Install with: npm install -g renovate"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to validate config: {str(e)}",
            "error_type": type(e).__name__
        }


@mcp.tool()
async def get_dependency_updates(
    repository: str,
    branch: str = "main",
    filter: Optional[str] = None,
    platform: str = "github",
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available dependency updates for a repository.
    
    Args:
        repository: Repository name (e.g., "owner/repo") or path for local platform
        branch: Branch to check (default: main) - ignored for local platform
        filter: Filter updates by package manager or pattern
        platform: Repository platform
        token: Authentication token
    
    Returns:
        List of available updates with details
    """
    # Input validation
    if not repository:
        return {
            "status": "error",
            "message": "repository is required"
        }
    
    if platform.lower() not in VALID_PLATFORMS:
        return {
            "status": "error",
            "message": f"Invalid platform '{platform}'. Valid platforms: {', '.join(VALID_PLATFORMS)}"
        }
    
    # Validate repository or path based on platform
    validation = validate_repository_or_path(repository, platform)
    if not validation["valid"]:
        return {
            "status": "error",
            "message": validation["error"]
        }
    
    # Branch validation only for non-local platforms
    if platform.lower() != "local":
        if not branch or not branch.strip():
            return {
                "status": "error",
                "message": "branch cannot be empty"
            }
        
        # Validate branch name (basic check)
        if not re.match(r'^[a-zA-Z0-9/_.-]+$', branch):
            return {
                "status": "error",
                "message": f"Invalid branch name: {branch}"
            }
    
    # Build command based on platform
    if platform.lower() == "local":
        # For local platform, we need to run from the directory
        # Note: Don't add repository as argument for local platform
        cmd = [
            "npx", "renovate",
            "--platform", "local",
            "--dry-run=extract",
            "--onboarding=false"  # Skip onboarding to avoid preset errors
        ]
        
        # Get resolved path from validation
        target_dir = validation.get("resolved_path", repository)
        original_cwd = os.getcwd()
    else:
        # For remote platforms
        cmd = [
            "npx", "renovate",
            "--platform", platform.lower(),
            "--dry-run", "extract",
            "--print-config",
            repository
        ]
        
        if token:
            if not token.strip():
                return {
                    "status": "error",
                    "message": "Token provided but is empty"
                }
            cmd.extend(["--token", token])
        elif not os.environ.get("RENOVATE_TOKEN") and platform.lower() != "local":
            return {
                "status": "error",
                "message": "No authentication token provided. Set RENOVATE_TOKEN env var or provide token parameter."
            }
        
        if branch != "main":
            cmd.extend(["--base-branch", branch])
    
    try:
        # Change directory for local platform
        if platform.lower() == "local":
            os.chdir(target_dir)
        
        # Clean environment to avoid npm config warnings
        clean_env = os.environ.copy()
        clean_env["NODE_ENV"] = "production"
        # Remove npm config that might cause warnings
        for key in list(clean_env.keys()):
            if key.startswith("npm_config_") or key.startswith("NPM_CONFIG_"):
                clean_env.pop(key, None)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
            env=clean_env
        )
        
        # Check if stderr only contains warnings (not actual errors)
        stderr_lines = result.stderr.strip().split('\n') if result.stderr else []
        actual_errors = [line for line in stderr_lines if line and not line.startswith("npm warn")]
        
        if result.returncode != 0 and actual_errors:
            # Real error occurred
            return {
                "status": "error",
                "message": "Failed to extract dependencies",
                "stderr": result.stderr[-10000:] if len(result.stderr) > 10000 else result.stderr,
                "stdout": result.stdout[-10000:] if len(result.stdout) > 10000 else result.stdout,
                "exit_code": result.returncode,
                "command": " ".join(cmd)
            }
        
        # Even if exit code is non-zero, if we have stdout data, try to parse it
        if not result.stdout and result.returncode != 0:
            return {
                "status": "error",
                "message": "No output from Renovate. Check if Renovate CLI is properly installed.",
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "hint": "Try running: npm install -g renovate"
            }
        
        # Parse the output to extract dependency information
        output_lines = result.stdout.split('\n') if result.stdout else []
        stderr_lines_all = result.stderr.split('\n') if result.stderr else []
        
        updates = []
        dependencies_found = []
        package_files_found = []
        errors = []
        
        # Common package file patterns for all languages
        package_file_patterns = [
            "packageFile", "Found", "manager:", "detected",
            # JavaScript/Node.js
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            # Python
            "requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "poetry.lock",
            # Go
            "go.mod", "go.sum",
            # Ruby
            "Gemfile", "Gemfile.lock",
            # PHP
            "composer.json", "composer.lock",
            # Java
            "pom.xml", "build.gradle", "build.gradle.kts",
            # Rust
            "Cargo.toml", "Cargo.lock",
            # .NET
            "*.csproj", "packages.config", "project.json"
        ]
        
        # Parse stdout
        for line in output_lines:
            # Look for package file detections
            if any(pattern in line for pattern in package_file_patterns):
                package_files_found.append(line.strip())
            
            # Look for dependency extractions
            if any(term in line for term in ["deps=", "dependencies", "extracted", "found", "analyzed"]):
                dependencies_found.append(line.strip())
            
            # Look for version patterns that indicate updates
            # This regex matches common version patterns like v1.2.3, 1.2.3, ^1.2.3, ~1.2.3, etc.
            if any(pattern in line for pattern in [
                "->", "→", "update", "upgrade", "available", "latest",
                "current:", "wanted:", "latest:", "from:", "to:"
            ]):
                if not filter or filter.lower() in line.lower():
                    updates.append(line.strip())
            
            # Also catch lines with version numbers (generic pattern)
            elif re.search(r'[v@^~]?\d+\.\d+(?:\.\d+)?', line):
                if any(term in line.lower() for term in ["update", "upgrade", "available", "outdated"]):
                    if not filter or filter.lower() in line.lower():
                        updates.append(line.strip())
        
        # Parse stderr for actual errors (not warnings)
        for line in stderr_lines_all:
            if line.strip() and not line.startswith("npm warn"):
                # Check if it's an actual error
                if any(term in line.lower() for term in ["error:", "fatal:", "failed"]):
                    errors.append(line.strip())
                # Also capture stack traces that indicate real problems
                elif "Error:" in line and "at " in line:
                    errors.append(line.strip())
        
        # If we found package files or dependencies, consider it a success even with warnings
        has_useful_output = package_files_found or dependencies_found or updates
        
        # Check if we have real errors (not just the false positive from parsing)
        real_errors = []
        for error in errors:
            # Filter out the "repositories list not supported" error which is expected for local platform
            if "repositories list not supported when platform=local" not in error:
                real_errors.append(error)
        
        # Filter out updates that are actually error messages
        filtered_updates = []
        for update in updates:
            if not any(term in update for term in ["Error:", "error:", "failed", "stack"]):
                filtered_updates.append(update)
        
        result_data = {
            "status": "success" if (has_useful_output and not real_errors) else ("error" if real_errors else "partial"),
            "repository": repository,
            "platform": platform,
            "updates_count": len(filtered_updates),
            "updates": filtered_updates[:50],  # Limit to first 50 updates
            "message": f"Found {len(filtered_updates)} potential updates",
            "filter_applied": filter if filter else None,
            "package_files_found": len(package_files_found),
            "dependencies_extracted": len(dependencies_found)
        }
        
        # Add branch info only for non-local platforms
        if platform.lower() != "local":
            result_data["branch"] = branch
        else:
            result_data["directory"] = repository
        
        # Add debug info if no updates found
        if not updates and (result.stdout or result.stderr):
            result_data["debug_info"] = {
                "stdout_sample": result.stdout[:1000] if result.stdout else None,
                "stderr_warnings": [line for line in stderr_lines if line.startswith("npm warn")][:5],
                "exit_code": result.returncode
            }
            result_data["hint"] = "No updates found. This might be normal if all dependencies are up to date."
            
        return result_data
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Dependency extraction timed out after 5 minutes"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "npx command not found. Please ensure Node.js and npm are installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get updates: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        # Restore original directory for local platform
        if platform.lower() == "local" and 'original_cwd' in locals():
            try:
                os.chdir(original_cwd)
            except Exception:
                pass


@mcp.tool()
async def create_onboarding_pr(
    repository: str,
    config_template: Optional[str] = None,
    platform: str = "github",
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create initial Renovate configuration PR for a repository.
    
    Args:
        repository: Repository name (e.g., "owner/repo")
        config_template: Optional config template (JSON string)
        platform: Repository platform
        token: Authentication token
    
    Returns:
        Result of onboarding PR creation
    """
    # Input validation
    if not repository:
        return {
            "status": "error",
            "message": "repository is required"
        }
    
    if not validate_repository_format(repository):
        return {
            "status": "error",
            "message": f"Invalid repository format: {repository}. Expected format: owner/repo"
        }
    
    if platform.lower() not in VALID_PLATFORMS:
        return {
            "status": "error",
            "message": f"Invalid platform '{platform}'. Valid platforms: {', '.join(VALID_PLATFORMS)}"
        }
    
    # Create a temporary config if template is provided
    config_file = None
    if config_template:
        if not config_template.strip():
            return {
                "status": "error",
                "message": "config_template provided but is empty"
            }
        try:
            # Validate JSON
            parsed_json = json.loads(config_template)
            # Pretty-print the JSON for better readability
            formatted_json = json.dumps(parsed_json, indent=2)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(formatted_json)
                config_file = f.name
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in config_template: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create temporary config file: {str(e)}"
            }
    
    cmd = [
        "npx", "renovate",
        "--platform", platform.lower(),
        "--onboarding", "true",
        "--onboarding-branch", "renovate/configure",
        repository
    ]
    
    if token:
        if not token.strip():
            return {
                "status": "error",
                "message": "Token provided but is empty"
            }
        cmd.extend(["--token", token])
    elif not os.environ.get("RENOVATE_TOKEN"):
        return {
            "status": "error",
            "message": "No authentication token provided. Set RENOVATE_TOKEN env var or provide token parameter."
        }
    
    if config_file:
        cmd.extend(["--config-file", config_file])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
            env={**os.environ, "NODE_ENV": "production"}
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "stdout": result.stdout[-50000:] if len(result.stdout) > 50000 else result.stdout,
            "stderr": result.stderr[-10000:] if len(result.stderr) > 10000 else result.stderr,
            "message": "Onboarding PR created successfully" if result.returncode == 0 else "Failed to create onboarding PR",
            "onboarding_branch": "renovate/configure"
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Onboarding PR creation timed out after 10 minutes"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "npx command not found. Please ensure Node.js and npm are installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create onboarding PR: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        if config_file and os.path.exists(config_file):
            try:
                os.unlink(config_file)
            except Exception:
                pass  # Ignore cleanup errors


@mcp.tool()
async def get_renovate_logs(
    repository: str,
    log_level: str = "info",
    date_range: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve Renovate execution logs for a repository.
    
    Args:
        repository: Repository name (e.g., "owner/repo")
        log_level: Log level (debug, info, warn, error)
        date_range: Optional date range (e.g., "last-24h", "2024-01-01")
    
    Returns:
        Filtered logs from recent Renovate runs
    """
    # Input validation
    if not repository:
        return {
            "status": "error",
            "message": "repository is required"
        }
    
    if not validate_repository_format(repository):
        return {
            "status": "error",
            "message": f"Invalid repository format: {repository}. Expected format: owner/repo"
        }
    
    if log_level.lower() not in VALID_LOG_LEVELS:
        return {
            "status": "error",
            "message": f"Invalid log level '{log_level}'. Valid levels: {', '.join(VALID_LOG_LEVELS)}"
        }
    
    # Sanitize repository name for file path
    safe_repo_name = re.sub(r'[^a-zA-Z0-9_.-]', '-', repository)
    log_file = Path(f"/tmp/renovate-{safe_repo_name}.log")
    
    if not log_file.exists():
        return {
            "status": "info",
            "message": "No logs found for this repository. Run Renovate first to generate logs.",
            "repository": repository,
            "log_file": str(log_file)
        }
    
    try:
        # Check file size to prevent reading huge files
        file_size = log_file.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return {
                "status": "error",
                "message": f"Log file too large ({file_size / 1024 / 1024:.2f}MB). Maximum size: 10MB"
            }
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()
        
        # Simple filtering by log level
        filtered_logs = []
        log_levels = ["debug", "info", "warn", "error"]
        try:
            min_level_index = log_levels.index(log_level.lower())
        except ValueError:
            min_level_index = 1  # Default to info
        
        for line in logs.split('\n'):
            for i, level in enumerate(log_levels):
                if level.upper() in line and i >= min_level_index:
                    filtered_logs.append(line)
                    break
        
        # Apply date range filter if provided
        if date_range:
            # This is a simplified implementation
            # In production, you'd parse dates and filter properly
            filtered_logs = [line for line in filtered_logs if date_range in line]
        
        return {
            "status": "success",
            "repository": repository,
            "log_level": log_level,
            "date_range": date_range,
            "total_lines": len(logs.split('\n')),
            "filtered_lines": len(filtered_logs),
            "logs": '\n'.join(filtered_logs[-100:])  # Last 100 filtered lines
        }
    except PermissionError:
        return {
            "status": "error",
            "message": f"Permission denied when reading log file: {log_file}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve logs: {str(e)}",
            "error_type": type(e).__name__
        }


@mcp.tool()
async def manage_dashboard(
    repository: str,
    action: str = "view",
    platform: str = "github",
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    View or manage the Renovate dependency dashboard.
    
    Args:
        repository: Repository name (e.g., "owner/repo")
        action: Action to perform (view, refresh)
        platform: Repository platform
        token: Authentication token
    
    Returns:
        Dashboard information or action result
    """
    # Input validation
    if not repository:
        return {
            "status": "error",
            "message": "repository is required"
        }
    
    if not validate_repository_format(repository):
        return {
            "status": "error",
            "message": f"Invalid repository format: {repository}. Expected format: owner/repo"
        }
    
    if action.lower() not in VALID_DASHBOARD_ACTIONS:
        return {
            "status": "error",
            "message": f"Invalid action '{action}'. Valid actions: {', '.join(VALID_DASHBOARD_ACTIONS)}"
        }
    
    if platform.lower() not in VALID_PLATFORMS:
        return {
            "status": "error",
            "message": f"Invalid platform '{platform}'. Valid platforms: {', '.join(VALID_PLATFORMS)}"
        }
    
    if action.lower() == "view":
        # Generate dashboard URL based on platform
        dashboard_urls = {
            "github": f"https://github.com/{repository}/issues?q=is:issue+is:open+author:app/renovate",
            "gitlab": f"https://gitlab.com/{repository}/-/issues?label_name[]=renovate",
            "bitbucket": f"https://bitbucket.org/{repository}/issues?status=new&status=open&reporter=renovate",
            "azure": f"https://dev.azure.com/{repository}/_workitems",
            "gitea": f"https://gitea.com/{repository}/issues?type=all&state=open&labels=renovate"
        }
        
        dashboard_url = dashboard_urls.get(platform.lower(), f"https://{platform}.com/{repository}/issues")
        
        return {
            "status": "success",
            "repository": repository,
            "platform": platform,
            "dashboard_url": dashboard_url,
            "message": "Check the repository issues/work items for the Renovate Dashboard",
            "note": "The dashboard issue contains a summary of all pending updates"
        }
    
    elif action.lower() == "refresh":
        # Trigger a refresh by running Renovate
        return await run_renovate(
            repositories=[repository],
            platform=platform,
            token=token,
            dry_run=False
        )
    
    else:
        # This should not happen due to validation above, but kept for safety
        return {
            "status": "error",
            "message": f"Invalid action: {action}. Use 'view' or 'refresh'"
        }


@mcp.tool()
async def schedule_run(
    repository: str,
    schedule_type: str = "immediate",
    cron_expression: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule or trigger Renovate runs.
    
    Args:
        repository: Repository name (e.g., "owner/repo")
        schedule_type: Type of schedule (immediate, hourly, daily, custom)
        cron_expression: Cron expression for custom schedules
    
    Returns:
        Scheduling result
    """
    # Input validation
    if not repository:
        return {
            "status": "error",
            "message": "repository is required"
        }
    
    if not validate_repository_format(repository):
        return {
            "status": "error",
            "message": f"Invalid repository format: {repository}. Expected format: owner/repo"
        }
    
    if schedule_type.lower() not in VALID_SCHEDULE_TYPES:
        return {
            "status": "error",
            "message": f"Invalid schedule type '{schedule_type}'. Valid types: {', '.join(VALID_SCHEDULE_TYPES)}"
        }
    
    schedule_type = schedule_type.lower()
    
    if schedule_type == "immediate":
        # Trigger immediate run
        return {
            "status": "info",
            "message": f"To run immediately, use the 'run_renovate' tool with repository '{repository}'",
            "repository": repository,
            "schedule_type": schedule_type
        }
    
    elif schedule_type in ["hourly", "daily"]:
        cron_map = {
            "hourly": "0 * * * *",
            "daily": "0 2 * * *"  # 2 AM daily
        }
        cron = cron_map[schedule_type]
        
        return {
            "status": "success",
            "message": f"Schedule configuration for {schedule_type} runs",
            "repository": repository,
            "schedule_type": schedule_type,
            "cron": cron,
            "example_config": {
                "schedule": [cron],
                "timezone": "UTC"
            },
            "note": "Add this configuration to your renovate.json file",
            "example_file_content": json.dumps({
                "extends": ["config:base"],
                "schedule": [cron],
                "timezone": "UTC"
            }, indent=2)
        }
    
    elif schedule_type == "custom":
        if not cron_expression:
            return {
                "status": "error",
                "message": "cron_expression is required for custom schedule type"
            }
        
        if not validate_cron_expression(cron_expression):
            return {
                "status": "error",
                "message": f"Invalid cron expression: '{cron_expression}'. Expected format: '* * * * *' (5 fields)"
            }
        
        return {
            "status": "success",
            "message": "Custom schedule configuration",
            "repository": repository,
            "schedule_type": schedule_type,
            "cron": cron_expression,
            "example_config": {
                "schedule": [cron_expression],
                "timezone": "UTC"
            },
            "note": "Add this configuration to your renovate.json file",
            "example_file_content": json.dumps({
                "extends": ["config:base"],
                "schedule": [cron_expression],
                "timezone": "UTC"
            }, indent=2)
        }
    
    else:
        # This should not happen due to validation above
        return {
            "status": "error",
            "message": "Invalid schedule type"
        }


@mcp.tool()
async def validate_credentials(
    platform: str = "github",
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test authentication and permissions for Renovate.
    
    Args:
        platform: Repository platform to test
        token: Authentication token to validate
    
    Returns:
        Validation result with permission details
    """
    # Input validation
    if platform.lower() not in VALID_PLATFORMS:
        return {
            "status": "error",
            "message": f"Invalid platform '{platform}'. Valid platforms: {', '.join(VALID_PLATFORMS)}"
        }
    
    # Check if Renovate is installed
    if not check_renovate_installed():
        return {
            "status": "error",
            "message": "Renovate CLI is not installed. Please install it with: npm install -g renovate"
        }
    
    cmd = [
        "npx", "renovate",
        "--platform", platform.lower(),
        "--dry-run", "extract",
        "--log-level", "debug"  # More detailed output for validation
    ]
    
    # Add a test repository based on platform
    test_repos = {
        "github": "renovatebot/renovate",
        "gitlab": "gitlab-org/gitlab",
        "bitbucket": "atlassian/aui",
        "azure": "Microsoft/vscode",
        "gitea": "gitea/gitea"
    }
    
    test_repo = test_repos.get(platform.lower(), "test/repo")
    cmd.append(test_repo)
    
    if token:
        if not token.strip():
            return {
                "status": "error",
                "message": "Token provided but is empty"
            }
        # Mask token in response for security
        masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:] if len(token) > 8 else "***"
        cmd.extend(["--token", token])
    elif not os.environ.get("RENOVATE_TOKEN"):
        return {
            "status": "error",
            "message": "No authentication token provided. Set RENOVATE_TOKEN env var or provide token parameter."
        }
    else:
        masked_token = "ENV_VAR"
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "NODE_ENV": "production"}
        )
        
        # Check for authentication success patterns in output
        auth_patterns = [
            "authentication successful",
            "authenticated",
            "platform access verified",
            "repository found"
        ]
        
        output_lower = result.stdout.lower() + result.stderr.lower()
        auth_success = any(pattern in output_lower for pattern in auth_patterns) or result.returncode == 0
        
        # Check for specific error patterns
        error_patterns = {
            "401": "Authentication failed - invalid token",
            "403": "Access forbidden - insufficient permissions",
            "404": "Platform or repository not found",
            "rate limit": "Rate limit exceeded"
        }
        
        error_message = None
        for pattern, message in error_patterns.items():
            if pattern in output_lower:
                error_message = message
                break
        
        return {
            "status": "success" if auth_success else "error",
            "authenticated": auth_success,
            "platform": platform,
            "token_used": masked_token,
            "test_repository": test_repo,
            "message": "Credentials validated successfully" if auth_success else (error_message or "Authentication failed"),
            "exit_code": result.returncode,
            "hint": "Check debug output for more details" if not auth_success else None
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Credential validation timed out after 60 seconds"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "npx command not found. Please ensure Node.js and npm are installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to validate credentials: {str(e)}",
            "error_type": type(e).__name__
        }


@mcp.tool()
async def run_renovate_local(
    directory: str = ".",
    config_file: Optional[str] = None,
    dry_run_mode: str = "lookup",
    log_level: str = "info"
) -> Dict[str, Any]:
    """
    Run Renovate against local filesystem for testing configurations.
    
    Args:
        directory: Local directory path to analyze (default: current directory)
        config_file: Path to Renovate config file (renovate.json)
        dry_run_mode: Dry run mode - "extract" or "lookup" (default: lookup)
        log_level: Log level (debug, info, warn, error)
    
    Returns:
        Execution result with analysis details
    """
    # Input validation
    if not check_renovate_installed():
        return {
            "status": "error",
            "message": "Renovate CLI is not installed. Please install it with: npm install -g renovate"
        }
    
    # Validate directory
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return {
            "status": "error",
            "message": f"Directory not found: {directory}"
        }
    
    if not dir_path.is_dir():
        return {
            "status": "error",
            "message": f"Path is not a directory: {directory}"
        }
    
    # Check if directory is accessible
    if not os.access(dir_path, os.R_OK):
        return {
            "status": "error",
            "message": f"Directory is not readable: {directory}"
        }
    
    # Validate dry run mode
    valid_dry_run_modes = ["extract", "lookup"]
    if dry_run_mode not in valid_dry_run_modes:
        return {
            "status": "error",
            "message": f"Invalid dry_run_mode '{dry_run_mode}'. Valid modes: {', '.join(valid_dry_run_modes)}"
        }
    
    # Validate log level
    if log_level.lower() not in VALID_LOG_LEVELS:
        return {
            "status": "error",
            "message": f"Invalid log level '{log_level}'. Valid levels: {', '.join(VALID_LOG_LEVELS)}"
        }
    
    # Validate config file if provided
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            return {
                "status": "error",
                "message": f"Config file not found: {config_file}"
            }
        if not config_path.is_file():
            return {
                "status": "error",
                "message": f"Config path is not a file: {config_file}"
            }
    
    # Build command
    cmd = [
        "npx", "renovate",
        "--platform", "local",
        f"--dry-run={dry_run_mode}",
        "--onboarding=false"
    ]
    
    # Add config file if provided
    if config_file:
        cmd.extend(["--config-file", str(Path(config_file).resolve())])
    
    # Save current directory and change to target directory
    original_cwd = os.getcwd()
    
    try:
        # Change to target directory (required for local platform)
        os.chdir(dir_path)
        
        # Check for package files
        package_files = []
        check_files = [
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            "Gemfile", "Gemfile.lock", "requirements.txt", "requirements.pip",
            "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock",
            "go.mod", "go.sum", "composer.json", "composer.lock",
            "pom.xml", "build.gradle", "build.gradle.kts", "Cargo.toml", "Cargo.lock"
        ]
        
        for file in check_files:
            if Path(file).exists():
                package_files.append(file)
        
        if not package_files and not config_file:
            return {
                "status": "warning",
                "message": "No package files found in directory. Renovate may not find any dependencies.",
                "directory": str(dir_path),
                "hint": "Ensure the directory contains package files like package.json, requirements.txt, etc."
            }
        
        # Run Renovate
        # Set up environment with LOG_LEVEL
        clean_env = os.environ.copy()
        clean_env["NODE_ENV"] = "production"
        clean_env["LOG_LEVEL"] = log_level.lower()
        # Remove npm config that might cause warnings
        for key in list(clean_env.keys()):
            if key.startswith("npm_config_") or key.startswith("NPM_CONFIG_"):
                clean_env.pop(key, None)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            env=clean_env
        )
        
        # Parse output for useful information
        output_lines = result.stdout.split('\n')
        dependencies_found = []
        updates_available = []
        
        for line in output_lines:
            if "packageFile" in line or "manager" in line:
                dependencies_found.append(line.strip())
            if "update" in line.lower() and ("available" in line.lower() or "found" in line.lower()):
                updates_available.append(line.strip())
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "directory": str(dir_path),
            "package_files": package_files,
            "dry_run_mode": dry_run_mode,
            "dependencies_found": len(dependencies_found),
            "updates_available": len(updates_available),
            "stdout": result.stdout[-50000:] if len(result.stdout) > 50000 else result.stdout,
            "stderr": result.stderr[-10000:] if len(result.stderr) > 10000 else result.stderr,
            "command": " ".join(cmd),
            "note": "Local platform runs in dry-run mode only and cannot create branches or PRs"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Renovate execution timed out after 10 minutes",
            "directory": str(dir_path)
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "npx command not found. Please ensure Node.js and npm are installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to run Renovate on local directory: {str(e)}",
            "error_type": type(e).__name__,
            "directory": str(dir_path)
        }
    finally:
        # Always restore original directory
        try:
            os.chdir(original_cwd)
        except Exception:
            pass


def main():
    """Main entry point for the MCP server."""
    import sys
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
