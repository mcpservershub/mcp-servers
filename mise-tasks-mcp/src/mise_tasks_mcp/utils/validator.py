"""Input validation utilities for mise-tasks-mcp."""

import re
from typing import Any, Optional


def validate_env_var_name(name: str) -> bool:
    """
    Validate environment variable name.
    
    Args:
        name: The environment variable name to validate
        
    Returns:
        True if the name is valid, False otherwise
    """
    if not name:
        return False
    
    # Must start with letter or underscore, followed by letters, numbers, or underscores
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, name))


def validate_task_name(name: str) -> bool:
    """
    Validate task name format.
    
    Args:
        name: The task name to validate
        
    Returns:
        True if the name is valid, False otherwise
    """
    if not name:
        return False
    
    # Task names can contain alphanumeric, dash, underscore, colon, dot
    pattern = r'^[a-zA-Z0-9_\-:\.]+$'
    return bool(re.match(pattern, name))


def sanitize_input(value: Any) -> str:
    """
    Sanitize input to prevent injection attacks.
    
    Args:
        value: The value to sanitize
        
    Returns:
        Sanitized string value
    """
    if value is None:
        return ""
    
    # Convert to string
    str_value = str(value)
    
    # Remove null bytes
    str_value = str_value.replace('\x00', '')
    
    # Escape shell special characters
    # First escape backslashes, then other characters
    str_value = str_value.replace('\\', '\\\\')
    dangerous_chars = ['`', '$', '&', '|', ';', '<', '>', '(', ')', '{', '}', '[', ']', '"', "'", '\n', '\r']
    for char in dangerous_chars:
        str_value = str_value.replace(char, f'\\{char}')
    
    return str_value


def validate_config_key(key: str) -> bool:
    """
    Validate configuration key format.
    
    Args:
        key: The configuration key to validate
        
    Returns:
        True if the key is valid, False otherwise
    """
    if not key:
        return False
    
    # Config keys are typically dot-separated paths
    pattern = r'^[a-zA-Z0-9_\-]+(\.?[a-zA-Z0-9_\-]+)*$'
    return bool(re.match(pattern, key))