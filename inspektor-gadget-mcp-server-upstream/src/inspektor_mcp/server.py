"""Main MCP Server implementation using FastMCP"""

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP

from .config import settings
from .tools import (
    ListContainersTool,
    TraceExecTool,
    TraceNetworkTool,
    TraceFilesystemTool,
    ProfileCPUTool,
    ProfileIOTool,
    SnapshotSystemTool,
    TopResourcesTool,
    AdviseSecurityTool,
    AnalyzeDeadlockTool,
    RunGadgetTool,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(settings.mcp_server_name)

# Initialize all tools
tools = {
    "list_containers": ListContainersTool(),
    "trace_exec": TraceExecTool(),
    "trace_network": TraceNetworkTool(),
    "trace_filesystem": TraceFilesystemTool(),
    "profile_cpu": ProfileCPUTool(),
    "profile_io": ProfileIOTool(),
    "snapshot_system": SnapshotSystemTool(),
    "top_resources": TopResourcesTool(),
    "advise_security": AdviseSecurityTool(),
    "analyze_deadlock": AnalyzeDeadlockTool(),
    "run_gadget": RunGadgetTool(),
}


# Register each tool with FastMCP using individual parameters
@mcp.tool()
async def list_containers(
    runtime: str = "all",
    namespace: Optional[str] = None,
    containername: Optional[str] = None,
    output_format: str = "json"
) -> Dict[str, Any]:
    """List all running containers with their metadata"""
    try:
        # Build arguments dict, excluding None values
        args = {"runtime": runtime, "output_format": output_format}
        if namespace is not None:
            args["namespace"] = namespace
        if containername is not None:
            args["containername"] = containername
            
        tool = tools["list_containers"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in list_containers: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def trace_exec(
    target: str = "host",
    container_name: Optional[str] = None,
    duration: int = 10,
    filter_uid: Optional[int] = None,
    filter_comm: Optional[str] = None,
    follow_fork: bool = True
) -> Dict[str, Any]:
    """Trace process execution in containers or host system"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "target": target,
            "duration": duration,
            "follow_fork": follow_fork
        }
        if container_name is not None:
            args["container_name"] = container_name
        if filter_uid is not None:
            args["filter_uid"] = filter_uid
        if filter_comm is not None:
            args["filter_comm"] = filter_comm
            
        tool = tools["trace_exec"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in trace_exec: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def trace_network(
    trace_type: str = "tcp",
    container_name: Optional[str] = None,
    duration: int = 10,
    filter_port: Optional[int] = None,
    filter_protocol: str = "tcp",
    show_drops: bool = False,
    show_retransmissions: bool = False
) -> Dict[str, Any]:
    """Trace network events including DNS, TCP, and connections"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "trace_type": trace_type,
            "duration": duration,
            "filter_protocol": filter_protocol,
            "show_drops": show_drops,
            "show_retransmissions": show_retransmissions
        }
        if container_name is not None:
            args["container_name"] = container_name
        if filter_port is not None:
            args["filter_port"] = filter_port
            
        tool = tools["trace_network"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in trace_network: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def trace_filesystem(
    trace_type: str = "open",
    container_name: Optional[str] = None,
    duration: int = 10,
    filter_path: Optional[str] = None,
    min_latency_ms: Optional[int] = None
) -> Dict[str, Any]:
    """Monitor file operations including open, mount, and slow I/O"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "trace_type": trace_type,
            "duration": duration
        }
        if container_name is not None:
            args["container_name"] = container_name
        if filter_path is not None:
            args["filter_path"] = filter_path
        if min_latency_ms is not None:
            args["min_latency_ms"] = min_latency_ms
            
        tool = tools["trace_filesystem"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in trace_filesystem: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def profile_cpu(
    target: str = "host",
    container_name: Optional[str] = None,
    pid: Optional[int] = None,
    duration: int = 30,
    frequency: int = 99,
    output_format: str = "flamegraph"
) -> Dict[str, Any]:
    """Profile CPU usage and generate flame graphs"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "target": target,
            "duration": duration,
            "frequency": frequency,
            "output_format": output_format
        }
        if container_name is not None:
            args["container_name"] = container_name
        if pid is not None:
            args["pid"] = pid
            
        tool = tools["profile_cpu"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in profile_cpu: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def profile_io(
    profile_type: str = "blockio",
    container_name: Optional[str] = None,
    duration: int = 30
) -> Dict[str, Any]:
    """Profile I/O operations including block I/O and TCP round-trip time"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "profile_type": profile_type,
            "duration": duration
        }
        if container_name is not None:
            args["container_name"] = container_name
            
        tool = tools["profile_io"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in profile_io: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def snapshot_system(
    snapshot_type: str = "process",
    container_name: Optional[str] = None,
    include_threads: bool = False,
    include_tcp: bool = True,
    include_udp: bool = True,
    include_unix: bool = False
) -> Dict[str, Any]:
    """Take a snapshot of system state including processes and sockets"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "snapshot_type": snapshot_type,
            "include_threads": include_threads,
            "include_tcp": include_tcp,
            "include_udp": include_udp,
            "include_unix": include_unix
        }
        if container_name is not None:
            args["container_name"] = container_name
            
        tool = tools["snapshot_system"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in snapshot_system: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def top_resources(
    resource_type: str = "process",
    container_name: Optional[str] = None,
    interval: int = 1,
    max_rows: int = 10,
    sort_by: str = "cpu"
) -> Dict[str, Any]:
    """Monitor top resource consumers in real-time"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "resource_type": resource_type,
            "interval": interval,
            "max_rows": max_rows,
            "sort_by": sort_by
        }
        if container_name is not None:
            args["container_name"] = container_name
            
        tool = tools["top_resources"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in top_resources: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def advise_security(
    advice_type: str = "all",
    container_name: str = None,  # Required for this tool
    duration: int = 60,
    output_format: str = "yaml"
) -> Dict[str, Any]:
    """Generate security policies and hardening recommendations"""
    try:
        # This tool requires container_name
        if not container_name:
            return {
                "success": False,
                "error": "container_name is required for security advice",
                "data": None
            }
            
        args = {
            "advice_type": advice_type,
            "container_name": container_name,
            "duration": duration,
            "output_format": output_format
        }
            
        tool = tools["advise_security"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in advise_security: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def analyze_deadlock(
    container_name: Optional[str] = None,
    pid: Optional[int] = None,
    duration: int = 30,
    stack_depth: int = 20
) -> Dict[str, Any]:
    """Detect potential deadlocks in applications"""
    try:
        # Build arguments dict, excluding None values
        args = {
            "duration": duration,
            "stack_depth": stack_depth
        }
        if container_name is not None:
            args["container_name"] = container_name
        if pid is not None:
            args["pid"] = pid
            
        tool = tools["analyze_deadlock"]
        result = await tool.execute(args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in analyze_deadlock: {e}")
        return {"success": False, "error": str(e), "data": None}


@mcp.tool()
async def run_gadget(
    gadget_name: str,
    container_name: Optional[str] = None,
    args: Optional[list] = None,
    timeout_seconds: int = 120
) -> Dict[str, Any]:
    """Run any Inspektor Gadget with custom parameters
    
    Args:
        gadget_name: Gadget name - can be short name (e.g., 'trace_open') or full image URL
        container_name: Container name to monitor (optional, defaults to host)
        args: Additional arguments to pass to the gadget (optional)
        timeout_seconds: Timeout for gadget execution in seconds (1-600, default: 120)
    
    Returns:
        Gadget execution results
    """
    try:
        # Build arguments dict, excluding None values
        tool_args = {
            "gadget_name": gadget_name,
            "timeout_seconds": timeout_seconds
        }
        if container_name is not None:
            tool_args["container_name"] = container_name
        if args is not None:
            tool_args["args"] = args
        
        tool = tools["run_gadget"]
        result = await tool.execute(tool_args)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error in run_gadget: {e}")
        return {"success": False, "error": str(e), "data": None}


# The server is ready to be used
# Run with: python -m inspektor_mcp