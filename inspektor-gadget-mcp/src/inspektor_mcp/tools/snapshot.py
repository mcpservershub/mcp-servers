"""Snapshot tools for point-in-time system state"""

from typing import Dict, Any

from .base import BaseTool
from ..models import SnapshotSystemRequest, CommandResult, SnapshotType
from ..utils.gadget_registry import GADGET_IMAGES


class SnapshotSystemTool(BaseTool):
    """Take snapshots of system state"""
    
    def get_description(self) -> str:
        return "Take a snapshot of system state including processes and sockets"
    
    def get_input_model(self):
        return SnapshotSystemRequest
    
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute system snapshot"""
        try:
            # Validate input
            validated = self.validate_input(arguments)
            
            # Map snapshot type to gadget
            snapshot_gadgets = {
                SnapshotType.PROCESS: "snapshot_process",
                SnapshotType.SOCKET: "snapshot_socket",
            }
            
            if validated.snapshot_type == SnapshotType.ALL:
                gadget_key = "snapshot_process"  # Use process as default for ALL
            else:
                gadget_key = snapshot_gadgets.get(validated.snapshot_type, "snapshot_process")
            
            # For snapshots, we don't need a long timeout
            args = [GADGET_IMAGES[gadget_key], "-t", "5"]
            
            # Add container filtering or host flag
            if validated.container_name:
                args.extend(["--containername", validated.container_name])
            else:
                # No container specified, monitor the host
                args.append("--host")
            
            # Execute snapshot using 'ig run'
            result = await self.executor.execute(
                "run",
                args,
                timeout=60  # Allow more time for complex snapshots
            )
            
            return CommandResult(**result)
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )