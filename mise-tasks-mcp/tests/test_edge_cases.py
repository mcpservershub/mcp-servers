"""Edge case tests for mise-tasks-mcp server."""

import pytest
from unittest.mock import patch
from mise_tasks_mcp.server import (
    set_env, get_env, unset_env,
    task_run, task_ls, task_info,
    get_config, fmt_config
)
from mise_tasks_mcp.utils.command import CommandResult
from mise_tasks_mcp.utils.validator import (
    validate_env_var_name,
    validate_task_name,
    validate_config_key,
    sanitize_input
)


class TestValidatorEdgeCases:
    """Test edge cases for validators."""
    
    def test_env_var_name_validation(self):
        """Test environment variable name validation edge cases."""
        # Valid cases
        assert validate_env_var_name("PATH") is True
        assert validate_env_var_name("_PRIVATE") is True
        assert validate_env_var_name("VAR_123") is True
        assert validate_env_var_name("__DOUBLE__") is True
        
        # Invalid cases
        assert validate_env_var_name("") is False
        assert validate_env_var_name("123START") is False
        assert validate_env_var_name("VAR-DASH") is False
        assert validate_env_var_name("VAR SPACE") is False
        assert validate_env_var_name("VAR.DOT") is False
        assert validate_env_var_name("VAR$SPECIAL") is False
    
    def test_task_name_validation(self):
        """Test task name validation edge cases."""
        # Valid cases
        assert validate_task_name("build") is True
        assert validate_task_name("test:unit") is True
        assert validate_task_name("deploy-prod") is True
        assert validate_task_name("pre.commit") is True
        assert validate_task_name("task_123") is True
        
        # Invalid cases
        assert validate_task_name("") is False
        assert validate_task_name("task with space") is False
        assert validate_task_name("task$special") is False
        assert validate_task_name("task;injection") is False
    
    def test_config_key_validation(self):
        """Test config key validation edge cases."""
        # Valid cases
        assert validate_config_key("experimental") is True
        assert validate_config_key("legacy_version_file") is True
        assert validate_config_key("node.version") is True
        assert validate_config_key("python-version") is True
        
        # Invalid cases
        assert validate_config_key("") is False
        assert validate_config_key(".startdot") is False
        assert validate_config_key("enddot.") is False
        assert validate_config_key("key..double") is False
        assert validate_config_key("key with space") is False
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test None
        assert sanitize_input(None) == ""
        
        # Test shell special characters
        assert sanitize_input("test`command`") == "test\\`command\\`"
        assert sanitize_input("$VAR") == "\\$VAR"
        assert sanitize_input("cmd && other") == "cmd \\&\\& other"
        assert sanitize_input("cmd | pipe") == "cmd \\| pipe"
        assert sanitize_input("cmd; injection") == "cmd\\; injection"
        
        # Test null bytes
        assert sanitize_input("test\x00null") == "testnull"
        
        # Test quotes
        assert sanitize_input('test "quoted"') == 'test \\"quoted\\"'
        assert sanitize_input("test 'single'") == "test \\'single\\'"


class TestEnvironmentEdgeCases:
    """Edge case tests for environment tools."""
    
    @pytest.mark.asyncio
    async def test_set_env_empty_value(self):
        """Test setting env var with empty value."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="", error="", return_code=0
            )
            
            result = await set_env("EMPTY_VAR", "")
            assert result["success"] is True
            assert result["value"] == ""
    
    @pytest.mark.asyncio
    async def test_set_env_special_chars_in_value(self):
        """Test setting env var with special characters."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="", error="", return_code=0
            )
            
            result = await set_env("VAR", "value with spaces and $pecial")
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_env_nonexistent(self):
        """Test getting non-existent env var."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=False,
                output="",
                error="Environment variable not found",
                return_code=1
            )
            
            result = await get_env("NONEXISTENT")
            assert result["success"] is False
            assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_env_empty_response(self):
        """Test getting env with empty response."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="", error="", return_code=0
            )
            
            result = await get_env()
            assert result["success"] is True
            assert result["variables"] == {}


class TestTaskEdgeCases:
    """Edge case tests for task tools."""
    
    @pytest.mark.asyncio
    async def test_task_run_timeout(self):
        """Test task run with timeout."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=False,
                output="",
                error="Command timed out after 60.0 seconds",
                return_code=-1
            )
            
            result = await task_run("long-running-task")
            assert result["success"] is False
            assert "timed out" in result["error"]
    
    @pytest.mark.asyncio
    async def test_task_run_with_spaces_in_args(self):
        """Test task run with spaces in arguments."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="Done", error="", return_code=0
            )
            
            result = await task_run("test", args='--message "hello world"')
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_task_ls_no_tasks(self):
        """Test listing tasks when none exist."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="", error="", return_code=0
            )
            
            result = await task_ls()
            assert result["success"] is True
            assert result["count"] == 0
            assert result["tasks"] == []
    
    @pytest.mark.asyncio
    async def test_task_info_malformed_output(self):
        """Test task info with malformed output."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True,
                output="Some malformed output without colons",
                error="",
                return_code=0
            )
            
            result = await task_info("test")
            assert result["success"] is True
            assert result["task_info"]["name"] == "test"
            assert "raw_output" in result["task_info"]


class TestConfigEdgeCases:
    """Edge case tests for config tools."""
    
    @pytest.mark.asyncio
    async def test_get_config_invalid_json(self):
        """Test get config with invalid JSON response."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True,
                output="Not valid JSON {broken",
                error="",
                return_code=0
            )
            
            result = await get_config()
            assert result["success"] is True
            assert "raw_config" in result
            assert result["raw_config"] == "Not valid JSON {broken"
    
    @pytest.mark.asyncio
    async def test_get_config_nested_key(self):
        """Test getting nested config key."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True,
                output="value123",
                error="",
                return_code=0
            )
            
            result = await get_config("tools.node.version")
            assert result["success"] is True
            assert result["key"] == "tools.node.version"
            assert result["value"] == "value123"


class TestUtilityEdgeCases:
    """Edge case tests for utility tools."""
    
    @pytest.mark.asyncio
    async def test_fmt_config_no_files(self):
        """Test formatting when no files to format."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True, output="", error="", return_code=0
            )
            
            result = await fmt_config()
            assert result["success"] is True
            assert result["formatted_files"] == []
    
    @pytest.mark.asyncio
    async def test_fmt_config_with_path(self):
        """Test formatting with specific path."""
        with patch('mise_tasks_mcp.server.run_mise_command') as mock:
            mock.return_value = CommandResult(
                success=True,
                output="formatted: /path/to/.mise.toml",
                error="",
                return_code=0
            )
            
            result = await fmt_config("/path/to")
            assert result["success"] is True
            assert len(result["formatted_files"]) == 1


class TestCommandInjectionPrevention:
    """Test prevention of command injection attacks."""
    
    @pytest.mark.asyncio
    async def test_env_injection_attempt(self):
        """Test that env var names prevent injection."""
        # These should fail validation
        result = await set_env("VAR; rm -rf /", "value")
        assert result["success"] is False
        
        result = await set_env("VAR`cmd`", "value")
        assert result["success"] is False
        
        result = await set_env("VAR$(cmd)", "value")
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_task_injection_attempt(self):
        """Test that task names prevent injection."""
        result = await task_run("task; rm -rf /")
        assert result["success"] is False
        
        result = await task_run("task`cmd`")
        assert result["success"] is False
        
        result = await task_run("task$(cmd)")
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_config_injection_attempt(self):
        """Test that config keys prevent injection."""
        result = await get_config("key; cat /etc/passwd")
        assert result["success"] is False
        
        result = await get_config("key`cmd`")
        assert result["success"] is False