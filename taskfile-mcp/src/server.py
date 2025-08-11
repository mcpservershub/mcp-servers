"""Simplified MCP Server for Taskfile development using Task CLI."""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from mcp.server import FastMCP

# Initialize MCP server
mcp = FastMCP("taskfile-mcp")


class TaskCLIWrapper:
    """Simple wrapper for Task CLI operations."""
    
    def __init__(self):
        self.task_binary = self._find_task_binary()
    
    def _find_task_binary(self) -> str:
        """Find the task binary in the system."""
        task_path = shutil.which("task")
        if not task_path:
            raise RuntimeError(
                "Task CLI not found. Please install it from https://taskfile.dev/installation"
            )
        return task_path
    
    async def run(self, args: list[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run task command and return output."""
        cmd = [self.task_binary] + args
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or Path.cwd()
        )
        
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode(), stderr.decode()


# Global CLI instance
cli = TaskCLIWrapper()


# Tool Implementations

@mcp.tool()
async def list_tasks(
    working_dir: Optional[str] = None,
    taskfile: Optional[str] = None,
    json_output: bool = True,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """List all available tasks in the Taskfile.
    
    Uses 'task --list-all' to get all tasks with descriptions.
    
    Args:
        working_dir: Directory containing the Taskfile
        taskfile: Optional path to a specific Taskfile (e.g., 'simple-python.yml')
        json_output: If true, return JSON format, otherwise text
        output_file: Optional file path to save the output
    """
    try:
        args = []
        if taskfile:
            args.extend(["-t", taskfile])
        args.append("--list-all")
        if json_output:
            args.append("--json")
        
        returncode, stdout, stderr = await cli.run(args, working_dir)
        
        if returncode != 0:
            return {"success": False, "error": stderr or "Failed to list tasks"}
        
        # Save to file if requested
        if output_file and stdout:
            try:
                # Determine the full path for the output file
                if working_dir and not output_file.startswith('/'):
                    # Relative path: save in working_dir
                    file_path = Path(working_dir) / output_file
                else:
                    # Absolute path or current directory
                    file_path = Path(output_file)
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the output
                file_path.write_text(stdout)
                
                # Return success with file info
                if json_output:
                    try:
                        data = json.loads(stdout)
                        return {
                            "success": True, 
                            "tasks": data,
                            "output_file": str(file_path),
                            "message": f"Output saved to {file_path}"
                        }
                    except json.JSONDecodeError:
                        return {
                            "success": True, 
                            "output": stdout,
                            "output_file": str(file_path),
                            "message": f"Output saved to {file_path}"
                        }
                else:
                    return {
                        "success": True, 
                        "output": stdout,
                        "output_file": str(file_path),
                        "message": f"Output saved to {file_path}"
                    }
            except Exception as write_error:
                # Still return the data even if file write fails
                if json_output:
                    try:
                        data = json.loads(stdout)
                        return {
                            "success": True, 
                            "tasks": data,
                            "warning": f"Could not save to file: {write_error}"
                        }
                    except json.JSONDecodeError:
                        return {
                            "success": True, 
                            "output": stdout,
                            "warning": f"Could not save to file: {write_error}"
                        }
                else:
                    return {
                        "success": True, 
                        "output": stdout,
                        "warning": f"Could not save to file: {write_error}"
                    }
        
        # No file output requested, return as before
        if json_output:
            try:
                data = json.loads(stdout)
                return {"success": True, "tasks": data}
            except json.JSONDecodeError:
                return {"success": True, "output": stdout}
        else:
            return {"success": True, "output": stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def run_task(
    task_name: str,
    working_dir: Optional[str] = None,
    taskfile: Optional[str] = None,
    dry_run: bool = False,
    watch: bool = False,
    parallel: bool = False,
    force: bool = False,
    silent: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """Execute a specific task using Task CLI.
    
    Supports all Task CLI flags like dry-run, watch, parallel, etc.
    
    Args:
        task_name: Name of the task to run
        working_dir: Directory containing the Taskfile
        taskfile: Optional path to a specific Taskfile (e.g., 'simple-python.yml')
        dry_run: Perform a dry run without executing
        watch: Run in watch mode
        parallel: Run dependencies in parallel
        force: Force run even if up to date
        silent: Suppress output
        verbose: Show verbose output
    """
    try:
        args = []
        
        if taskfile:
            args.extend(["-t", taskfile])
        if dry_run:
            args.append("--dry")
        if watch:
            args.append("--watch")
        if parallel:
            args.append("--parallel")
        if force:
            args.append("--force")
        if silent:
            args.append("--silent")
        if verbose:
            args.append("--verbose")
        
        args.append(task_name)
        
        returncode, stdout, stderr = await cli.run(args, working_dir)
        
        return {
            "success": returncode == 0,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def init_taskfile(
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Initialize a new Taskfile in the specified directory.
    
    Uses 'task --init' to create a basic Taskfile.yml.
    
    Args:
        working_dir: Directory where to initialize the Taskfile
    """
    try:
        returncode, stdout, stderr = await cli.run(["--init"], working_dir)
        
        if returncode != 0:
            return {"success": False, "error": stderr or "Failed to initialize Taskfile"}
        
        return {
            "success": True,
            "message": "Taskfile initialized successfully",
            "output": stdout
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def validate_taskfile(
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Validate a Taskfile by attempting to list tasks.
    
    If Task can parse and list tasks, the Taskfile is valid.
    
    Args:
        working_dir: Directory containing the Taskfile to validate
    """
    try:
        # Try to list tasks - if this works, the Taskfile is valid
        returncode, stdout, stderr = await cli.run(["--list-all", "--silent"], working_dir)
        
        if returncode != 0:
            # Parse error message for helpful feedback
            error_msg = stderr or stdout
            return {
                "success": True,
                "valid": False,
                "error": error_msg,
                "errors": [error_msg]
            }
        
        return {
            "success": True,
            "valid": True,
            "message": "Taskfile is valid"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_task_summary(
    task_name: str,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Get detailed summary of a specific task.
    
    Uses 'task --summary <task>' to show task details.
    
    Args:
        task_name: Name of the task to get summary for
        working_dir: Directory containing the Taskfile
    """
    try:
        args = ["--summary", task_name]
        returncode, stdout, stderr = await cli.run(args, working_dir)
        
        if returncode != 0:
            return {"success": False, "error": stderr or f"Task '{task_name}' not found"}
        
        return {
            "success": True,
            "task": task_name,
            "summary": stdout
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def dry_run(
    task_name: str,
    working_dir: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Perform a dry run to see what commands would be executed.
    
    Shows all commands without actually running them.
    
    Args:
        task_name: Name of the task to dry run
        working_dir: Directory containing the Taskfile
        verbose: Show verbose output
    """
    return await run_task(
        task_name=task_name,
        working_dir=working_dir,
        dry_run=True,
        verbose=verbose
    )


@mcp.tool()
async def watch_task(
    task_name: str,
    working_dir: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run a task in watch mode, re-running when files change.
    
    Requires 'sources' to be defined in the task.
    
    Args:
        task_name: Name of the task to watch
        working_dir: Directory containing the Taskfile
        verbose: Show verbose output
    """
    return await run_task(
        task_name=task_name,
        working_dir=working_dir,
        watch=True,
        verbose=verbose
    )


def main():
    """Main entry point for the MCP server."""
    import sys
    
    # Check if Task CLI is available
    try:
        TaskCLIWrapper()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the MCP server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()