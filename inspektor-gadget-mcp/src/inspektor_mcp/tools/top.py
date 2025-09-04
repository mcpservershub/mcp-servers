"""Top tools for resource monitoring"""

from typing import Dict, Any

from .base import BaseTool
from ..models import TopResourcesRequest, CommandResult, ResourceType


class TopResourcesTool(BaseTool):
    """Monitor top resource consumers"""
    
    def get_description(self) -> str:
        return "Monitor top resource consumers in real-time"
    
    def get_input_model(self):
        return TopResourcesRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute top monitoring"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Map resource type to gadget image with v0.43.0 tag
            resource_map = {
                ResourceType.PROCESS: "ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0",
                ResourceType.FILE: "ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0",
                ResourceType.TCP: "ghcr.io/inspektor-gadget/gadget/top_tcp:v0.43.0",
                ResourceType.BLOCKIO: "ghcr.io/inspektor-gadget/gadget/top_blockio:v0.43.0",
            }
            
            if validated.resource_type == ResourceType.ALL:
                # For 'all', we'll run process top as the most comprehensive
                gadget_image = resource_map[ResourceType.PROCESS]
            else:
                gadget_image = resource_map[validated.resource_type]
            
            # Build command arguments
            # For ig run, timeout is specified with -t flag
            timeout = max(validated.interval * 10, 60)  # Minimum 60 seconds
            args = [gadget_image, "-t", str(timeout)]
            
            # Add max-rows parameter if supported by the gadget
            if validated.resource_type in [ResourceType.PROCESS, ResourceType.FILE]:
                args.extend(["--max-entries", str(validated.max_rows)])
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Execute top command using 'ig run'
            result = await self.executor.execute(
                "run",
                args,
                timeout=timeout + 30  # Add generous buffer
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )