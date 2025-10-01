#!/usr/bin/env python3
"""
strace MCP Server - Main server implementation
"""

import asyncio
import subprocess
import shutil
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator


# Create the FastMCP server instance
mcp = FastMCP("strace-mcp-server")


class TraceOptions(BaseModel):
    """Common options for trace operations"""
    trace_filter: str = Field(default="all", description="Filter: all, file, network, process, memory, signal")
    follow_forks: bool = Field(default=False, description="Follow child processes")
    max_string_size: int = Field(default=32, description="Maximum string size to capture")
    timeout: int = Field(default=30, description="Timeout in seconds")
    show_timestamps: bool = Field(default=False, description="Include timestamps in output")
    
    @field_validator('trace_filter')
    def validate_filter(cls, v):
        valid_filters = ['all', 'file', 'network', 'process', 'memory', 'signal', 'ipc', 'desc']
        if v not in valid_filters:
            raise ValueError(f"Invalid filter: {v}. Must be one of: {', '.join(valid_filters)}")
        return v
    
    @field_validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v


def check_strace_available():
    """Check if strace is available on the system"""
    return shutil.which("strace") is not None


def build_strace_command(base_cmd: List[str], options: TraceOptions) -> List[str]:
    """Build strace command with options"""
    cmd = ["strace"]
    
    # Add filter options
    filter_map = {
        'file': ['-e', 'trace=%file'],
        'network': ['-e', 'trace=%network'],
        'process': ['-e', 'trace=%process'],
        'memory': ['-e', 'trace=%memory'],
        'signal': ['-e', 'trace=%signal'],
        'ipc': ['-e', 'trace=%ipc'],
        'desc': ['-e', 'trace=%desc']
    }
    
    if options.trace_filter != 'all' and options.trace_filter in filter_map:
        cmd.extend(filter_map[options.trace_filter])
    
    # Add other options
    if options.follow_forks:
        cmd.append("-f")
    
    cmd.extend(["-s", str(options.max_string_size)])
    
    if options.show_timestamps:
        cmd.append("-t")
    
    # Add the base command
    cmd.extend(base_cmd)
    
    return cmd


