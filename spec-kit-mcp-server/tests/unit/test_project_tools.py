"""Unit tests for project management tools."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from spec_kit_mcp.tools.project import InitProjectTool, CheckSystemTool
from spec_kit_mcp.models import ToolResponse, AIAssistant
from spec_kit_mcp.exceptions import FileSystemError, ConfigurationError


class TestInitProjectTool:
    """Tests for InitProjectTool."""

    @pytest.mark.asyncio
    async def test_init_project_success(self, mock_settings, temp_dir):
        """Test successful project initialization."""
        tool = InitProjectTool(mock_settings)

        with patch('spec_kit_mcp.tools.project.GitHubClient') as mock_github:
            with patch('spec_kit_mcp.tools.project.GitOperations') as mock_git:
                mock_github_instance = mock_github.return_value
                mock_github_instance.download_template = AsyncMock(return_value=temp_dir)

                mock_git_instance = mock_git.return_value
                mock_git_instance.is_git_repo.return_value = False
                mock_git_instance.init_repository = AsyncMock()
                mock_git_instance.initial_commit = AsyncMock()

                response = await tool.execute(
                    project_name="test-project",
                    ai_assistant="claude",
                    use_current_dir=False,
                    skip_git=False,
                    ignore_agent_tools=True
                )

                assert response.success is True
                assert "test-project" in response.message
                assert response.data["ai_assistant"] == "claude"

    @pytest.mark.asyncio
    async def test_init_project_existing_directory(self, mock_settings, temp_dir):
        """Test initialization fails when directory exists."""
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        tool = InitProjectTool(mock_settings)

        with pytest.raises(FileSystemError) as exc_info:
            await tool.execute(
                project_name="existing-project",
                ai_assistant="claude",
                ignore_agent_tools=True
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_init_project_current_directory(self, mock_settings, temp_dir):
        """Test initialization in current directory."""
        tool = InitProjectTool(mock_settings)

        with patch('spec_kit_mcp.tools.project.GitHubClient') as mock_github:
            with patch('spec_kit_mcp.tools.project.GitOperations') as mock_git:
                with patch('spec_kit_mcp.tools.project.Path.cwd', return_value=temp_dir):
                    mock_github_instance = mock_github.return_value
                    mock_github_instance.download_template = AsyncMock(return_value=temp_dir)

                    mock_git_instance = mock_git.return_value
                    mock_git_instance.is_git_repo.return_value = True

                    response = await tool.execute(
                        use_current_dir=True,
                        ai_assistant="gemini",
                        skip_git=True,
                        ignore_agent_tools=True
                    )

                    assert response.success is True
                    assert response.data["ai_assistant"] == "gemini"
                    assert response.data["git_initialized"] is False

    @pytest.mark.asyncio
    async def test_check_ai_tools(self, mock_settings):
        """Test AI tool checking."""
        tool = InitProjectTool(mock_settings)

        with patch('shutil.which', return_value=None):
            with pytest.raises(ConfigurationError) as exc_info:
                await tool._check_ai_tools(AIAssistant.CLAUDE)

            assert "claude CLI tool not found" in str(exc_info.value)


class TestCheckSystemTool:
    """Tests for CheckSystemTool."""

    @pytest.mark.asyncio
    async def test_check_system_all_tools(self, mock_settings):
        """Test system check with all tools available."""
        tool = CheckSystemTool(mock_settings)

        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda x: True  # All tools available

            with patch('spec_kit_mcp.tools.project.GitOperations') as mock_git:
                mock_git_instance = mock_git.return_value
                mock_git_instance.is_git_repo.return_value = True

                response = await tool.execute()

                assert response.success is True
                assert response.data["tools"]["git"] is True
                assert response.data["tools"]["python"] is True
                assert response.data["ready"] is True

    @pytest.mark.asyncio
    async def test_check_system_missing_tools(self, mock_settings):
        """Test system check with missing tools."""
        tool = CheckSystemTool(mock_settings)

        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                if cmd == "git":
                    return None
                return True

            mock_which.side_effect = which_side_effect

            response = await tool.execute()

            assert response.success is True
            assert response.data["tools"]["git"] is False
            assert response.data["ready"] is False