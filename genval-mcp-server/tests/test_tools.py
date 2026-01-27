"""
Comprehensive test suite for Genval MCP Server tools.

Tests cover:
- Tool availability and registration
- Parameter validation
- Command construction
- Error handling
- Output formatting
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genval_mcp_server import (
    app,
    artifact_build,
    artifact_pull,
    artifact_push,
    celval_dockerfile,
    celval_infrafile,
    celval_terraform,
    cue_validate_generate,
    cuemod_init,
    dockerfile_generate,
    format_result,
    genai_generate,
    genai_init,
    genval_version,
    regex_validate,
    regoval_dockerfile,
    regoval_infrafile,
    regoval_terraform,
    run_genval_command,
    show_json,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_success_result() -> dict:
    """Mock successful command result."""
    return {
        "success": True,
        "exit_code": 0,
        "stdout": "Command executed successfully",
        "stderr": "",
        "command": "genval test"
    }


@pytest.fixture
def mock_error_result() -> dict:
    """Mock error command result."""
    return {
        "success": False,
        "exit_code": 1,
        "stdout": "",
        "stderr": "Error: Invalid input",
        "command": "genval test"
    }


@pytest.fixture
def mock_process_success():
    """Mock successful subprocess."""
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"Success output", b""))
    return mock_proc


@pytest.fixture
def mock_process_error():
    """Mock failed subprocess."""
    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"Error output"))
    return mock_proc


# =============================================================================
# Test Helper Functions
# =============================================================================

def test_format_result(mock_success_result):
    """Test result formatting."""
    formatted = format_result(mock_success_result)

    assert "Command: genval test" in formatted
    assert "Exit Code: 0" in formatted
    assert "Success: True" in formatted
    assert "Command executed successfully" in formatted


def test_format_result_with_error(mock_error_result):
    """Test error result formatting."""
    formatted = format_result(mock_error_result)

    assert "Command: genval test" in formatted
    assert "Exit Code: 1" in formatted
    assert "Success: False" in formatted
    assert "Error: Invalid input" in formatted


@pytest.mark.asyncio
async def test_run_genval_command_success(mock_process_success):
    """Test successful genval command execution."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        # Mock 'which genval' check
        mock_which = AsyncMock()
        mock_which.returncode = 0
        mock_which.communicate = AsyncMock(return_value=(b"/usr/local/bin/genval", b""))

        # Mock actual genval command
        mock_exec.side_effect = [mock_which, mock_process_success]

        result = await run_genval_command(["version"])

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "Success output" in result["stdout"]


@pytest.mark.asyncio
async def test_run_genval_command_not_found():
    """Test genval command when binary not found."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        # Mock 'which genval' returning not found
        mock_which = AsyncMock()
        mock_which.returncode = 1
        mock_which.communicate = AsyncMock(return_value=(b"", b""))
        mock_exec.return_value = mock_which

        result = await run_genval_command(["version"])

        assert result["success"] is False
        assert "genval executable not found" in result["stderr"]


@pytest.mark.asyncio
async def test_run_genval_command_error(mock_process_error):
    """Test genval command execution with error."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        # Mock 'which genval' check
        mock_which = AsyncMock()
        mock_which.returncode = 0
        mock_which.communicate = AsyncMock(return_value=(b"/usr/local/bin/genval", b""))

        # Mock actual genval command with error
        mock_exec.side_effect = [mock_which, mock_process_error]

        result = await run_genval_command(["invalid-command"])

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "Error output" in result["stderr"]


# =============================================================================
# Test Version Tool
# =============================================================================

@pytest.mark.asyncio
async def test_genval_version():
    """Test version tool."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "genval version v0.7.1",
            "stderr": "",
            "command": "genval version"
        }

        result = await genval_version()

        mock_run.assert_called_once_with(["version"])
        assert "genval version v0.7.1" in result


# =============================================================================
# Test Artifact Tools
# =============================================================================

@pytest.mark.asyncio
async def test_artifact_build_basic():
    """Test basic artifact build."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Artifact created successfully",
            "stderr": "",
            "command": "genval artifact build --reqinput ./input --output ./output.tar.gz"
        }

        result = await artifact_build(
            reqinput="./input",
            output="./output.tar.gz"
        )

        args = mock_run.call_args[0][0]
        assert args == ["artifact", "build", "--reqinput", "./input", "--output", "./output.tar.gz"]
        assert "Artifact created successfully" in result


@pytest.mark.asyncio
async def test_artifact_push_with_signing():
    """Test artifact push with signing."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Artifact pushed and signed",
            "stderr": "",
            "command": "genval artifact push"
        }

        result = await artifact_push(
            reqinput="./policies",
            dest="oci://ghcr.io/test/repo:v1",
            sign=True,
            cosign_key="./cosign.key",
            credentials="user:token",
            annotations=["key1=value1", "key2=value2"]
        )

        args = mock_run.call_args[0][0]
        assert "artifact" in args
        assert "push" in args
        assert "--sign" in args
        assert "--cosign-key" in args
        assert "./cosign.key" in args
        assert "--credentials" in args
        assert "user:token" in args
        assert "--annotations" in args


@pytest.mark.asyncio
async def test_artifact_pull_with_verification():
    """Test artifact pull with verification."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Artifact pulled and verified",
            "stderr": "",
            "command": "genval artifact pull"
        }

        result = await artifact_pull(
            dest="oci://ghcr.io/test/repo:v1",
            path="./output",
            verify=True,
            pub_key="./cosign.pub"
        )

        args = mock_run.call_args[0][0]
        assert "artifact" in args
        assert "pull" in args
        assert "--verify" in args
        assert "--pub-key" in args