async def run_strace(cmd: List[str], timeout: int) -> Dict[str, Any]:
    """Execute strace command and return results"""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024*1024  # 1MB buffer limit
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.terminate()
            await asyncio.sleep(0.1)
            if proc.returncode is None:
                proc.kill()
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        
        # strace outputs to stderr by default
        output = stderr.decode('utf-8', errors='replace')
        
        return {
            "success": True,
            "output": output,
            "lines": len(output.splitlines()),
            "truncated": len(output) > 100000
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def trace_command(
    command: str,
    args: Optional[List[str]] = None,
    trace_filter: str = "all",
    follow_forks: bool = False,
    max_string_size: int = 32,
    timeout: int = 30,
    show_timestamps: bool = False
) -> Dict[str, Any]:
    """
    Trace system calls of a command
    
    Args:
        command: Command to execute and trace
        args: Arguments for the command
        trace_filter: Filter type (all, file, network, process, memory, signal, ipc, desc)
        follow_forks: Follow child processes
        max_string_size: Maximum string size to capture
        timeout: Timeout in seconds
        show_timestamps: Include timestamps in output
    
    Returns:
        Trace output and metadata
    """
    if not check_strace_available():
        return {"success": False, "error": "strace is not available on this system"}
    
    # Validate options
    try:
        options = TraceOptions(
            trace_filter=trace_filter,
            follow_forks=follow_forks,
            max_string_size=max_string_size,
            timeout=timeout,
            show_timestamps=show_timestamps
        )
    except Exception as e:
        return {"success": False, "error": f"Invalid options: {str(e)}"}
    
    # Build command
    base_cmd = [command]
    if args:
        base_cmd.extend(args)
    
    strace_cmd = build_strace_command(base_cmd, options)
    
    # Run strace
    result = await run_strace(strace_cmd, timeout)
    result["command"] = " ".join(base_cmd)
    result["filter"] = trace_filter
    
    return result


@mcp.tool()
async def trace_process(
    pid: int,
    duration: int = 10,
    trace_filter: str = "all",
    follow_children: bool = False,
    show_timestamps: bool = False
) -> Dict[str, Any]:
    """
    Attach to and trace an existing process
    
    Args:
        pid: Process ID to attach to
        duration: Duration to trace in seconds
        trace_filter: Filter type (all, file, network, process, memory, signal, ipc, desc)
        follow_children: Follow child processes
        show_timestamps: Include timestamps in output
    
    Returns:
        Trace output and metadata
    """
    if not check_strace_available():
        return {"success": False, "error": "strace is not available on this system"}
    
    # Check if process exists
    if not os.path.exists(f"/proc/{pid}"):
        return {"success": False, "error": f"Process with PID {pid} not found"}
    
    # Validate options
    try:
        options = TraceOptions(
            trace_filter=trace_filter,
            follow_forks=follow_children,
            timeout=duration,
            show_timestamps=show_timestamps
        )
    except Exception as e:
        return {"success": False, "error": f"Invalid options: {str(e)}"}
    
    # Build command for attaching to process
    cmd = ["timeout", str(duration)]
    strace_cmd = build_strace_command(["-p", str(pid)], options)
    cmd.extend(strace_cmd)
    
    # Run strace
    result = await run_strace(cmd, duration + 2)  # Add 2 seconds buffer
    result["pid"] = pid
    result["duration"] = duration
    result["filter"] = trace_filter
    
    return result


@mcp.tool()
async def analyze_syscalls(
    command: str,
    args: Optional[List[str]] = None,
    sort_by: str = "time",
    show_errors_only: bool = False,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Generate statistical analysis of system calls
    
    Args:
        command: Command to execute and analyze
        args: Arguments for the command
        sort_by: Sort results by (time, calls, errors, syscall)
        show_errors_only: Only show failed syscalls
        timeout: Timeout in seconds
    
    Returns:
        System call statistics
    """
    if not check_strace_available():
        return {"success": False, "error": "strace is not available on this system"}
    
    # Validate sort option
    valid_sorts = ['time', 'calls', 'errors', 'syscall', 'name']
    if sort_by not in valid_sorts:
        return {"success": False, "error": f"Invalid sort option. Must be one of: {', '.join(valid_sorts)}"}
    
    # Build command for statistics
    cmd = ["strace", "-c"]
    
    if sort_by != "time":
        sort_map = {
            'calls': 'calls',
            'errors': 'errors', 
            'syscall': 'name',
            'name': 'name'
        }
        cmd.extend(["-S", sort_map[sort_by]])
    
    if show_errors_only:
        cmd.extend(["-e", "status=failed"])
    
    # Add the command to trace
    cmd.append(command)
    if args:
        cmd.extend(args)
    
    # Run strace with statistics
    result = await run_strace(cmd, timeout)
    result["command"] = command if not args else f"{command} {' '.join(args)}"
    result["sort_by"] = sort_by
    result["errors_only"] = show_errors_only
    
    return result


@mcp.tool()
async def trace_file_operations(
    command: str,
    args: Optional[List[str]] = None,
    path_filter: Optional[str] = None,
    show_reads: bool = True,
    show_writes: bool = True,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Trace file system operations
    
    Args:
        command: Command to execute and trace
        args: Arguments for the command
        path_filter: Optional path to filter operations
        show_reads: Include read operations
        show_writes: Include write operations
        timeout: Timeout in seconds
    
    Returns:
        File operation trace results
    """
    if not check_strace_available():
        return {"success": False, "error": "strace is not available on this system"}
    
    # Build command
    cmd = ["strace", "-e", "trace=%file"]
    
    # Add path filter if specified
    if path_filter:
        cmd.extend(["-P", path_filter])
    
    # Add read/write filters
    if show_reads and not show_writes:
        cmd.extend(["-e", "read=all"])
    elif show_writes and not show_reads:
        cmd.extend(["-e", "write=all"])
    elif show_reads and show_writes:
        cmd.extend(["-e", "read=all", "-e", "write=all"])
    
    cmd.append(command)
    if args:
        cmd.extend(args)
    
    # Run strace
    result = await run_strace(cmd, timeout)
    result["command"] = command if not args else f"{command} {' '.join(args)}"
    result["path_filter"] = path_filter
    result["show_reads"] = show_reads
    result["show_writes"] = show_writes
    
    return result


@mcp.tool()
async def trace_network_activity(
    command: str,
    args: Optional[List[str]] = None,
    show_data: bool = False,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Monitor network-related system calls
    
    Args:
        command: Command to execute and trace
        args: Arguments for the command
        show_data: Show data transferred (increases output size)
        timeout: Timeout in seconds
    
    Returns:
        Network activity trace results
    """
    if not check_strace_available():
        return {"success": False, "error": "strace is not available on this system"}
    
    # Build command
    cmd = ["strace", "-e", "trace=%network"]
    
    if show_data:
        cmd.extend(["-s", "256", "-e", "read=all", "-e", "write=all"])
    
    cmd.append(command)
    if args:
        cmd.extend(args)
    
    # Run strace
    result = await run_strace(cmd, timeout)
    result["command"] = command if not args else f"{command} {' '.join(args)}"
    result["show_data"] = show_data
    
    return result


@mcp.tool()
async def list_available_filters() -> Dict[str, Any]:
    """
    List all available trace filters and their descriptions
    
    Returns:
        Dictionary of available filters and descriptions
    """
    filters = {
        "all": "Trace all system calls",
        "file": "Trace file-related system calls (open, close, read, write, etc.)",
        "network": "Trace network-related system calls (socket, connect, send, recv, etc.)",
        "process": "Trace process-related system calls (fork, exec, wait, etc.)",
        "memory": "Trace memory-related system calls (mmap, brk, etc.)",
        "signal": "Trace signal-related system calls",
        "ipc": "Trace IPC-related system calls (msgget, semget, etc.)",
        "desc": "Trace file descriptor-related system calls"
    }
    
    return {
        "success": True,
        "filters": filters,
        "note": "Use these filters with trace_command or trace_process tools"
    }


def main():
    """Main entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()