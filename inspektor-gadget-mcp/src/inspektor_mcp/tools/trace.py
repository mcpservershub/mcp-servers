"""Tracing tools for various system events"""

from typing import Dict, Any
import asyncio

from .base import BaseTool
from ..models import (
    TraceExecRequest,
    TraceNetworkRequest,
    TraceFilesystemRequest,
    CommandResult,
    Target,
    TraceType,
)
from ..utils.gadget_registry import GADGET_IMAGES


class TraceExecTool(BaseTool):
    """Trace process execution in containers or host"""
    
    def get_description(self) -> str:
        return "Trace process execution in containers or host system"
    
    def get_input_model(self):
        return TraceExecRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute trace exec command"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Build command arguments with gadget image
            # For ig run, timeout is specified with -t flag
            args = [GADGET_IMAGES["trace_exec"], "-t", str(validated.duration)]
            
            # Add filtering parameters supported by trace_exec
            if validated.filter_uid is not None:
                args.extend(["--uid", str(validated.filter_uid)])
            
            if validated.filter_comm:
                # Note: trace_exec doesn't have --comm flag in v0.43.0
                # We'll need to filter in post-processing
                pass
            
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            elif validated.target == Target.HOST:
                args.append("--host")
            
            # Run with ig run
            result = await self.executor.execute(
                "run",
                args,
                timeout=validated.duration + 30
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )


class TraceNetworkTool(BaseTool):
    """Comprehensive network tracing"""
    
    def get_description(self) -> str:
        return "Trace network events including DNS, TCP, and connections"
    
    def get_input_model(self):
        return TraceNetworkRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute network tracing commands"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Determine which trace to run
            trace_gadgets = {
                TraceType.DNS: "trace_dns",
                TraceType.TCP: "trace_tcp",
                TraceType.BIND: "trace_bind",
                TraceType.SSL: "trace_ssl",
                TraceType.SNI: "trace_sni",
            }
            
            if validated.trace_type == TraceType.ALL:
                gadget_key = "trace_tcp"  # Use TCP as default for ALL
            else:
                gadget_key = trace_gadgets.get(validated.trace_type, "trace_tcp")
            
            # For ig run, timeout is specified with -t flag
            args = [GADGET_IMAGES[gadget_key], "-t", str(validated.duration)]
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Add specific filters for TCP tracing
            if gadget_key == "trace_tcp":
                # trace_tcp has --accept-only, --connect-only, --failure-only flags
                if validated.show_drops:
                    args.append("--failure-only")
            
            # Execute trace
            result = await self.executor.execute(
                "run",
                args,
                timeout=validated.duration + 30
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )


class TraceFilesystemTool(BaseTool):
    """Trace filesystem operations"""
    
    def get_description(self) -> str:
        return "Monitor file operations including open, mount, and slow I/O"
    
    def get_input_model(self):
        return TraceFilesystemRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute filesystem tracing"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Map trace type to gadget
            fs_gadgets = {
                "open": "trace_open",
                "mount": "trace_mount",
                "fsslower": "trace_fsslower",
            }
            
            gadget_key = fs_gadgets.get(validated.trace_type, "trace_open")
            # For ig run, timeout is specified with -t flag
            args = [GADGET_IMAGES[gadget_key], "-t", str(validated.duration)]
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Add trace-specific options (need to check docs for each gadget's flags)
            # Most filesystem gadgets don't have many filter options in v0.43.0
            
            # Execute trace
            result = await self.executor.execute(
                "run",
                args,
                timeout=validated.duration + 30
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )