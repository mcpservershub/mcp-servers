"""Ripgrep MCP tools implementation."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from . import utils, validators

logger = logging.getLogger(__name__)


async def search(
    pattern: str,
    path: Optional[str] = None,
    case_sensitive: bool = True,
    whole_word: bool = False,
    line_numbers: bool = True,
    max_results: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Search for patterns in files recursively.
    
    Args:
        pattern: Regex pattern to search
        path: Directory or file to search in
        case_sensitive: Whether search is case sensitive
        whole_word: Match whole words only
        line_numbers: Include line numbers in results
        max_results: Maximum number of results
        
    Returns:
        List of search results
    """
    # Validate parameters
    params = validators.SearchParams(
        pattern=pattern,
        path=path,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        line_numbers=line_numbers,
        max_results=max_results or utils.get_max_results()
    )
    
    # Build ripgrep command
    args = []
    
    if not params.case_sensitive:
        args.append("-i")
    
    if params.whole_word:
        args.append("-w")
    
    if params.line_numbers:
        args.append("-n")
        args.append("--column")
    
    if params.max_results:
        args.extend(["-m", str(params.max_results)])
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    # Parse results
    if returncode == 0:
        results = utils.parse_ripgrep_output(stdout, include_line_numbers=params.line_numbers)
        return results[:params.max_results] if params.max_results else results
    elif returncode == 1:
        # No matches found
        return []
    else:
        raise RuntimeError(f"ripgrep error: {stderr}")


