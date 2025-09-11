"""Input validation utilities for LiteLLM MCP Server."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class CompletionRequest(BaseModel):
    """Validation model for completion requests."""
    
    model: str = Field(..., description="Model identifier")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling")
    stream: Optional[bool] = Field(False, description="Enable streaming")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    user: Optional[str] = Field(None, description="User identifier")
    
    @validator('messages')
    def validate_messages(cls, v):
        """Validate message format."""
        if not v:
            raise ValueError("Messages cannot be empty")
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content'")
            if msg['role'] not in ['system', 'user', 'assistant', 'function']:
                raise ValueError(f"Invalid role: {msg['role']}")
        return v


class FallbackCompletionRequest(BaseModel):
    """Validation model for fallback completion requests."""
    
    models: List[str] = Field(..., min_items=1, description="Ordered list of models to try")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    retry_strategy: Optional[str] = Field("sequential", pattern="^(sequential|random)$")


class EmbeddingRequest(BaseModel):
    """Validation model for embedding requests."""
    
    model: str = Field(..., description="Embedding model")
    input: str | List[str] = Field(..., description="Text(s) to embed")
    encoding_format: Optional[str] = Field(None, description="Encoding format")
    user: Optional[str] = Field(None, description="User identifier")


class ImageGenerationRequest(BaseModel):
    """Validation model for image generation requests."""
    
    model: str = Field(..., description="Image generation model")
    prompt: str = Field(..., min_length=1, description="Image generation prompt")
    n: Optional[int] = Field(1, ge=1, le=10, description="Number of images")
    size: Optional[str] = Field("1024x1024", pattern="^\\d+x\\d+$")
    quality: Optional[str] = Field("standard", pattern="^(standard|hd)$")
    style: Optional[str] = Field(None, pattern="^(vivid|natural)$")
    response_format: Optional[str] = Field("url", pattern="^(url|b64_json)$")
    user: Optional[str] = Field(None)


class CostEstimateRequest(BaseModel):
    """Validation model for cost estimation requests."""
    
    model: str = Field(..., description="Model identifier")
    prompt_tokens: int = Field(..., gt=0, description="Number of prompt tokens")
    max_completion_tokens: Optional[int] = Field(None, gt=0, description="Max completion tokens")


class ModelInfoRequest(BaseModel):
    """Validation model for model info requests."""
    
    model: str = Field(..., description="Model identifier")
    include_pricing: Optional[bool] = Field(True, description="Include pricing information")
    include_context: Optional[bool] = Field(True, description="Include context window info")


class RouterConfigRequest(BaseModel):
    """Validation model for router configuration."""
    
    strategy: str = Field(..., pattern="^(cost-optimized|latency-optimized|balanced)$")
    rules: Optional[List[Dict[str, Any]]] = Field(None, description="Custom routing rules")
    enable_fallback: Optional[bool] = Field(True)
    fallback_models: Optional[List[str]] = Field(None)


class BudgetConfigRequest(BaseModel):
    """Validation model for budget configuration."""
    
    daily_limit: Optional[float] = Field(None, gt=0, description="Daily spending limit in USD")
    weekly_limit: Optional[float] = Field(None, gt=0, description="Weekly spending limit in USD")
    monthly_limit: Optional[float] = Field(None, gt=0, description="Monthly spending limit in USD")
    alert_threshold: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Alert threshold")


def validate_model_name(model: str) -> str:
    """Validate and normalize model name."""
    # Remove leading/trailing whitespace
    model = model.strip()
    
    # Check if model is empty
    if not model:
        raise ValueError("Model name cannot be empty")
    
    # Common model name mappings
    model_aliases = {
        'gpt4': 'gpt-4',
        'gpt-4-turbo': 'gpt-4-turbo-preview',
        'claude3': 'claude-3-sonnet-20240229',
        'claude-3': 'claude-3-sonnet-20240229',
    }
    
    # Apply alias if exists
    model_lower = model.lower()
    if model_lower in model_aliases:
        model = model_aliases[model_lower]
    
    return model


def validate_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and normalize chat messages."""
    if not messages:
        raise ValueError("Messages cannot be empty")
    
    validated_messages = []
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise ValueError(f"Message at index {i} must be a dictionary")
        
        if 'role' not in msg:
            raise ValueError(f"Message at index {i} missing 'role'")
        
        if 'content' not in msg:
            raise ValueError(f"Message at index {i} missing 'content'")
        
        role = msg['role']
        if role not in ['system', 'user', 'assistant', 'function', 'tool']:
            raise ValueError(f"Invalid role '{role}' at index {i}")
        
        validated_messages.append({
            'role': role,
            'content': msg['content'],
            **{k: v for k, v in msg.items() if k not in ['role', 'content']}
        })
    
    return validated_messages