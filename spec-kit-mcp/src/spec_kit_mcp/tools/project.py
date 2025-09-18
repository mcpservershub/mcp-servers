"""Project management tools for spec-kit MCP server."""

import asyncio
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .base import BaseTool
from ..models import ToolResponse, InitProjectRequest, AIAssistant
from ..exceptions import ConfigurationError, NetworkError, FileSystemError
from ..utils.github import GitHubClient
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class InitProjectTool(BaseTool):
    """Initialize a new spec-kit project."""

    async def execute(
        self,
        project_name: Optional[str] = None,
        ai_assistant: str = "claude",
        use_current_dir: bool = False,
        skip_git: bool = False,
        ignore_agent_tools: bool = False
    ) -> ToolResponse:
        """Execute project initialization."""
        # Validate inputs
        request = InitProjectRequest(
            project_name=project_name,
            ai_assistant=AIAssistant(ai_assistant),
            use_current_dir=use_current_dir,
            skip_git=skip_git,
            ignore_agent_tools=ignore_agent_tools
        )

        # Check prerequisites
        if not ignore_agent_tools:
            await self._check_ai_tools(request.ai_assistant)

        # Determine project path
        if use_current_dir:
            project_path = Path.cwd()
            logger.info(f"Initializing in current directory: {project_path}")
        else:
            project_path = Path.cwd() / project_name
            if project_path.exists():
                raise FileSystemError(
                    f"Directory {project_name} already exists",
                    suggestions=["Choose a different name", "Use --use-current-dir flag"]
                )
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")

        try:
            # Download templates from GitHub
            github_client = GitHubClient(self.settings)
            await github_client.download_template(
                ai_assistant=request.ai_assistant.value,
                target_dir=project_path
            )

            # Ensure .specify directory exists
            specify_dir = project_path / ".specify"
            specify_dir.mkdir(exist_ok=True)

            # Initialize git repository if needed
            git_initialized = False
            if not skip_git:
                git_ops = GitOperations(project_path)
                if not git_ops.is_git_repo():
                    await git_ops.init_repository()
                    await git_ops.initial_commit("Initial commit from spec-kit MCP")
                    git_initialized = True
                else:
                    logger.info("Git repository already exists")

            # Set up AI-specific configurations
            await self._setup_ai_config(project_path, request.ai_assistant)

            # Make scripts executable (Unix-like systems)
            await self._make_scripts_executable(project_path)

            return self.create_success_response(
                message=f"Successfully initialized spec-kit project at {project_path}",
                data={
                    "project_path": str(project_path),
                    "ai_assistant": request.ai_assistant.value,
                    "git_initialized": git_initialized,
                    "specify_dir": str(specify_dir)
                },
                artifacts=[project_path]
            )

        except Exception as e:
            # Clean up on failure (only if we created the directory)
            if not use_current_dir and project_path.exists():
                shutil.rmtree(project_path, ignore_errors=True)
            raise

    async def _check_ai_tools(self, ai_assistant: AIAssistant) -> None:
        """Check if required AI tools are installed."""
        tool_checks = {
            AIAssistant.CLAUDE: "claude",
            AIAssistant.GEMINI: "gemini",
            AIAssistant.COPILOT: None  # Copilot doesn't need CLI tool
        }

        tool_name = tool_checks.get(ai_assistant)
        if tool_name and not shutil.which(tool_name):
            raise ConfigurationError(
                f"{ai_assistant.value} CLI tool not found",
                details={"tool": tool_name},
                suggestions=[
                    f"Install {tool_name} CLI",
                    "Use --ignore-agent-tools flag to skip this check"
                ]
            )

    async def _setup_ai_config(self, project_path: Path, ai_assistant: AIAssistant) -> None:
        """Set up AI-specific configuration files."""
        config_paths = {
            AIAssistant.CLAUDE: project_path / ".claude" / "commands",
            AIAssistant.GEMINI: project_path / ".gemini" / "commands",
            AIAssistant.COPILOT: project_path / ".github" / "prompts"
        }

        config_path = config_paths.get(ai_assistant)
        if config_path:
            config_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created AI config directory: {config_path}")

    async def _make_scripts_executable(self, project_path: Path) -> None:
        """Make shell scripts executable on Unix-like systems."""
        import os
        import stat

        scripts_dir = project_path / ".specify" / "scripts"
        if not scripts_dir.exists():
            return

        for script_file in scripts_dir.glob("*.sh"):
            try:
                st = os.stat(script_file)
                os.chmod(script_file, st.st_mode | stat.S_IEXEC)
                logger.info(f"Made executable: {script_file.name}")
            except Exception as e:
                logger.warning(f"Could not make {script_file.name} executable: {e}")


class CheckSystemTool(BaseTool):
    """Check system requirements."""

    async def execute(self) -> ToolResponse:
        """Check system requirements and installed tools."""
        results = {
            "git": shutil.which("git") is not None,
            "claude": shutil.which("claude") is not None,
            "gemini": shutil.which("gemini") is not None,
            "python": shutil.which("python") is not None or shutil.which("python3") is not None,
            "uv": shutil.which("uv") is not None,
        }

        # Check repository status
        repo_status = {
            "repo_path": str(self.settings.repo_path),
            "repo_exists": self.settings.repo_path.exists(),
            "is_git_repo": False,
            "templates_available": False,
            "scripts_available": False,
        }

        if repo_status["repo_exists"]:
            git_ops = GitOperations(self.settings.repo_path)
            repo_status["is_git_repo"] = git_ops.is_git_repo()

            if self.settings.templates_path:
                repo_status["templates_available"] = self.settings.templates_path.exists()

            if self.settings.scripts_path:
                repo_status["scripts_available"] = self.settings.scripts_path.exists()

        # Check GitHub connectivity
        github_status = {
            "github_token_set": bool(self.settings.github_token),
            "rate_limit": None
        }

        if self.settings.github_token:
            try:
                github_client = GitHubClient(self.settings)
                github_status["rate_limit"] = await github_client.check_rate_limit()
            except Exception as e:
                logger.warning(f"Could not check GitHub rate limit: {e}")

        all_tools_available = all([
            results["git"],
            results["python"],
            any([results["claude"], results["gemini"]])  # At least one AI tool
        ])

        return self.create_success_response(
            message="System check complete",
            data={
                "tools": results,
                "repository": repo_status,
                "github": github_status,
                "ready": all_tools_available
            }
        )


# Export tool functions for server registration
async def init_project(
    project_name: Optional[str] = None,
    ai_assistant: str = "claude",
    use_current_dir: bool = False,
    skip_git: bool = False,
    ignore_agent_tools: bool = False,
    settings: Settings = None
) -> ToolResponse:
    """Initialize a new spec-kit project."""
    tool = InitProjectTool(settings)
    return await tool.execute(
        project_name=project_name,
        ai_assistant=ai_assistant,
        use_current_dir=use_current_dir,
        skip_git=skip_git,
        ignore_agent_tools=ignore_agent_tools
    )


async def check_system(settings: Settings) -> ToolResponse:
    """Check system requirements."""
    tool = CheckSystemTool(settings)
    return await tool.execute()