"""Flexible gadget runner tool"""

from typing import Dict, Any

from .base import BaseTool
from ..models import RunGadgetRequest, CommandResult
from ..utils.gadget_registry import GADGET_IMAGES


class RunGadgetTool(BaseTool):
    """Run arbitrary Inspektor Gadget gadgets with custom parameters"""
    
    def get_description(self) -> str:
        return "Run any Inspektor Gadget with custom parameters"
    
    def get_input_model(self):
        return RunGadgetRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute arbitrary gadget with user-specified parameters"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Resolve gadget name - support both short names and full URLs
            gadget_name = validated.gadget_name
            
            # Check if it's a short name that we can expand
            if gadget_name in GADGET_IMAGES:
                gadget_name = GADGET_IMAGES[gadget_name]
            elif not gadget_name.startswith(("ghcr.io/", "docker.io/", "quay.io/")):
                # If it's not a full URL and not in our registry, 
                # try to construct a default URL
                if "/" not in gadget_name:
                    # Assume it's a gadget name without version
                    if ":v" not in gadget_name:
                        gadget_name = f"ghcr.io/inspektor-gadget/gadget/{gadget_name}:v0.43.0"
                    else:
                        gadget_name = f"ghcr.io/inspektor-gadget/gadget/{gadget_name}"
            
            # Build command arguments
            args = [gadget_name]
            
            # Add user-provided arguments first (they might include timeout or other flags)
            if validated.args:
                args.extend(validated.args)
            
            # Add container filtering or host flag
            # Only add if not already present in user args
            if validated.container_name:
                if "--containername" not in validated.args:
                    args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host (if not already specified)
                if "--host" not in validated.args and "--containername" not in validated.args:
                    args.append("--host")
            
            # Execute gadget using 'ig run'
            result = await self.executor.execute(
                "run",
                args,
                timeout=validated.timeout_seconds
            )
            
            # Add metadata about the execution
            if result.get("success"):
                result["metadata"] = {
                    "gadget": validated.gadget_name,
                    "target": validated.container_name if validated.container_name else "host",
                    "custom_args": validated.args,
                    "timeout": validated.timeout_seconds
                }
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )