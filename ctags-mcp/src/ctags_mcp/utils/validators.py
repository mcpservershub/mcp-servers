"""Validation utilities for CTags MCP server."""

import os
from pathlib import Path
from typing import Optional


def validate_path(path: str) -> tuple[bool, Optional[str]]:
    """Validate a file or directory path.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        return False, f"Path does not exist: {path}"
    
    # Check for path traversal attempts
    try:
        path_obj.resolve()
    except Exception as e:
        return False, f"Invalid path: {e}"
    
    return True, None


def validate_tags_file(tags_file: str) -> tuple[bool, Optional[str]]:
    """Validate a tags file.
    
    Args:
        tags_file: Path to tags file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tags_file:
        return False, "Tags file path cannot be empty"
    
    if not os.path.exists(tags_file):
        return False, f"Tags file not found: {tags_file}"
    
    if not os.path.isfile(tags_file):
        return False, f"Path is not a file: {tags_file}"
    
    # Check if it's a valid tags file by reading first few lines
    try:
        with open(tags_file, 'r') as f:
            first_line = f.readline()
            # Tags files often start with !_TAG_ headers or direct tag entries
            if not (first_line.startswith('!_TAG_') or '\t' in first_line):
                return False, "File does not appear to be a valid tags file"
    except Exception as e:
        return False, f"Cannot read tags file: {e}"
    
    return True, None