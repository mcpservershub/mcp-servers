"""Analysis tools for debugging complex issues"""

from typing import Dict, Any

from .base import BaseTool
from ..models import AnalyzeDeadlockRequest, CommandResult
from ..utils.gadget_registry import GADGET_IMAGES


class AnalyzeDeadlockTool(BaseTool):
    """Detect potential deadlocks in applications"""
    
    def get_description(self) -> str:
        return "Detect potential deadlocks in applications"
    
    def get_input_model(self):
        return AnalyzeDeadlockRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute deadlock analysis"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Build command arguments with gadget image
            # For ig run, timeout is specified with -t flag
            args = [GADGET_IMAGES["deadlock"], "-t", str(validated.duration)]
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Execute deadlock detection using 'ig run'
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