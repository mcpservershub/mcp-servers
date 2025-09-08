"""Tests for mise-tasks-mcp server tools."""

import pytest
from unittest.mock import patch, AsyncMock
from mise_tasks_mcp.server import (
    set_env, get_env, unset_env,
    task_run, task_ls, task_info, task_edit, task_deps,
    get_config, current_config,
    self_update, fmt_config
)
from mise_tasks_mcp.utils.command import CommandResult


@pytest.fixture
def mock_run_mise_command():
    """Mock the run_mise_command function."""
    with patch('mise_tasks_mcp.server.run_mise_command') as mock:
        yield mock


class TestEnvironmentTools:
    """Tests for environment management tools."""
    
    @pytest.mark.asyncio
    async def test_set_env(self, mock_run_mise_command):
        """Test setting an environment variable."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Environment variable set",
            error="",
            return_code=0
        )
        
        result = await set_env("TEST_VAR", "test_value")
        
        assert result["success"] is True
        assert result["key"] == "TEST_VAR"
        assert result["value"] == "test_value"
        mock_run_mise_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_env_invalid_name(self):
        """Test setting env var with invalid name."""
        result = await set_env("123-invalid", "value")
        
        assert result["success"] is False
        assert "Invalid environment variable name" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_env_single(self, mock_run_mise_command):
        """Test getting a single environment variable."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="test_value",
            error="",
            return_code=0
        )
        
        result = await get_env("TEST_VAR")
        
        assert result["success"] is True
        assert result["key"] == "TEST_VAR"
        assert result["value"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_env_all(self, mock_run_mise_command):
        """Test getting all environment variables."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="VAR1=value1\nVAR2=value2",
            error="",
            return_code=0
        )
        
        result = await get_env()
        
        assert result["success"] is True
        assert result["variables"] == {"VAR1": "value1", "VAR2": "value2"}
    
    @pytest.mark.asyncio
    async def test_unset_env(self, mock_run_mise_command):
        """Test unsetting an environment variable."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Environment variable unset",
            error="",
            return_code=0
        )
        
        result = await unset_env("TEST_VAR")
        
        assert result["success"] is True
        assert result["key"] == "TEST_VAR"
        mock_run_mise_command.assert_called_once()


class TestTaskTools:
    """Tests for task management tools."""
    
    @pytest.mark.asyncio
    async def test_task_run(self, mock_run_mise_command):
        """Test running a task."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Task completed successfully",
            error="",
            return_code=0
        )
        
        result = await task_run("build")
        
        assert result["success"] is True
        assert result["task"] == "build"
        assert "completed successfully" in result["output"]
    
    @pytest.mark.asyncio
    async def test_task_run_with_args(self, mock_run_mise_command):
        """Test running a task with arguments."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Test passed",
            error="",
            return_code=0
        )
        
        result = await task_run("test", args="--verbose --coverage")
        
        assert result["success"] is True
        assert result["task"] == "test"
        mock_run_mise_command.assert_called_once()
        # Check that args were passed
        call_args = mock_run_mise_command.call_args[0]
        assert "--verbose" in call_args[1]
        assert "--coverage" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_task_ls(self, mock_run_mise_command):
        """Test listing tasks."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="build Build the project\ntest Run tests\nlint Run linter",
            error="",
            return_code=0
        )
        
        result = await task_ls()
        
        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["name"] == "build"
    
    @pytest.mark.asyncio
    async def test_task_info(self, mock_run_mise_command):
        """Test getting task info."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Name: build\nDescription: Build project\nCommand: npm run build",
            error="",
            return_code=0
        )
        
        result = await task_info("build")
        
        assert result["success"] is True
        assert result["task_info"]["name"] == "build"
        assert "description" in result["task_info"]
    
    @pytest.mark.asyncio
    async def test_task_edit(self, mock_run_mise_command):
        """Test editing a task."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="",
            error="",
            return_code=0
        )
        
        result = await task_edit("build")
        
        assert result["success"] is True
        assert result["task"] == "build"
        assert result["message"] == "Task opened for editing"
    
    @pytest.mark.asyncio
    async def test_task_deps(self, mock_run_mise_command):
        """Test getting task dependencies."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="install\ncompile\ntest",
            error="",
            return_code=0
        )
        
        result = await task_deps("build")
        
        assert result["success"] is True
        assert result["task"] == "build"
        assert result["count"] == 3
        assert "install" in result["dependencies"]


class TestConfigTools:
    """Tests for configuration tools."""
    
    @pytest.mark.asyncio
    async def test_get_config_key(self, mock_run_mise_command):
        """Test getting a specific config value."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="true",
            error="",
            return_code=0
        )
        
        result = await get_config("experimental")
        
        assert result["success"] is True
        assert result["key"] == "experimental"
        assert result["value"] == "true"
    
    @pytest.mark.asyncio
    async def test_get_config_all(self, mock_run_mise_command):
        """Test getting all config."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output='{"experimental": true, "legacy_version_file": false}',
            error="",
            return_code=0
        )
        
        result = await get_config()
        
        assert result["success"] is True
        assert result["config"]["experimental"] is True
        assert result["config"]["legacy_version_file"] is False
    
    @pytest.mark.asyncio
    async def test_current_config(self, mock_run_mise_command):
        """Test getting current config sources."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="/home/user/.config/mise/config.toml\n/home/user/project/.mise.toml",
            error="",
            return_code=0
        )
        
        result = await current_config()
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["config_files"]) == 2


class TestUtilityTools:
    """Tests for utility tools."""
    
    @pytest.mark.asyncio
    async def test_self_update(self, mock_run_mise_command):
        """Test self-update."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Updated to version 2024.1.0",
            error="",
            return_code=0
        )
        
        result = await self_update()
        
        assert result["success"] is True
        assert "Updated to version" in result["output"]
    
    @pytest.mark.asyncio
    async def test_self_update_with_version(self, mock_run_mise_command):
        """Test self-update to specific version."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output="Updated to version 2023.12.0",
            error="",
            return_code=0
        )
        
        result = await self_update(version="2023.12.0", force=True)
        
        assert result["success"] is True
        mock_run_mise_command.assert_called_once()
        # Check that version and force were passed
        call_args = mock_run_mise_command.call_args[0]
        assert "2023.12.0" in call_args[1]
        assert "--force" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_fmt_config(self, mock_run_mise_command):
        """Test formatting config files."""
        mock_run_mise_command.return_value = CommandResult(
            success=True,
            output=".mise.toml\n.mise.local.toml",
            error="",
            return_code=0
        )
        
        result = await fmt_config()
        
        assert result["success"] is True
        assert len(result["formatted_files"]) == 2
        assert ".mise.toml" in result["formatted_files"]