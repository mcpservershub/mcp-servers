"""Base class for all spec-kit tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import asyncio
from pathlib import Path

from ..models import ToolResponse, ErrorResponse
from ..exceptions import SpecKitError, ValidationError
from ..config import Settings


class BaseTool(ABC):
    """Base class for all spec-kit tools."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResponse:
        """Execute the tool operation."""
        pass

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        # Default implementation - override in subclasses
        return kwargs

    async def check_prerequisites(self) -> None:
        """Check if prerequisites are met."""
        # Default implementation - override in subclasses
        pass

    def validate_path(self, path: Path, must_exist: bool = False) -> Path:
        """Validate that path is within allowed boundaries."""
        try:
            resolved_path = path.resolve()
        except Exception as e:
            raise ValidationError(
                f"Invalid path: {path}",
                details={"path": str(path), "error": str(e)}
            )

        if self.settings.restrict_to_repo:
            try:
                resolved_path.relative_to(self.settings.repo_path.resolve())
            except ValueError:
                raise ValidationError(
                    f"Path {path} is outside repository boundary",
                    details={"path": str(path), "repo": str(self.settings.repo_path)},
                    suggestions=["Use a path within the repository"]
                )

        if must_exist and not resolved_path.exists():
            raise ValidationError(
                f"Path does not exist: {path}",
                details={"path": str(path)},
                suggestions=["Check the path and try again"]
            )

        return resolved_path

    async def run_with_timeout(self, coro, timeout: Optional[int] = None):
        """Run coroutine with timeout."""
        timeout = timeout or self.settings.script_timeout
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise SpecKitError(
                f"Operation timed out after {timeout} seconds",
                suggestions=["Increase timeout in settings", "Check for hanging operations"]
            )

    def get_feature_dir(self, branch_name: Optional[str] = None) -> Path:
        """Get the feature directory for a branch."""
        if not branch_name:
            # Get current branch
            from ..utils.git_ops import GitOperations
            git_ops = GitOperations(self.settings.repo_path)
            branch_name = asyncio.run(git_ops.get_current_branch())

        specs_dir = self.settings.repo_path / "specs"
        feature_dir = specs_dir / branch_name

        return feature_dir

    def get_spec_file(self, branch_name: Optional[str] = None) -> Path:
        """Get the specification file path."""
        feature_dir = self.get_feature_dir(branch_name)
        return feature_dir / "spec.md"

    def get_plan_file(self, branch_name: Optional[str] = None) -> Path:
        """Get the plan file path."""
        feature_dir = self.get_feature_dir(branch_name)
        return feature_dir / "plan.md"

    def get_tasks_file(self, branch_name: Optional[str] = None) -> Path:
        """Get the tasks file path."""
        feature_dir = self.get_feature_dir(branch_name)
        return feature_dir / "tasks.md"

    def create_success_response(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Path]] = None
    ) -> ToolResponse:
        """Create a success response."""
        return ToolResponse(
            success=True,
            message=message,
            data=data or {},
            artifacts=[str(a) for a in (artifacts or [])]
        )

    def create_error_response(
        self,
        message: str,
        error_type: str = "ToolError",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ) -> ErrorResponse:
        """Create an error response."""
        return ErrorResponse(
            error_type=error_type,
            message=message,
            details=details or {},
            suggestions=suggestions or []
        )