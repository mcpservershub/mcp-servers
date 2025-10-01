"""Configuration management for spec-kit MCP server."""

from pathlib import Path
from typing import Optional, List
import os
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseModel):
    """Configuration settings for spec-kit MCP server."""

    # Repository settings
    repo_path: Path = Field(
        default_factory=lambda: Path(os.getenv("SPEC_KIT_REPO_PATH", str(Path.cwd())))
    )
    templates_path: Optional[Path] = None
    scripts_path: Optional[Path] = None

    # GitHub settings
    github_token: Optional[str] = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    github_repo_owner: str = Field(default="github")
    github_repo_name: str = Field(default="spec-kit")

    # Default settings
    default_ai_assistant: str = Field(
        default_factory=lambda: os.getenv("SPEC_KIT_DEFAULT_AI", "claude")
    )
    auto_git_init: bool = Field(default=True)

    # Performance settings
    max_concurrent_operations: int = Field(default=5)
    script_timeout: int = Field(default=30)  # seconds

    # Security settings
    allowed_paths: List[Path] = Field(default_factory=list)
    restrict_to_repo: bool = Field(default=True)

    @field_validator("repo_path", "templates_path", "scripts_path")
    @classmethod
    def validate_paths(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate that paths exist if provided."""
        if v and not v.exists():
            # Create the path if it doesn't exist
            v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("templates_path")
    @classmethod
    def set_templates_path(cls, v: Optional[Path], info) -> Path:
        """Set default templates path if not provided."""
        if v is None:
            repo_path = info.data.get("repo_path")
            if repo_path:
                return repo_path / ".specify" / "templates"
        return v

    @field_validator("scripts_path")
    @classmethod
    def set_scripts_path(cls, v: Optional[Path], info) -> Path:
        """Set default scripts path if not provided."""
        if v is None:
            repo_path = info.data.get("repo_path")
            if repo_path:
                return repo_path / ".specify" / "scripts"
        return v

    @field_validator("default_ai_assistant")
    @classmethod
    def validate_ai_assistant(cls, v: str) -> str:
        """Validate AI assistant choice."""
        valid_assistants = ["claude", "gemini", "copilot"]
        if v not in valid_assistants:
            raise ValueError(f"AI assistant must be one of {valid_assistants}")
        return v

    model_config = {
        "env_prefix": "SPEC_KIT_",
        "env_file": ".env",
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }


# Global settings instance
settings = Settings()