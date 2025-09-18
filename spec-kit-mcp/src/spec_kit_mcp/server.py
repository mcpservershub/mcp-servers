"""Main MCP server implementation using FastMCP."""

from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import logging
import asyncio
import functools
from pathlib import Path

from spec_kit_mcp.config import settings
from spec_kit_mcp.models import (
    ToolResponse,
    ErrorResponse,
    AIAssistant,
    ProjectType,
    TaskStatus,
    ConstitutionCheckType,
    FeatureStatus,
    DocumentFormat,
    ContractType,
)
from spec_kit_mcp.exceptions import SpecKitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("spec-kit-mcp")
mcp.description = "MCP Server for spec-kit - Spec-Driven Development workflows"


def handle_errors(func):
    """Decorator for consistent error handling across all tools."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            logger.info(f"Executing tool: {func.__name__}")
            result = await func(*args, **kwargs)
            logger.info(f"Tool {func.__name__} completed successfully")
            return result
        except SpecKitError as e:
            logger.error(f"SpecKit error in {func.__name__}: {e}")
            return ErrorResponse(
                error_type=e.__class__.__name__,
                message=str(e),
                details=e.details,
                suggestions=e.suggestions
            ).model_dump()
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return ErrorResponse(
                error_type="InternalError",
                message="An unexpected error occurred",
                details={"error": str(e), "tool": func.__name__}
            ).model_dump()

    return wrapper


# Import tool implementations (we'll create these next)
from spec_kit_mcp.tools import project, specification, planning, tasks, constitution, context, workflow, documentation


# ============================================================================
# Project Management Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_init(
    project_name: Optional[str] = None,
    ai_assistant: str = "claude",
    use_current_dir: bool = False,
    skip_git: bool = False,
    ignore_agent_tools: bool = False
) -> Dict[str, Any]:
    """
    Initialize a new Spec-Kit project with templates and structure.

    Args:
        project_name: Name for the project directory (required unless use_current_dir is True)
        ai_assistant: AI assistant to configure for (claude, gemini, or copilot)
        use_current_dir: Initialize in current directory instead of creating new one
        skip_git: Skip git repository initialization
        ignore_agent_tools: Skip checks for AI agent tools

    Returns:
        ToolResponse with project initialization details
    """
    return (await project.init_project(
        project_name=project_name,
        ai_assistant=ai_assistant,
        use_current_dir=use_current_dir,
        skip_git=skip_git,
        ignore_agent_tools=ignore_agent_tools,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_check() -> Dict[str, Any]:
    """
    Check for required tools and system compatibility.

    Returns:
        ToolResponse with system check results
    """
    return (await project.check_system(settings=settings)).model_dump()


# ============================================================================
# Specification Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_specify(
    feature_description: str,
    mark_clarifications: bool = True
) -> Dict[str, Any]:
    """
    Create a new feature specification and branch.

    Args:
        feature_description: Natural language description of the feature
        mark_clarifications: Mark ambiguities with [NEEDS CLARIFICATION]

    Returns:
        ToolResponse with specification creation details
    """
    return (await specification.create_specification(
        feature_description=feature_description,
        mark_clarifications=mark_clarifications,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_validate_spec(spec_path: str) -> Dict[str, Any]:
    """
    Validate a specification against the review checklist.

    Args:
        spec_path: Path to spec.md file to validate

    Returns:
        ToolResponse with validation results
    """
    return (await specification.validate_specification(
        spec_path=spec_path,
        settings=settings
    )).model_dump()


# ============================================================================
# Planning Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_plan(
    tech_stack: str,
    language: str,
    framework: str,
    storage: Optional[str] = None,
    project_type: str = "single"
) -> Dict[str, Any]:
    """
    Create technical implementation plan from feature specification.

    Args:
        tech_stack: Technology stack and architecture choices
        language: Primary programming language
        framework: Primary framework
        storage: Database/storage solution (optional)
        project_type: Project structure type (single, web, or mobile)

    Returns:
        ToolResponse with plan generation details
    """
    return (await planning.create_plan(
        tech_stack=tech_stack,
        language=language,
        framework=framework,
        storage=storage,
        project_type=project_type,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_research(
    topics: List[str],
    context: str
) -> Dict[str, Any]:
    """
    Research technical decisions and best practices.

    Args:
        topics: List of topics to research
        context: Feature context for research

    Returns:
        ToolResponse with research results
    """
    return (await planning.conduct_research(
        topics=topics,
        context=context,
        settings=settings
    )).model_dump()


# ============================================================================
# Task Management Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_generate_tasks(
    include_parallel_markers: bool = True,
    enforce_tdd: bool = True
) -> Dict[str, Any]:
    """
    Break down implementation plan into numbered, executable tasks.

    Args:
        include_parallel_markers: Mark tasks that can run in parallel with [P]
        enforce_tdd: Enforce test-driven development order

    Returns:
        ToolResponse with generated tasks
    """
    return (await tasks.generate_tasks(
        include_parallel_markers=include_parallel_markers,
        enforce_tdd=enforce_tdd,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_task_status(
    task_id: str,
    status: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get or update task completion status.

    Args:
        task_id: Task identifier (e.g., T001)
        status: New status to set (pending, in_progress, completed, blocked)
        notes: Additional notes about the task

    Returns:
        ToolResponse with task status information
    """
    return (await tasks.update_task_status(
        task_id=task_id,
        status=status,
        notes=notes,
        settings=settings
    )).model_dump()


# ============================================================================
# Constitution & Compliance Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_check_constitution(
    check_type: str,
    artifact_path: str
) -> Dict[str, Any]:
    """
    Check plan/implementation against constitutional requirements.

    Args:
        check_type: Type of check (simplicity, architecture, testing, observability, versioning)
        artifact_path: Path to artifact to check

    Returns:
        ToolResponse with constitution check results
    """
    return (await constitution.check_constitution(
        check_type=check_type,
        artifact_path=artifact_path,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_complexity_tracking(
    violation: str,
    justification: str,
    alternatives_rejected: str
) -> Dict[str, Any]:
    """
    Track and justify necessary complexity violations.

    Args:
        violation: Description of the violation
        justification: Why the complexity is needed
        alternatives_rejected: Why simpler alternatives won't work

    Returns:
        ToolResponse with complexity tracking details
    """
    return (await constitution.track_complexity(
        violation=violation,
        justification=justification,
        alternatives_rejected=alternatives_rejected,
        settings=settings
    )).model_dump()


# ============================================================================
# Context Management Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_update_context(
    agent_type: str,
    technologies: Optional[Dict[str, str]] = None,
    recent_changes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update agent-specific context files with new technology stack.

    Args:
        agent_type: Which agent context to update (claude, gemini, or copilot)
        technologies: New technologies to add
        recent_changes: Recent feature changes

    Returns:
        ToolResponse with context update details
    """
    return (await context.update_agent_context(
        agent_type=agent_type,
        technologies=technologies or {},
        recent_changes=recent_changes or [],
        settings=settings
    )).model_dump()


# ============================================================================
# Workflow Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_current_branch() -> Dict[str, Any]:
    """
    Get information about the current feature branch.

    Returns:
        ToolResponse with current branch information
    """
    return (await workflow.get_current_branch(settings=settings)).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_list_features(
    status_filter: str = "all"
) -> Dict[str, Any]:
    """
    List all feature branches with their specifications.

    Args:
        status_filter: Filter by status (all, draft, planned, in_progress, completed)

    Returns:
        ToolResponse with list of features
    """
    return (await workflow.list_features(
        status_filter=status_filter,
        settings=settings
    )).model_dump()


# ============================================================================
# Documentation Tools
# ============================================================================

@mcp.tool()
@handle_errors
async def spec_kit_generate_quickstart(
    include_test_scenarios: bool = True,
    format: str = "markdown"
) -> Dict[str, Any]:
    """
    Generate quickstart documentation from feature specifications.

    Args:
        include_test_scenarios: Include test scenarios in quickstart
        format: Output format (markdown, html, or pdf)

    Returns:
        ToolResponse with generated quickstart path
    """
    return (await documentation.generate_quickstart(
        include_test_scenarios=include_test_scenarios,
        format=format,
        settings=settings
    )).model_dump()


@mcp.tool()
@handle_errors
async def spec_kit_generate_contracts(
    contract_type: str = "openapi",
    include_tests: bool = True
) -> Dict[str, Any]:
    """
    Generate OpenAPI/GraphQL contracts from feature requirements.

    Args:
        contract_type: Type of contract to generate (openapi, graphql, or grpc)
        include_tests: Generate contract tests

    Returns:
        ToolResponse with generated contracts
    """
    return (await documentation.generate_contracts(
        contract_type=contract_type,
        include_tests=include_tests,
        settings=settings
    )).model_dump()


# Initialize server on module load
logger.info("Spec-kit MCP server initialized")
logger.info(f"Repository path: {settings.repo_path}")
logger.info(f"Templates path: {settings.templates_path}")
logger.info(f"Scripts path: {settings.scripts_path}")