"""Advisory tools for security recommendations"""

from typing import Dict, Any

from .base import BaseTool
from ..models import AdviseSecurityRequest, CommandResult, AdviceType, OutputFormat
from ..utils.gadget_registry import GADGET_IMAGES


class AdviseSecurityTool(BaseTool):
    """Generate security policies and recommendations"""
    
    def get_description(self) -> str:
        return "Generate security policies and hardening recommendations"
    
    def get_input_model(self):
        return AdviseSecurityRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute security advisory"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Map advice type to gadget
            advice_gadgets = {
                AdviceType.NETWORKPOLICY: "advise_networkpolicy",
                AdviceType.SECCOMP: "advise_seccomp",
            }
            
            if validated.advice_type == AdviceType.ALL:
                gadget_key = "advise_networkpolicy"  # Use network policy as default for ALL
            else:
                gadget_key = advice_gadgets.get(validated.advice_type, "advise_networkpolicy")
            
            # For ig run, timeout is specified with -t flag
            args = [GADGET_IMAGES[gadget_key], "-t", str(validated.duration)]
            
            # Container name is typically required for advise commands
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            
            # Execute advise command using 'ig run'
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