# =============================================================================
# Test Dockerfile Tools
# =============================================================================

@pytest.mark.asyncio
async def test_dockerfile_generate_basic():
    """Test basic Dockerfile generation."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Dockerfile generated",
            "stderr": "",
            "command": "genval dockerfile"
        }

        result = await dockerfile_generate(
            reqinput="./input.json",
            output="./Dockerfile"
        )

        args = mock_run.call_args[0][0]
        assert "dockerfile" in args
        assert "--reqinput" in args
        assert "./input.json" in args


@pytest.mark.asyncio
async def test_dockerfile_generate_with_policies():
    """Test Dockerfile generation with policies."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Dockerfile generated and validated",
            "stderr": "",
            "command": "genval dockerfile"
        }

        result = await dockerfile_generate(
            reqinput="./input.json",
            output="./Dockerfile",
            inputpolicy="./input.rego",
            outputpolicy="./output.rego",
            takeaction=True
        )

        args = mock_run.call_args[0][0]
        assert "--inputpolicy" in args
        assert "--outputpolicy" in args
        assert "--takeaction" in args


# =============================================================================
# Test Regoval Tools
# =============================================================================

@pytest.mark.asyncio
async def test_regoval_dockerfile():
    """Test Dockerfile validation with Rego."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Validation successful",
            "stderr": "",
            "command": "genval regoval dockerfileval"
        }

        result = await regoval_dockerfile(
            reqinput="./Dockerfile",
            policy="./policy.rego"
        )

        args = mock_run.call_args[0][0]
        assert "regoval" in args
        assert "dockerfileval" in args
        assert "--reqinput" in args
        assert "--policy" in args


@pytest.mark.asyncio
async def test_regoval_infrafile_with_remediation():
    """Test K8s validation with remediation."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Validation successful, issues remediated",
            "stderr": "",
            "command": "genval regoval infrafile"
        }

        result = await regoval_infrafile(
            reqinput="./deployment.yaml",
            policy="./k8s.rego",
            takeaction=True,
            model="gpt-4",
            output="./fixed.yaml"
        )

        args = mock_run.call_args[0][0]
        assert "regoval" in args
        assert "infrafile" in args
        assert "--takeaction" in args
        assert "--model" in args
        assert "gpt-4" in args


@pytest.mark.asyncio
async def test_regoval_terraform():
    """Test Terraform validation with Rego."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Terraform validation successful",
            "stderr": "",
            "command": "genval regoval terraform"
        }

        result = await regoval_terraform(
            reqinput="./main.tf",
            policy="./terraform.rego"
        )

        args = mock_run.call_args[0][0]
        assert "regoval" in args
        assert "terraform" in args


# =============================================================================
# Test Celval Tools
# =============================================================================

@pytest.mark.asyncio
async def test_celval_dockerfile():
    """Test Dockerfile validation with CEL."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "CEL validation successful",
            "stderr": "",
            "command": "genval celval dockerfileval"
        }

        result = await celval_dockerfile(
            reqinput="./Dockerfile",
            policy="./cel-policies"
        )

        args = mock_run.call_args[0][0]
        assert "celval" in args
        assert "dockerfileval" in args


@pytest.mark.asyncio
async def test_celval_infrafile():
    """Test K8s validation with CEL."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "CEL validation successful",
            "stderr": "",
            "command": "genval celval infrafile"
        }

        result = await celval_infrafile(
            reqinput="./deployment.yaml",
            policy="./k8s_cel.yaml"
        )

        args = mock_run.call_args[0][0]
        assert "celval" in args
        assert "infrafile" in args


@pytest.mark.asyncio
async def test_celval_terraform():
    """Test Terraform validation with CEL."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "CEL validation successful",
            "stderr": "",
            "command": "genval celval terraform"
        }

        result = await celval_terraform(
            reqinput="./main.tf",
            policy="./terraform_cel.yaml"
        )

        args = mock_run.call_args[0][0]
        assert "celval" in args
        assert "terraform" in args


# =============================================================================
# Test Cue Tools
# =============================================================================

