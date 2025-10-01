"""Command execution utilities for mise-tasks-mcp."""

import asyncio
import shutil
from dataclasses import dataclass
from typing import List, Optional
import os


@dataclass
class CommandResult:
    """Result of a command execution."""
    
    success: bool
    output: str
    error: str
    return_code: int


async def run_mise_command(
    command: str, 
    args: Optional[List[str]] = None,
    timeout: float = 30.0,
    env: Optional[dict] = None
) -> CommandResult:
    """
    Execute a mise command asynchronously.
    
    Args:
        command: The mise subcommand to run
        args: Optional list of arguments for the command
        timeout: Timeout in seconds for command execution
        env: Optional environment variables to set
        
    Returns:
        CommandResult containing the outcome of the command
    """
    mise_path = shutil.which("mise")
    if not mise_path:
        return CommandResult(
            success=False,
            output="",
            error="mise CLI not found in PATH",
            return_code=1
        )
    
    cmd_parts = [mise_path, command]
    if args:
        cmd_parts.extend(args)
    
    # Prepare environment
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=cmd_env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                return_code=-1
            )
        
        return CommandResult(
            success=process.returncode == 0,
            output=stdout.decode("utf-8", errors="replace").strip(),
            error=stderr.decode("utf-8", errors="replace").strip(),
            return_code=process.returncode or 0
        )
        
    except Exception as e:
        return CommandResult(
            success=False,
            output="",
            error=f"Failed to execute command: {str(e)}",
            return_code=1
        )