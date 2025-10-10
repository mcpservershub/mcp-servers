"""Configuration management for LiteLLM MCP Server."""

import os
from typing import Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LiteLLMConfig(BaseModel):
    """Configuration for LiteLLM MCP Server."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    azure_api_key: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    azure_api_base: Optional[str] = Field(default=None, description="Azure OpenAI base URL")
    azure_api_version: Optional[str] = Field(default="2024-02-15-preview", description="Azure API version")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS Access Key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS Secret Access Key")
    aws_region_name: Optional[str] = Field(default="us-east-1", description="AWS Region")
    
    # Default settings
    default_model: str = Field(default="gpt-3.5-turbo", description="Default model to use")
    default_temperature: float = Field(default=0.7, description="Default temperature")
    default_max_tokens: int = Field(default=2000, description="Default max tokens")
    default_timeout: int = Field(default=30, description="Default timeout in seconds")
    
    # Router configuration
    enable_fallback: bool = Field(default=True, description="Enable automatic fallback")
    fallback_models: list[str] = Field(
        default=["gpt-3.5-turbo", "claude-3-haiku-20240307"],
        description="Fallback models in order of preference"
    )
    routing_strategy: str = Field(
        default="cost-optimized",
        description="Routing strategy: cost-optimized, latency-optimized, or balanced"
    )
    
    # Budget settings
    enable_budget_tracking: bool = Field(default=True, description="Enable budget tracking")
    daily_budget_limit: float = Field(default=10.0, description="Daily budget limit in USD")
    alert_threshold: float = Field(default=0.8, description="Alert when budget reaches this percentage")
    
    # Cache settings
    enable_cache: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_requests: bool = Field(default=True, description="Log all requests")
    
    class Config:
        env_prefix = "LITELLM_"
        case_sensitive = False


class ConfigManager:
    """Manages configuration for the LiteLLM MCP Server."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("LITELLM_CONFIG_FILE", "config.yaml")
        self.config = self._load_config()
    
    def _load_config(self) -> LiteLLMConfig:
        """Load configuration from file and environment variables."""
        config_data = {}
        
        # Load from YAML file if exists
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                file_config = yaml.safe_load(f) or {}
                config_data.update(file_config)
        
        # Override with environment variables
        env_overrides = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'azure_api_key': os.getenv('AZURE_API_KEY'),
            'azure_api_base': os.getenv('AZURE_API_BASE'),
            'azure_api_version': os.getenv('AZURE_API_VERSION'),
            'google_api_key': os.getenv('GOOGLE_API_KEY'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'aws_region_name': os.getenv('AWS_REGION_NAME'),
        }
        
        # Filter out None values and update config
        env_overrides = {k: v for k, v in env_overrides.items() if v is not None}
        config_data.update(env_overrides)
        
        return LiteLLMConfig(**config_data)
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get all configured API keys."""
        return {
            'openai': self.config.openai_api_key,
            'anthropic': self.config.anthropic_api_key,
            'azure': self.config.azure_api_key,
            'google': self.config.google_api_key,
        }
    
    def get_litellm_env(self) -> Dict[str, str]:
        """Get environment variables for LiteLLM."""
        env = {}
        if self.config.openai_api_key:
            env['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.anthropic_api_key:
            env['ANTHROPIC_API_KEY'] = self.config.anthropic_api_key
        if self.config.azure_api_key:
            env['AZURE_API_KEY'] = self.config.azure_api_key
        if self.config.azure_api_base:
            env['AZURE_API_BASE'] = self.config.azure_api_base
        if self.config.google_api_key:
            env['GEMINI_API_KEY'] = self.config.google_api_key
        if self.config.aws_access_key_id:
            env['AWS_ACCESS_KEY_ID'] = self.config.aws_access_key_id
        if self.config.aws_secret_access_key:
            env['AWS_SECRET_ACCESS_KEY'] = self.config.aws_secret_access_key
        if self.config.aws_region_name:
            env['AWS_REGION_NAME'] = self.config.aws_region_name
        return env