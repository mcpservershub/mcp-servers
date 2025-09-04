"""Command executor for running ig commands"""

import asyncio
import json
import shutil
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..config import settings
from .errors import (
    IGNotFoundError,
    GadgetExecutionError,
    TimeoutError,
    PermissionError,
)


class CommandExecutor:
    """Execute ig commands with proper error handling"""
    
    def __init__(self):
        self._ig_binary = None
        self.default_timeout = settings.ig_default_timeout
    
    @property
    def ig_binary(self) -> str:
        """Lazy initialization of ig binary path"""
        if self._ig_binary is None:
            self._ig_binary = self._find_ig_binary()
        return self._ig_binary
    
    def _find_ig_binary(self) -> str:
        """Find the ig binary path"""
        ig_path = settings.ig_binary_path
        
        # Check if it's an absolute path
        if Path(ig_path).is_absolute() and Path(ig_path).exists():
            return ig_path
        
        # Check if it's in PATH
        binary = shutil.which(ig_path)
        if binary:
            return binary
        
        # Check common locations
        common_paths = [
            "/usr/local/bin/ig",
            "/usr/bin/ig",
            "/opt/ig/bin/ig",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        raise IGNotFoundError(
            f"Inspektor-Gadget binary not found. Searched: {ig_path}, PATH, and common locations"
        )
    
    async def execute(
        self,
        command: str,
        args: List[str],
        timeout: Optional[int] = None,
        parse_json: bool = True
    ) -> Dict[str, Any]:
        """
        Execute an ig command
        
        Args:
            command: The ig subcommand (e.g., "trace", "snapshot")
            args: Arguments for the command
            timeout: Command timeout in seconds
            parse_json: Whether to parse JSON output
        
        Returns:
            Dictionary with success, data, error, and metadata
        """
        timeout = timeout or self.default_timeout
        
        # Build full command
        cmd_args = [self.ig_binary, command] + args
        
        # Add JSON output flag if needed
        if parse_json and "--output" not in args and "-o" not in args:
            cmd_args.extend(["--output", "json"])
        
        start_time = time.time()
        
        try:
            # Create subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check return code
            if proc.returncode != 0:
                stderr_text = stderr.decode("utf-8", errors="ignore")
                
                # Check for permission errors
                if "permission denied" in stderr_text.lower() or "operation not permitted" in stderr_text.lower():
                    raise PermissionError(
                        "Insufficient permissions. Inspektor-Gadget requires root or CAP_SYS_ADMIN capability"
                    )
                
                # Check for daemon connection errors
                if "ig.socket" in stderr_text or "container-collection isn't available" in stderr_text:
                    raise GadgetExecutionError(
                        "ig daemon not running or insufficient permissions. "
                        "Please ensure:\n"
                        "1. You're running the MCP server with sudo/root privileges\n"
                        "2. The ig daemon is running (if required for your setup)\n"
                        "3. Container runtime is accessible\n\n"
                        f"Original error: {stderr_text}"
                    )
                
                raise GadgetExecutionError(f"Command failed: {stderr_text}")
            
            # Parse output
            stdout_text = stdout.decode("utf-8", errors="ignore")
            
            if parse_json and stdout_text.strip():
                try:
                    # Handle streaming JSON (one object per line)
                    if "\n" in stdout_text and stdout_text.strip().startswith("{"):
                        data = [
                            json.loads(line)
                            for line in stdout_text.strip().split("\n")
                            if line.strip()
                        ]
                    else:
                        data = json.loads(stdout_text)
                except json.JSONDecodeError:
                    # Fallback to raw text
                    data = stdout_text
            else:
                data = stdout_text
            
            return {
                "success": True,
                "data": data,
                "command": " ".join(cmd_args),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            if isinstance(e, (TimeoutError, PermissionError, GadgetExecutionError)):
                raise
            
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd_args),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def execute_streaming(
        self,
        command: str,
        args: List[str],
        timeout: Optional[int] = None
    ):
        """
        Execute a command and yield output lines as they come
        
        Useful for long-running traces
        """
        timeout = timeout or self.default_timeout
        cmd_args = [self.ig_binary, command] + args
        
        # Ensure JSON output for streaming
        if "--output" not in args and "-o" not in args:
            cmd_args.extend(["--output", "json"])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            async def read_stream():
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    
                    line_text = line.decode("utf-8", errors="ignore").strip()
                    if line_text:
                        try:
                            yield json.loads(line_text)
                        except json.JSONDecodeError:
                            yield {"raw": line_text}
            
            # Use asyncio timeout
            async with asyncio.timeout(timeout):
                async for item in read_stream():
                    yield item
                    
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            yield {"error": f"Command timed out after {timeout} seconds"}
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()