"""Container management tools"""

from typing import Dict, Any

from .base import BaseTool
from ..models import ListContainersRequest, CommandResult


class ListContainersTool(BaseTool):
    """List running containers across different runtimes"""
    
    def get_description(self) -> str:
        return "List all running containers with their metadata"
    
    def get_input_model(self):
        return ListContainersRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute list-containers command"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Build command arguments
            args = []
            
            # For ig list-containers, use --runtimes (plural) not --runtime
            if validated.runtime and validated.runtime != "all":
                args.extend(["--runtimes", validated.runtime])
            
            if validated.containername:
                args.extend(["--containername", validated.containername])
            
            # Note: --namespace flag doesn't exist in ig list-containers
            # It has --containerd-namespace for containerd-specific namespace
            
            # Execute command
            result = await self.executor.execute(
                "list-containers",
                args,
                parse_json=(validated.output_format == "json")
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )