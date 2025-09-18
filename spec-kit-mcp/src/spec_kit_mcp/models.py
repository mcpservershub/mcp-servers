"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pathlib import Path


class AIAssistant(str, Enum):
    """Supported AI assistants."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    COPILOT = "copilot"


class ProjectType(str, Enum):
    """Project structure types."""
    SINGLE = "single"
    WEB = "web"
    MOBILE = "mobile"


class TaskStatus(str, Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ConstitutionCheckType(str, Enum):
    """Constitution check types."""
    SIMPLICITY = "simplicity"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    OBSERVABILITY = "observability"
    VERSIONING = "versioning"


class FeatureStatus(str, Enum):
    """Feature development status."""
    ALL = "all"
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DocumentFormat(str, Enum):
    """Documentation output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class ContractType(str, Enum):
    """API contract types."""
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"


class ToolResponse(BaseModel):
    """Standard response for all tools."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[str]] = None  # Changed to str for JSON serialization


class ErrorResponse(BaseModel):
    """Error response format."""
    error_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)


class InitProjectRequest(BaseModel):
    """Request model for spec_kit_init."""
    project_name: Optional[str] = None
    ai_assistant: AIAssistant = AIAssistant.CLAUDE
    use_current_dir: bool = False
    skip_git: bool = False
    ignore_agent_tools: bool = False

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: Optional[str], info) -> Optional[str]:
        """Validate project name."""
        values = info.data
        if not values.get("use_current_dir") and not v:
            raise ValueError("project_name is required when not using current directory")
        if v and not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "project_name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v


class SpecifyRequest(BaseModel):
    """Request model for spec_kit_specify."""
    feature_description: str = Field(..., min_length=10, max_length=5000)
    mark_clarifications: bool = True

    @field_validator("feature_description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate and clean feature description."""
        if not v.strip():
            raise ValueError("feature_description cannot be empty")
        return v.strip()


class PlanRequest(BaseModel):
    """Request model for spec_kit_plan."""
    tech_stack: str = Field(..., min_length=5, max_length=1000)
    language: str = Field(..., min_length=1, max_length=100)
    framework: str = Field(..., min_length=1, max_length=100)
    storage: Optional[str] = None
    project_type: ProjectType = ProjectType.SINGLE


class ResearchRequest(BaseModel):
    """Request model for spec_kit_research."""
    topics: List[str] = Field(..., min_items=1, max_items=10)
    context: str = Field(..., min_length=10, max_length=1000)

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: List[str]) -> List[str]:
        """Validate research topics."""
        cleaned = [topic.strip() for topic in v if topic.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty topic is required")
        return cleaned


class GenerateTasksRequest(BaseModel):
    """Request model for spec_kit_generate_tasks."""
    include_parallel_markers: bool = True
    enforce_tdd: bool = True


class TaskStatusRequest(BaseModel):
    """Request model for spec_kit_task_status."""
    task_id: str = Field(..., pattern=r"^T\d{3}$")
    status: Optional[TaskStatus] = None
    notes: Optional[str] = None


class ConstitutionCheckRequest(BaseModel):
    """Request model for spec_kit_check_constitution."""
    check_type: ConstitutionCheckType
    artifact_path: str

    @field_validator("artifact_path")
    @classmethod
    def validate_artifact_path(cls, v: str) -> str:
        """Validate artifact path."""
        if not v.strip():
            raise ValueError("artifact_path cannot be empty")
        return v.strip()


class ComplexityTrackingRequest(BaseModel):
    """Request model for spec_kit_complexity_tracking."""
    violation: str = Field(..., min_length=5, max_length=500)
    justification: str = Field(..., min_length=10, max_length=1000)
    alternatives_rejected: str = Field(..., min_length=10, max_length=1000)


class UpdateContextRequest(BaseModel):
    """Request model for spec_kit_update_context."""
    agent_type: AIAssistant
    technologies: Dict[str, str] = Field(default_factory=dict)
    recent_changes: List[str] = Field(default_factory=list, max_items=10)


class ListFeaturesRequest(BaseModel):
    """Request model for spec_kit_list_features."""
    status_filter: FeatureStatus = FeatureStatus.ALL


class GenerateQuickstartRequest(BaseModel):
    """Request model for spec_kit_generate_quickstart."""
    include_test_scenarios: bool = True
    format: DocumentFormat = DocumentFormat.MARKDOWN


class GenerateContractsRequest(BaseModel):
    """Request model for spec_kit_generate_contracts."""
    contract_type: ContractType = ContractType.OPENAPI
    include_tests: bool = True


class ValidateSpecRequest(BaseModel):
    """Request model for spec_kit_validate_spec."""
    spec_path: str = Field(..., min_length=1)

    @field_validator("spec_path")
    @classmethod
    def validate_spec_path(cls, v: str) -> str:
        """Validate spec path."""
        if not v.strip():
            raise ValueError("spec_path cannot be empty")
        return v.strip()