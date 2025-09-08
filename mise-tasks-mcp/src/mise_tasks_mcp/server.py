#!/usr/bin/env python3
"""MCP server for mise tasks and configuration management."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .utils.command import run_mise_command
from .utils.validator import (
    validate_env_var_name,
    validate_task_name,
    validate_config_key,
    sanitize_input
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("mise-tasks-mcp")


# Environment Management Tools

@mcp.tool()
async def set_env(key: str, value: str, file: Optional[str] = None) -> Dict[str, Any]:
    """
    Set an environment variable in mise.
    
    Args:
        key: Environment variable name
        value: Environment variable value
        file: Optional file to update (.env or .mise.toml)
        
    Returns:
        Operation result with status
    """
    if not validate_env_var_name(key):
        return {
            "success": False,
            "error": f"Invalid environment variable name: {key}"
        }
    
    args = ["env", "set"]
    if file:
        args.extend(["--file", file])
    args.extend([key, value])
    
    result = await run_mise_command("", args)
    
    return {
        "success": result.success,
        "key": key,
        "value": value,
        "output": result.output if result.success else None,
        "error": result.error if not result.success else None
    }


@mcp.tool()
async def get_env(key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get environment variable(s) from mise.
    
    Args:
        key: Optional specific environment variable to get
        
    Returns:
        Environment variable(s) and their values
    """
    if key and not validate_env_var_name(key):
        return {
            "success": False,
            "error": f"Invalid environment variable name: {key}"
        }
    
    if key:
        args = ["env", "get", key]
    else:
        args = ["env"]
    
    result = await run_mise_command("", args)
    
    if result.success:
        if key:
            # Single variable
            return {
                "success": True,
                "key": key,
                "value": result.output
            }
        else:
            # Parse all variables
            env_vars = {}
            for line in result.output.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    env_vars[k] = v
            return {
                "success": True,
                "variables": env_vars
            }
    else:
        return {
            "success": False,
            "error": result.error
        }


@mcp.tool()
async def unset_env(key: str, file: Optional[str] = None) -> Dict[str, Any]:
    """
    Unset an environment variable in mise.
    
    Args:
        key: Environment variable name to unset
        file: Optional file to update (.env or .mise.toml)
        
    Returns:
        Operation result with status
    """
    if not validate_env_var_name(key):
        return {
            "success": False,
            "error": f"Invalid environment variable name: {key}"
        }
    
    args = ["env", "unset"]
    if file:
        args.extend(["--file", file])
    args.append(key)
    
    result = await run_mise_command("", args)
    
    return {
        "success": result.success,
        "key": key,
        "output": result.output if result.success else None,
        "error": result.error if not result.success else None
    }


# Task Management Tools

