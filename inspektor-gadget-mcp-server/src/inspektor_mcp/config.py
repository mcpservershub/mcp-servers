"""Configuration management using Pydantic Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Inspektor-Gadget settings
    ig_binary_path: str = Field(default="ig", alias="IG_BINARY_PATH")
    ig_default_timeout: int = Field(default=120, alias="IG_DEFAULT_TIMEOUT")
    ig_default_runtime: str = Field(default="docker", alias="IG_DEFAULT_RUNTIME")
    
    # MCP Server settings
    mcp_server_name: str = Field(default="inspektor-gadget", alias="MCP_SERVER_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True
    )


# Global settings instance
settings = Settings()