@pytest.mark.asyncio
async def test_cue_validate_generate():
    """Test Cue validation and generation."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Manifests generated successfully",
            "stderr": "",
            "command": "genval cue"
        }

        result = await cue_validate_generate(
            reqinput="./app.yaml",
            resource="Application",
            policy="./policy",
            output="./output",
            verbose=True
        )

        args = mock_run.call_args[0][0]
        assert "cue" in args
        assert "--reqinput" in args
        assert "--resource" in args
        assert "Application" in args
        assert "--policy" in args
        assert "--output" in args
        assert "--verbose" in args


@pytest.mark.asyncio
async def test_cuemod_init():
    """Test cuemod initialization."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Workspace initialized",
            "stderr": "",
            "command": "genval cuemod init"
        }

        result = await cuemod_init(
            tool="k8s:latest",
            credentials="user:token"
        )

        args = mock_run.call_args[0][0]
        assert "cuemod" in args
        assert "init" in args
        assert "--tool" in args
        assert "k8s:latest" in args
        assert "--credentials" in args


# =============================================================================
# Test Regex Validation
# =============================================================================

@pytest.mark.asyncio
async def test_regex_validate():
    """Test regex validation."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Regex validation passed",
            "stderr": "",
            "command": "genval regex"
        }

        result = await regex_validate(
            reqinput="./config.json",
            policy="./regex_policy.yaml"
        )

        args = mock_run.call_args[0][0]
        assert "regex" in args
        assert "--reqinput" in args
        assert "--policy" in args


# =============================================================================
# Test GenAI Tools
# =============================================================================

@pytest.mark.asyncio
async def test_genai_generate():
    """Test AI generation."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "IaC generated successfully",
            "stderr": "",
            "command": "genval genai"
        }

        result = await genai_generate(
            prompt="Create a secure K8s deployment",
            model="GPT4",
            output="./deployment.yaml",
            endpoint="https://api.openai.com",
            assistant="security",
            config="./config.yaml"
        )

        args = mock_run.call_args[0][0]
        assert "genai" in args
        assert "--prompt" in args
        assert "--model" in args
        assert "GPT4" in args
        assert "--output" in args
        assert "--endpoint" in args
        assert "--assistant" in args
        assert "--config" in args


@pytest.mark.asyncio
async def test_genai_init():
    """Test GenAI initialization."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "GenAI initialized",
            "stderr": "",
            "command": "genval genai init"
        }

        result = await genai_init()

        args = mock_run.call_args[0][0]
        assert args == ["genai", "init"]


# =============================================================================
# Test Utility Tools
# =============================================================================

@pytest.mark.asyncio
async def test_show_json():
    """Test showJSON utility."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": '{"key": "value"}',
            "stderr": "",
            "command": "genval showJSON"
        }

        result = await show_json(reqinput="./Dockerfile")

        args = mock_run.call_args[0][0]
        assert "showJSON" in args
        assert "--reqinput" in args


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_tools_workflow():
    """Test a complete workflow using multiple tools."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        # Mock responses for different commands
        def mock_command_response(args):
            if args[0] == "version":
                return {
                    "success": True,
                    "exit_code": 0,
                    "stdout": "genval v0.7.1",
                    "stderr": "",
                    "command": "genval version"
                }
            elif args[0] == "dockerfile":
                return {
                    "success": True,
                    "exit_code": 0,
                    "stdout": "Dockerfile generated",
                    "stderr": "",
                    "command": "genval dockerfile"
                }
            elif args[0] == "regoval":
                return {
                    "success": True,
                    "exit_code": 0,
                    "stdout": "Validation passed",
                    "stderr": "",
                    "command": "genval regoval"
                }

        mock_run.side_effect = mock_command_response

        # Step 1: Check version
        version_result = await genval_version()
        assert "genval v0.7.1" in version_result

        # Step 2: Generate Dockerfile
        dockerfile_result = await dockerfile_generate(
            reqinput="./input.json",
            output="./Dockerfile"
        )
        assert "Dockerfile generated" in dockerfile_result

        # Step 3: Validate Dockerfile
        validate_result = await regoval_dockerfile(
            reqinput="./Dockerfile",
            policy="./policy.rego"
        )
        assert "Validation passed" in validate_result


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_command_failure_handling():
    """Test handling of command failures."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": "Error: File not found",
            "command": "genval dockerfile"
        }

        result = await dockerfile_generate(
            reqinput="./nonexistent.json",
            output="./Dockerfile"
        )

        assert "Error: File not found" in result
        assert "Success: False" in result


@pytest.mark.asyncio
async def test_exception_handling():
    """Test handling of exceptions during command execution."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.side_effect = Exception("Unexpected error")

        # Should handle exception gracefully
        with pytest.raises(Exception):
            await genval_version()


# =============================================================================
# Parameter Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_required_parameters():
    """Test that required parameters are enforced."""
    with pytest.raises(TypeError):
        # Missing required parameters should raise TypeError
        await artifact_build()  # type: ignore


@pytest.mark.asyncio
async def test_optional_parameters():
    """Test that optional parameters work correctly."""
    with patch("genval_mcp_server.run_genval_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "exit_code": 0,
            "stdout": "Success",
            "stderr": "",
            "command": "genval artifact build"
        }

        # Should work with only required parameters
        result = await artifact_build(reqinput="./input")

        args = mock_run.call_args[0][0]
        assert "artifact" in args
        assert "build" in args


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