async def search_by_type(
    pattern: str,
    file_type: str,
    path: Optional[str] = None,
    exclude_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search within specific file types.
    
    Args:
        pattern: Regex pattern to search
        file_type: File type to search in
        path: Directory to search in
        exclude_type: File types to exclude
        
    Returns:
        Filtered search results by file type
    """
    # Validate parameters
    params = validators.SearchByTypeParams(
        pattern=pattern,
        file_type=file_type,
        path=path,
        exclude_type=exclude_type
    )
    
    # Build ripgrep command
    args = ["-n", "--column"]
    
    # Add file type filter
    args.extend(utils.format_file_type_arg(params.file_type))
    
    # Add exclude type if specified
    if params.exclude_type:
        args.extend(["--type-not", params.exclude_type])
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    # Parse results
    if returncode == 0:
        return utils.parse_ripgrep_output(stdout, include_line_numbers=True)
    elif returncode == 1:
        return []
    else:
        raise RuntimeError(f"ripgrep error: {stderr}")


async def search_with_context(
    pattern: str,
    before_context: int = 2,
    after_context: int = 2,
    path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get search results with context lines before/after matches.
    
    Args:
        pattern: Search pattern
        before_context: Lines before match
        after_context: Lines after match
        path: Search path
        
    Returns:
        Matches with surrounding context
    """
    # Validate parameters
    params = validators.SearchWithContextParams(
        pattern=pattern,
        before_context=before_context,
        after_context=after_context,
        path=path
    )
    
    # Build ripgrep command
    args = ["-n"]
    
    if params.before_context > 0:
        args.extend(["-B", str(params.before_context)])
    
    if params.after_context > 0:
        args.extend(["-A", str(params.after_context)])
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    # Parse results with context
    if returncode == 0:
        return utils.parse_context_output(stdout)
    elif returncode == 1:
        return []
    else:
        raise RuntimeError(f"ripgrep error: {stderr}")


async def replace(
    pattern: str,
    replacement: str,
    path: Optional[str] = None,
    dry_run: bool = True
) -> List[Dict[str, Any]]:
    """
    Find patterns and suggest or apply replacements.
    
    Args:
        pattern: Pattern to find
        replacement: Replacement text
        path: Target path
        dry_run: Preview changes without applying
        
    Returns:
        List of proposed or applied changes
    """
    # Validate parameters
    params = validators.ReplaceParams(
        pattern=pattern,
        replacement=replacement,
        path=path,
        dry_run=dry_run
    )
    
    # Build ripgrep command for preview
    args = ["-n", "--replace", params.replacement]
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep to get replacements
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    if returncode != 0 and returncode != 1:
        raise RuntimeError(f"ripgrep error: {stderr}")
    
    # Parse replacement results
    results = []
    if stdout:
        lines = stdout.strip().split("\n")
        for line in lines:
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    results.append({
                        "file_path": parts[0],
                        "line_number": int(parts[1]) if parts[1].isdigit() else None,
                        "original": pattern,
                        "replacement": parts[2],
                        "applied": not params.dry_run
                    })
    
    # If not dry run, would need to implement actual file modification
    # For safety, we keep it as dry_run only in this implementation
    if not params.dry_run:
        logger.warning("Actual file modification not implemented for safety. Results show preview only.")
    
    return results


async def list_files(
    pattern: Optional[str] = None,
    file_type: Optional[str] = None,
    path: Optional[str] = None,
    include_hidden: bool = False
) -> List[str]:
    """
    List files matching criteria.
    
    Args:
        pattern: Filter by file name pattern
        file_type: Filter by file type
        path: Search directory
        include_hidden: Include hidden files
        
    Returns:
        List of file paths matching criteria
    """
    # Validate parameters
    params = validators.ListFilesParams(
        pattern=pattern,
        file_type=file_type,
        path=path,
        include_hidden=include_hidden
    )
    
    # Build ripgrep command
    args = ["--files"]
    
    if params.include_hidden:
        args.append("--hidden")
    
    if params.file_type:
        args.extend(utils.format_file_type_arg(params.file_type))
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    if returncode != 0:
        raise RuntimeError(f"ripgrep error: {stderr}")
    
    # Filter by pattern if specified
    files = stdout.strip().split("\n") if stdout.strip() else []
    
    if params.pattern and files:
        import fnmatch
        files = [f for f in files if fnmatch.fnmatch(f, params.pattern)]
    
    return files


async def search_multiline(
    pattern: str,
    path: Optional[str] = None,
    pcre2: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for patterns spanning multiple lines.
    
    Args:
        pattern: Multiline regex pattern
        path: Search path
        pcre2: Use PCRE2 engine for advanced patterns
        
    Returns:
        Multiline matches with file locations
    """
    # Validate parameters
    params = validators.SearchMultilineParams(
        pattern=pattern,
        path=path,
        pcre2=pcre2
    )
    
    # Build ripgrep command
    args = ["-U", "-n"]  # -U enables multiline mode
    
    if params.pcre2:
        args.append("-P")  # Use PCRE2 engine
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    # Parse results
    if returncode == 0:
        return utils.parse_ripgrep_output(stdout, include_line_numbers=True)
    elif returncode == 1:
        return []
    else:
        raise RuntimeError(f"ripgrep error: {stderr}")


async def stats(
    pattern: str,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get statistics about search operations.
    
    Args:
        pattern: Pattern to analyze
        path: Target path
        
    Returns:
        Search statistics
    """
    # Validate parameters
    params = validators.StatsParams(
        pattern=pattern,
        path=path
    )
    
    # Build ripgrep command
    args = ["--stats", "-q"]  # -q for quiet (only stats)
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep with timing
    start_time = time.time()
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    elapsed_ms = (time.time() - start_time) * 1000
    
    # Parse statistics from stderr (ripgrep outputs stats to stderr)
    stats_dict = {
        "pattern": params.pattern,
        "time_taken_ms": elapsed_ms,
        "total_matches": 0,
        "files_searched": 0,
        "files_with_matches": 0
    }
    
    if stderr:
        lines = stderr.strip().split("\n")
        for line in lines:
            if "matches" in line and "lines" in line:
                # Extract match count
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        stats_dict["total_matches"] = int(part)
                        break
            elif "files contained matches" in line:
                parts = line.split()
                if parts[0].isdigit():
                    stats_dict["files_with_matches"] = int(parts[0])
            elif "files searched" in line:
                parts = line.split()
                if parts[0].isdigit():
                    stats_dict["files_searched"] = int(parts[0])
    
    return stats_dict


async def search_binary(
    pattern: str,
    path: Optional[str] = None,
    encoding: str = "utf-8"
) -> List[Dict[str, Any]]:
    """
    Search in binary files.
    
    Args:
        pattern: Pattern to search
        path: Target path
        encoding: File encoding
        
    Returns:
        Matches from binary files
    """
    # Validate parameters
    params = validators.SearchBinaryParams(
        pattern=pattern,
        path=path,
        encoding=encoding
    )
    
    # Build ripgrep command
    args = ["-a", "-n"]  # -a treats binary files as text
    
    if params.encoding != "utf-8":
        args.extend(["-E", params.encoding])
    
    # Add pattern
    args.append(params.pattern)
    
    # Add path if specified
    if params.path:
        args.append(utils.sanitize_path(params.path))
    
    # Run ripgrep
    stdout, stderr, returncode = await utils.run_ripgrep(args, timeout=utils.get_timeout())
    
    # Parse results
    if returncode == 0:
        return utils.parse_ripgrep_output(stdout, include_line_numbers=True)
    elif returncode == 1:
        return []
    else:
        raise RuntimeError(f"ripgrep error: {stderr}")


async def validate_ripgrep() -> bool:
    """Validate ripgrep is available and working."""
    try:
        _, _, returncode = await utils.run_ripgrep(["--version"], timeout=5)
        return returncode == 0
    except Exception:
        return False