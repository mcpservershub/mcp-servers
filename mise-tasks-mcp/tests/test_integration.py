"""Integration tests for mise-tasks-mcp server with actual mise commands."""

import pytest
import shutil
from mise_tasks_mcp.server import (
    set_env, get_env, unset_env,
    task_run, task_ls, task_info,
    get_config, current_config,
    self_update, fmt_config
)


# Skip all tests if mise is not installed
pytestmark = pytest.mark.skipif(
    not shutil.which("mise"),
    reason="mise CLI not installed"
)


class TestEnvironmentIntegration:
    """Integration tests for environment tools."""
    
    @pytest.mark.asyncio
    async def test_env_workflow(self):
        """Test complete environment variable workflow."""
        # Set a test variable
        result = await set_env("MISE_TEST_VAR", "test_value_123")
        if result["success"]:
            # Get the variable
            get_result = await get_env("MISE_TEST_VAR")
            assert get_result["success"] is True
            
            # Unset the variable
            unset_result = await unset_env("MISE_TEST_VAR")
            assert unset_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_all_env(self):
        """Test getting all environment variables."""
        result = await get_env()
        # Should at least be able to call it
        assert isinstance(result, dict)
        assert "success" in result


class TestTaskIntegration:
    """Integration tests for task tools."""
    
    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """Test listing tasks."""
        result = await task_ls()
        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "tasks" in result
            assert isinstance(result["tasks"], list)
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_hidden(self):
        """Test listing tasks including hidden ones."""
        result = await task_ls(hidden=True)
        assert isinstance(result, dict)
        assert "success" in result


class TestConfigIntegration:
    """Integration tests for config tools."""
    
    @pytest.mark.asyncio
    async def test_get_config_all(self):
        """Test getting all config."""
        result = await get_config()
        assert isinstance(result, dict)
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_current_config_files(self):
        """Test listing config files."""
        result = await current_config()
        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "config_files" in result
            assert isinstance(result["config_files"], list)


class TestEdgeCasesWithRealCommands:
    """Test edge cases with real mise commands."""
    
    @pytest.mark.asyncio
    async def test_invalid_task_name(self):
        """Test running non-existent task."""
        result = await task_run("nonexistent_task_xyz_123")
        # Should fail gracefully
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_env_var_with_special_chars(self):
        """Test environment variable with special characters in value."""
        # Set variable with spaces and special chars
        result = await set_env("MISE_TEST_SPECIAL", "value with spaces & symbols!")
        if result["success"]:
            # Clean up
            await unset_env("MISE_TEST_SPECIAL")
    
    @pytest.mark.asyncio
    async def test_empty_env_value(self):
        """Test setting empty environment variable."""
        result = await set_env("MISE_TEST_EMPTY", "")
        if result["success"]:
            # Clean up
            await unset_env("MISE_TEST_EMPTY")
    
    @pytest.mark.asyncio
    async def test_very_long_env_value(self):
        """Test environment variable with very long value."""
        long_value = "x" * 1000
        result = await set_env("MISE_TEST_LONG", long_value)
        if result["success"]:
            # Clean up
            await unset_env("MISE_TEST_LONG")