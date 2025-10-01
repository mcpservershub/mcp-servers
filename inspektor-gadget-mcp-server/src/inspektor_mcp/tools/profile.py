"""Profiling tools for performance analysis"""

from typing import Dict, Any

from .base import BaseTool
from ..models import ProfileCPURequest, ProfileIORequest, CommandResult, Target


class ProfileCPUTool(BaseTool):
    """CPU profiling with flame graph support"""
    
    def get_description(self) -> str:
        return "Profile CPU usage and generate flame graphs"
    
    def get_input_model(self):
        return ProfileCPURequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute CPU profiling"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Build command arguments for ig run
            # Use the gadget image format with version tag
            gadget_image = "ghcr.io/inspektor-gadget/gadget/profile_cpu:v0.43.0"
            # For ig run, timeout is specified with -t flag
            args = [gadget_image, "-t", str(validated.duration)]
            
            # Add container filtering or host flag
            if validated.target == Target.CONTAINER and validated.container_name:
                args.extend(["--containername", validated.container_name])
            elif validated.target == Target.HOST:
                args.append("--host")
            
            # Execute profiling using 'ig run'
            result = await self.executor.execute(
                "run",
                args,
                timeout=validated.duration + 30,  # Add buffer for command timeout
                parse_json=True
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )


class ProfileIOTool(BaseTool):
    """I/O profiling for block I/O and TCP RTT"""
    
    def get_description(self) -> str:
        return "Profile I/O operations including block I/O and TCP round-trip time"
    
    def get_input_model(self):
        return ProfileIORequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute I/O profiling"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Determine gadget image based on profile type with version tag
            if validated.profile_type == "blockio":
                gadget_image = "ghcr.io/inspektor-gadget/gadget/profile_blockio:v0.43.0"
            else:  # tcprtt
                gadget_image = "ghcr.io/inspektor-gadget/gadget/profile_tcprtt:v0.43.0"
            
            # Build command arguments with timeout
            args = [gadget_image, "-t", str(validated.duration)]
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Execute profiling
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