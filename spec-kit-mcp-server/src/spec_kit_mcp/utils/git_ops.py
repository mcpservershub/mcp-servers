"""Git operations using GitPython."""

import git
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import re
import logging

from ..exceptions import GitOperationError

logger = logging.getLogger(__name__)


class GitOperations:
    """Handle git operations using GitPython."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._repo = None

    @property
    def repo(self) -> git.Repo:
        """Get or initialize git repository."""
        if not self._repo:
            try:
                self._repo = git.Repo(self.repo_path)
            except git.InvalidGitRepositoryError:
                raise GitOperationError(
                    f"Not a git repository: {self.repo_path}",
                    suggestions=["Initialize with git init", "Check repository path"]
                )
        return self._repo

    async def init_repository(self) -> None:
        """Initialize a new git repository."""
        try:
            self._repo = git.Repo.init(self.repo_path)
            logger.info(f"Initialized git repository at {self.repo_path}")
        except Exception as e:
            raise GitOperationError(
                f"Failed to initialize git repository",
                details={"error": str(e), "path": str(self.repo_path)}
            )

    async def create_branch(self, branch_name: str) -> str:
        """Create and checkout a new branch."""
        # Validate branch name format (###-feature-name)
        if not re.match(r'^\d{3}-[a-z0-9-]+$', branch_name):
            raise GitOperationError(
                f"Invalid branch name format: {branch_name}",
                details={"expected_format": "###-feature-name"},
                suggestions=["Use format like '001-my-feature'"]
            )

        try:
            # Check if branch already exists
            if branch_name in [b.name for b in self.repo.branches]:
                raise GitOperationError(
                    f"Branch already exists: {branch_name}",
                    suggestions=["Use a different branch name", "Checkout existing branch"]
                )

            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            logger.info(f"Created and checked out branch: {branch_name}")
            return branch_name
        except GitOperationError:
            raise
        except Exception as e:
            raise GitOperationError(
                f"Failed to create branch {branch_name}",
                details={"error": str(e)}
            )

    async def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            return "HEAD"

    async def initial_commit(self, message: str) -> None:
        """Create initial commit."""
        try:
            # Add all files
            self.repo.index.add("*")
            # Commit
            self.repo.index.commit(message)
            logger.info(f"Created initial commit: {message}")
        except Exception as e:
            raise GitOperationError(
                f"Failed to create initial commit",
                details={"error": str(e)}
            )

    async def commit_changes(self, message: str, files: Optional[List[str]] = None) -> None:
        """Commit changes to repository."""
        try:
            if files:
                self.repo.index.add(files)
            else:
                self.repo.index.add("*")

            if self.repo.index.diff("HEAD"):
                self.repo.index.commit(message)
                logger.info(f"Committed changes: {message}")
            else:
                logger.info("No changes to commit")
        except Exception as e:
            raise GitOperationError(
                f"Failed to commit changes",
                details={"error": str(e)}
            )

    async def get_status(self) -> Dict[str, List[str]]:
        """Get repository status."""
        try:
            status = {
                "modified": [item.a_path for item in self.repo.index.diff(None)],
                "staged": [item.a_path for item in self.repo.index.diff("HEAD")],
                "untracked": self.repo.untracked_files
            }
            return status
        except Exception as e:
            raise GitOperationError(
                f"Failed to get repository status",
                details={"error": str(e)}
            )

    async def list_branches(self) -> List[str]:
        """List all branches."""
        try:
            return [branch.name for branch in self.repo.branches]
        except Exception as e:
            raise GitOperationError(
                f"Failed to list branches",
                details={"error": str(e)}
            )

    async def checkout_branch(self, branch_name: str) -> None:
        """Checkout an existing branch."""
        try:
            self.repo.git.checkout(branch_name)
            logger.info(f"Checked out branch: {branch_name}")
        except Exception as e:
            raise GitOperationError(
                f"Failed to checkout branch {branch_name}",
                details={"error": str(e)},
                suggestions=["Check if branch exists", "Use list_branches to see available branches"]
            )

    async def get_feature_branches(self) -> List[Tuple[str, int]]:
        """Get all feature branches with their numbers."""
        branches = await self.list_branches()
        feature_branches = []

        for branch in branches:
            match = re.match(r'^(\d{3})-(.+)$', branch)
            if match:
                number = int(match.group(1))
                feature_branches.append((branch, number))

        return sorted(feature_branches, key=lambda x: x[1])

    async def get_next_feature_number(self) -> int:
        """Get the next available feature number."""
        feature_branches = await self.get_feature_branches()
        if feature_branches:
            return feature_branches[-1][1] + 1
        return 1

    def is_git_repo(self) -> bool:
        """Check if the path is a git repository."""
        try:
            git.Repo(self.repo_path)
            return True
        except git.InvalidGitRepositoryError:
            return False