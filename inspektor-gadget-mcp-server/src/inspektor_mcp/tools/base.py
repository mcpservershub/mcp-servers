"""Base class for all MCP tools"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

from ..utils import CommandExecutor
from ..models import CommandResult


class BaseTool(ABC):
    """Base class for all Inspektor-Gadget MCP tools"""
    
    def __init__(self):
        self.executor = CommandExecutor()
        self.name = self.__class__.__name__.replace("Tool", "").lower()
    
    @abstractmethod
    def get_description(self) -> str:
        """Get tool description"""
        pass
    
    @abstractmethod
    def get_input_model(self) -> type[BaseModel]:
        """Get Pydantic model for input validation"""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> CommandResult:
        """Execute the tool with given arguments"""
        pass
    
    def validate_input(self, arguments: Dict[str, Any]) -> BaseModel:
        """Validate input using Pydantic model"""
        model_class = self.get_input_model()
        return model_class(**arguments)
    
    def build_args(self, validated_input: BaseModel) -> list[str]:
        """Build command arguments from validated input"""
        args = []
        
        # Convert Pydantic model to dict, excluding None values
        data = validated_input.model_dump(exclude_none=True)
        
        for key, value in data.items():
            # Skip certain fields that aren't command arguments
            if key in ["output_format", "duration"]:
                continue
                
            # Convert snake_case to kebab-case for flags
            flag = key.replace("_", "-")
            
            if isinstance(value, bool):
                if value:
                    args.append(f"--{flag}")
            elif value is not None:
                args.extend([f"--{flag}", str(value)])
        
        return args