@mcp.tool()
async def task_run(task: str, args: Optional[str] = None, cd: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a mise task.
    
    Args:
        task: Task name to run
        args: Optional arguments to pass to the task
        cd: Optional directory to run the task in
        
    Returns:
        Task execution result
    """
    if not validate_task_name(task):
        return {
            "success": False,
            "error": f"Invalid task name: {task}"
        }
    
    cmd_args = ["tasks", "run"]
    if cd:
        cmd_args.extend(["--cd", cd])
    cmd_args.append(task)
    
    if args:
        # Split args and add them
        cmd_args.extend(args.split())
    
    result = await run_mise_command("", cmd_args, timeout=60.0)
    
    return {
        "success": result.success,
        "task": task,
        "output": result.output,
        "error": result.error if not result.success else None,
        "return_code": result.return_code
    }


@mcp.tool()
async def task_ls(hidden: bool = False) -> Dict[str, Any]:
    """
    List available mise tasks.
    
    Args:
        hidden: Include hidden tasks
        
    Returns:
        List of available tasks with descriptions
    """
    args = ["tasks", "ls"]
    if hidden:
        args.append("--hidden")
    
    result = await run_mise_command("", args)
    
    if result.success:
        # Parse task list
        tasks = []
        for line in result.output.split('\n'):
            if line.strip():
                # Tasks are typically formatted as "name description"
                parts = line.split(None, 1)
                if parts:
                    task_info = {"name": parts[0]}
                    if len(parts) > 1:
                        task_info["description"] = parts[1]
                    tasks.append(task_info)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    else:
        return {
            "success": False,
            "error": result.error
        }


@mcp.tool()
async def task_info(task: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific task.
    
    Args:
        task: Task name to get info for
        
    Returns:
        Detailed task information
    """
    if not validate_task_name(task):
        return {
            "success": False,
            "error": f"Invalid task name: {task}"
        }
    
    args = ["tasks", "info", task]
    result = await run_mise_command("", args)
    
    if result.success:
        # Parse task info
        info = {
            "name": task,
            "raw_output": result.output
        }
        
        # Try to extract structured info from output
        lines = result.output.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                info[key] = value.strip()
        
        return {
            "success": True,
            "task_info": info
        }
    else:
        return {
            "success": False,
            "error": result.error
        }


@mcp.tool()
async def task_edit(task: str, editor: Optional[str] = None) -> Dict[str, Any]:
    """
    Open a task for editing in the configured editor.
    
    Args:
        task: Task name to edit
        editor: Optional editor to use (defaults to $EDITOR)
        
    Returns:
        Status of the edit operation
    """
    if not validate_task_name(task):
        return {
            "success": False,
            "error": f"Invalid task name: {task}"
        }
    
    args = ["tasks", "edit", task]
    
    env = {}
    if editor:
        env["EDITOR"] = editor
    
    # Note: This might open an interactive editor
    result = await run_mise_command("", args, env=env if env else None)
    
    return {
        "success": result.success,
        "task": task,
        "message": "Task opened for editing" if result.success else None,
        "error": result.error if not result.success else None
    }


@mcp.tool()
async def task_deps(task: str) -> Dict[str, Any]:
    """
    List dependencies for a specific task.
    
    Args:
        task: Task name to get dependencies for
        
    Returns:
        List of task dependencies
    """
    if not validate_task_name(task):
        return {
            "success": False,
            "error": f"Invalid task name: {task}"
        }
    
    args = ["tasks", "deps", task]
    result = await run_mise_command("", args)
    
    if result.success:
        # Parse dependencies
        deps = []
        for line in result.output.split('\n'):
            if line.strip():
                deps.append(line.strip())
        
        return {
            "success": True,
            "task": task,
            "dependencies": deps,
            "count": len(deps)
        }
    else:
        return {
            "success": False,
            "error": result.error
        }


# Configuration Tools

@mcp.tool()
async def get_config(key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get mise configuration value(s).
    
    Args:
        key: Optional specific configuration key to get
        
    Returns:
        Configuration value(s)
    """
    if key and not validate_config_key(key):
        return {
            "success": False,
            "error": f"Invalid configuration key: {key}"
        }
    
    args = ["config", "get"]
    if key:
        args.append(key)
    
    result = await run_mise_command("", args)
    
    if result.success:
        if key:
            return {
                "success": True,
                "key": key,
                "value": result.output
            }
        else:
            # Try to parse as JSON for full config
            try:
                config = json.loads(result.output)
                return {
                    "success": True,
                    "config": config
                }
            except json.JSONDecodeError:
                # Return raw output if not JSON
                return {
                    "success": True,
                    "raw_config": result.output
                }
    else:
        return {
            "success": False,
            "error": result.error
        }


@mcp.tool()
async def current_config() -> Dict[str, Any]:
    """
    Show current mise configuration with sources.
    
    Returns:
        Current configuration and its sources
    """
    args = ["config", "ls"]
    result = await run_mise_command("", args)
    
    if result.success:
        # Parse config sources
        config_files = []
        for line in result.output.split('\n'):
            if line.strip():
                config_files.append(line.strip())
        
        return {
            "success": True,
            "config_files": config_files,
            "count": len(config_files)
        }
    else:
        return {
            "success": False,
            "error": result.error
        }


# Utility Tools

@mcp.tool()
async def self_update(version: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Update mise CLI to the latest or specified version.
    
    Args:
        version: Optional specific version to update to
        force: Force update even if already on latest
        
    Returns:
        Update status and version information
    """
    args = ["self-update"]
    if version:
        args.append(version)
    if force:
        args.append("--force")
    
    result = await run_mise_command("", args, timeout=120.0)
    
    return {
        "success": result.success,
        "output": result.output,
        "error": result.error if not result.success else None
    }


@mcp.tool()
async def fmt_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Format mise configuration files.
    
    Args:
        path: Optional specific path to format (defaults to current directory)
        
    Returns:
        Format operation result
    """
    args = ["fmt"]
    if path:
        args.append(path)
    
    result = await run_mise_command("", args)
    
    return {
        "success": result.success,
        "formatted_files": result.output.split('\n') if result.success and result.output else [],
        "error": result.error if not result.success else None
    }


# Main entry point
def main():
    """Run the MCP server."""
    import sys
    
    try:
        logger.info("Starting mise-tasks-mcp server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()