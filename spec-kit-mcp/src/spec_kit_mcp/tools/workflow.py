"""Workflow tools for spec-kit MCP server."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import BaseTool
from ..models import ToolResponse, FeatureStatus
from ..utils.git_ops import GitOperations
from ..exceptions import GitOperationError
from ..config import Settings

logger = logging.getLogger(__name__)


class GetCurrentBranchTool(BaseTool):
    """Get information about the current feature branch."""

    async def execute(self) -> ToolResponse:
        """Get current branch information."""
        try:
            git_ops = GitOperations(self.settings.repo_path)
            branch = await git_ops.get_current_branch()

            # Get additional branch info
            branch_info = {
                "name": branch,
                "is_feature_branch": self._is_feature_branch(branch),
                "feature_number": self._extract_feature_number(branch),
                "feature_name": self._extract_feature_name(branch)
            }

            # Check for feature directory
            if branch_info["is_feature_branch"]:
                specs_dir = self.settings.repo_path / "specs" / branch
                if specs_dir.exists():
                    branch_info["specs_dir"] = str(specs_dir)
                    branch_info["has_spec"] = (specs_dir / "spec.md").exists()
                    branch_info["has_plan"] = (specs_dir / "plan.md").exists()
                    branch_info["has_tasks"] = (specs_dir / "tasks.md").exists()
                else:
                    branch_info["specs_dir"] = None
                    branch_info["has_spec"] = False
                    branch_info["has_plan"] = False
                    branch_info["has_tasks"] = False

            return self.create_success_response(
                message=f"Current branch: {branch}",
                data=branch_info
            )

        except Exception as e:
            logger.error(f"Failed to get current branch: {e}")
            return self.create_error_response(
                error=str(e),
                suggestions=["Ensure you're in a git repository", "Run 'git init' if needed"]
            )

    def _is_feature_branch(self, branch: str) -> bool:
        """Check if branch is a feature branch."""
        return branch not in ["main", "master", "develop", "staging", "production"]

    def _extract_feature_number(self, branch: str) -> Optional[str]:
        """Extract feature number from branch name."""
        parts = branch.split('-', 1)
        if parts[0].isdigit():
            return parts[0]
        return None

    def _extract_feature_name(self, branch: str) -> str:
        """Extract feature name from branch name."""
        parts = branch.split('-', 1)
        if len(parts) > 1 and parts[0].isdigit():
            return parts[1].replace('-', ' ').title()
        return branch.replace('-', ' ').title()


async def get_current_branch(settings: Settings) -> ToolResponse:
    """Get current branch information."""
    tool = GetCurrentBranchTool(settings)
    return await tool.execute()


class ListFeaturesTool(BaseTool):
    """List all feature branches with their specifications."""

    async def execute(self, status_filter: str = "all") -> ToolResponse:
        """List feature branches with filtering."""
        try:
            git_ops = GitOperations(self.settings.repo_path)

            # Get all branches
            all_branches = await git_ops.list_branches()

            # Filter for feature branches (numbered branches)
            feature_branches = []
            for branch in all_branches:
                if self._is_feature_branch(branch):
                    feature_info = await self._get_feature_info(branch)

                    # Apply status filter
                    if status_filter == "all" or feature_info["status"] == status_filter:
                        feature_branches.append(feature_info)

            # Sort by feature number
            feature_branches.sort(key=lambda x: int(x["number"]) if x["number"] else 999)

            # Create summary
            summary = {
                "total_features": len(feature_branches),
                "by_status": self._count_by_status(feature_branches),
                "filter_applied": status_filter
            }

            return self.create_success_response(
                message=f"Found {len(feature_branches)} feature(s)",
                data={
                    "features": feature_branches,
                    "summary": summary
                }
            )

        except Exception as e:
            logger.error(f"Failed to list features: {e}")
            return self.create_error_response(
                error=str(e),
                suggestions=["Ensure you're in a git repository"]
            )

    def _is_feature_branch(self, branch: str) -> bool:
        """Check if branch is a feature branch."""
        # Feature branches typically start with numbers or are not protected branches
        protected = ["main", "master", "develop", "staging", "production"]
        if branch in protected:
            return False
        # Check if it starts with a number (feature branch pattern)
        parts = branch.split('-', 1)
        return parts[0].isdigit() or branch not in protected

    async def _get_feature_info(self, branch: str) -> Dict[str, Any]:
        """Get information about a feature branch."""
        parts = branch.split('-', 1)
        feature_number = parts[0] if parts[0].isdigit() else None
        feature_name = parts[1].replace('-', ' ').title() if len(parts) > 1 else branch

        # Check for feature files
        specs_dir = self.settings.repo_path / "specs" / branch
        has_spec = False
        has_plan = False
        has_tasks = False
        status = "draft"

        if specs_dir.exists():
            has_spec = (specs_dir / "spec.md").exists()
            has_plan = (specs_dir / "plan.md").exists()
            has_tasks = (specs_dir / "tasks.md").exists()

            # Determine status based on files present
            if has_tasks:
                status = "in_progress"
                # Check if tasks are completed
                tasks_file = specs_dir / "tasks.md"
                if tasks_file.exists():
                    content = tasks_file.read_text()
                    if "[x]" in content:
                        total_tasks = content.count("[ ]") + content.count("[x]") + content.count("[~]") + content.count("[!]")
                        completed_tasks = content.count("[x]")
                        if total_tasks > 0 and completed_tasks == total_tasks:
                            status = "completed"
            elif has_plan:
                status = "planned"
            elif has_spec:
                status = "specified"

        return {
            "branch": branch,
            "number": feature_number,
            "name": feature_name,
            "status": status,
            "has_spec": has_spec,
            "has_plan": has_plan,
            "has_tasks": has_tasks,
            "specs_dir": str(specs_dir) if specs_dir.exists() else None
        }

    def _count_by_status(self, features: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count features by status."""
        counts = {
            "draft": 0,
            "specified": 0,
            "planned": 0,
            "in_progress": 0,
            "completed": 0
        }
        for feature in features:
            status = feature.get("status", "draft")
            if status in counts:
                counts[status] += 1
        return counts


async def list_features(
    status_filter: str = "all",
    settings: Settings = None
) -> ToolResponse:
    """List feature branches."""
    tool = ListFeaturesTool(settings)
    return await tool.execute(status_filter=status_filter)