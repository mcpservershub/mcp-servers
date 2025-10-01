"""Main MCP server implementation for LiteLLM."""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from mcp.server.fastmcp import FastMCP
import litellm
from litellm import completion, acompletion, embedding, aembedding, image_generation
from litellm import completion_cost
from litellm.utils import get_valid_models, get_model_info

from .config import ConfigManager
from .utils import (
    format_completion_response,
    format_embedding_response,
    format_image_response,
    format_model_info,
    format_cost_estimate,
    format_usage_stats,
    format_error_response,
    CompletionRequest,
    FallbackCompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    CostEstimateRequest,
    ModelInfoRequest,
    validate_model_name,
    validate_messages,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configuration
config_manager = ConfigManager()

# Set environment variables for LiteLLM
for key, value in config_manager.get_litellm_env().items():
    os.environ[key] = value

# Initialize FastMCP server
mcp = FastMCP("litellm-mcp-server")

# Track usage statistics
usage_stats = {
    'total_requests': 0,
    'total_tokens': 0,
    'total_cost': 0.0,
    'by_model': {},
    'by_provider': {},
    'session_start': datetime.now().isoformat(),
}


def update_usage_stats(model: str, tokens: int, cost: float):
    """Update usage statistics."""
    global usage_stats
    usage_stats['total_requests'] += 1
    usage_stats['total_tokens'] += tokens
    usage_stats['total_cost'] += cost
    
    # Update by model
    if model not in usage_stats['by_model']:
        usage_stats['by_model'][model] = {'requests': 0, 'tokens': 0, 'cost': 0}
    usage_stats['by_model'][model]['requests'] += 1
    usage_stats['by_model'][model]['tokens'] += tokens
    usage_stats['by_model'][model]['cost'] += cost
    
    # Extract provider from model name
    provider = model.split('/')[0] if '/' in model else 'openai'
    if provider not in usage_stats['by_provider']:
        usage_stats['by_provider'][provider] = {'requests': 0, 'tokens': 0, 'cost': 0}
    usage_stats['by_provider'][provider]['requests'] += 1
    usage_stats['by_provider'][provider]['tokens'] += tokens
    usage_stats['by_provider'][provider]['cost'] += cost


@mcp.tool(
    name="litellm_complete",
    description="Complete text using any LLM provider through LiteLLM"
)
async def litellm_complete(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    stream: Optional[bool] = False,
    stop: Optional[List[str]] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete text using any LLM provider through LiteLLM.
    
    Args:
        model: Model identifier (e.g., 'gpt-4', 'claude-3-sonnet')
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        top_p: Top-p sampling
        stream: Enable streaming response
        stop: Stop sequences
        presence_penalty: Presence penalty (-2 to 2)
        frequency_penalty: Frequency penalty (-2 to 2)
        user: User identifier
    
    Returns:
        Formatted completion response
    """
    try:
        # Validate inputs
        model = validate_model_name(model)
        messages = validate_messages(messages)
        
        # Build kwargs
        kwargs = {
            'model': model,
            'messages': messages,
        }
        
        # Add optional parameters
        if temperature is not None:
            kwargs['temperature'] = temperature
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        if top_p is not None:
            kwargs['top_p'] = top_p
        if stop is not None:
            kwargs['stop'] = stop
        if presence_penalty is not None:
            kwargs['presence_penalty'] = presence_penalty
        if frequency_penalty is not None:
            kwargs['frequency_penalty'] = frequency_penalty
        if user is not None:
            kwargs['user'] = user
        
        # Handle streaming
        if stream:
            # For streaming, we'll collect chunks and return the full response
            response_chunks = []
            async for chunk in await acompletion(**kwargs, stream=True):
                response_chunks.append(chunk)
            
            # Combine chunks into final response
            if response_chunks:
                final_response = response_chunks[-1]
                return format_completion_response(final_response)
        else:
            # Non-streaming completion
            response = await acompletion(**kwargs)
            
            # Calculate cost and update stats
            if hasattr(response, 'usage'):
                total_tokens = response.usage.get('total_tokens', 0)
                try:
                    cost = completion_cost(completion_response=response)
                    update_usage_stats(model, total_tokens, cost)
                except:
                    pass
            
            return format_completion_response(response)
            
    except Exception as e:
        logger.error(f"Error in litellm_complete: {str(e)}")
        return format_error_response(e, f"Failed to complete with model {model}")


@mcp.tool(
    name="litellm_complete_with_fallback",
    description="Complete text with automatic fallback to alternative models on failure"
)
async def litellm_complete_with_fallback(
    models: List[str],
    messages: List[Dict[str, Any]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    retry_strategy: Optional[str] = "sequential",
) -> Dict[str, Any]:
    """
    Complete text with automatic fallback to alternative models.
    
    Args:
        models: Ordered list of models to try
        messages: List of message dictionaries
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        retry_strategy: 'sequential' or 'random'
    
    Returns:
        Formatted completion response from the first successful model
    """
    try:
        # Validate inputs
        if not models:
            raise ValueError("At least one model must be provided")
        
        messages = validate_messages(messages)
        
        # Prepare kwargs
        kwargs = {
            'messages': messages,
        }
        if temperature is not None:
            kwargs['temperature'] = temperature
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        # Try models based on strategy
        if retry_strategy == "random":
            import random
            models = random.sample(models, len(models))
        
        last_error = None
        for model in models:
            try:
                model = validate_model_name(model)
                response = await acompletion(model=model, **kwargs)
                
                # Calculate cost and update stats
                if hasattr(response, 'usage'):
                    total_tokens = response.usage.get('total_tokens', 0)
                    try:
                        cost = completion_cost(completion_response=response)
                        update_usage_stats(model, total_tokens, cost)
                    except:
                        pass
                
                result = format_completion_response(response)
                result['fallback_info'] = {
                    'model_used': model,
                    'models_tried': models[:models.index(model) + 1],
                    'strategy': retry_strategy,
                }
                return result
                
            except Exception as e:
                logger.warning(f"Model {model} failed: {str(e)}")
                last_error = e
                continue
        
        # All models failed
        return format_error_response(
            last_error or Exception("All models failed"),
            f"All fallback models failed: {models}"
        )
        
    except Exception as e:
        logger.error(f"Error in litellm_complete_with_fallback: {str(e)}")
        return format_error_response(e, "Failed to complete with fallback")


@mcp.tool(
    name="litellm_list_models",
    description="List all available LLM models with their providers and capabilities"
)
async def litellm_list_models(
    provider: Optional[str] = None,
    capability: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all available models.
    
    Args:
        provider: Filter by provider (e.g., 'openai', 'anthropic')
        capability: Filter by capability ('chat', 'completion', 'embedding', 'image')
    
    Returns:
        List of available models with their information
    """
    try:
        # Get all valid models
        all_models = get_valid_models()
        
        # Filter by provider if specified
        if provider:
            all_models = [m for m in all_models if provider.lower() in m.lower()]
        
        # Filter by capability if specified
        if capability:
            capability_models = []
            for model in all_models:
                try:
                    info = get_model_info(model)
                    if capability == 'chat' and info.get('mode') == 'chat':
                        capability_models.append(model)
                    elif capability == 'completion' and info.get('mode') == 'completion':
                        capability_models.append(model)
                    elif capability == 'embedding' and 'embed' in model.lower():
                        capability_models.append(model)
                    elif capability == 'image' and ('dall' in model.lower() or 'stable' in model.lower()):
                        capability_models.append(model)
                except:
                    continue
            all_models = capability_models
        
        # Get detailed info for each model
        models_info = []
        for model in all_models[:50]:  # Limit to 50 models for performance
            try:
                info = get_model_info(model)
                models_info.append({
                    'model': model,
                    'provider': info.get('litellm_provider', 'unknown'),
                    'mode': info.get('mode', 'chat'),
                    'supports_function_calling': info.get('supports_function_calling', False),
                    'supports_vision': info.get('supports_vision', False),
                })
            except:
                models_info.append({
                    'model': model,
                    'provider': 'unknown',
                    'mode': 'unknown',
                })
        
        return {
            'models': models_info,
            'total_count': len(models_info),
            'filters_applied': {
                'provider': provider,
                'capability': capability,
            }
        }
        
    except Exception as e:
        logger.error(f"Error in litellm_list_models: {str(e)}")
        return format_error_response(e, "Failed to list models")


@mcp.tool(
    name="litellm_model_info",
    description="Get detailed information about a specific model including costs and limits"
)
async def litellm_model_info(
    model: str,
    include_pricing: Optional[bool] = True,
    include_context: Optional[bool] = True,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific model.
    
    Args:
        model: Model identifier
        include_pricing: Include pricing information
        include_context: Include context window information
    
    Returns:
        Detailed model information
    """
    try:
        model = validate_model_name(model)
        
        # Get model info from LiteLLM
        info = get_model_info(model)
        
        # Format the response
        result = format_model_info(model, info)
        
        # Remove pricing if not requested
        if not include_pricing and 'pricing' in result:
            del result['pricing']
        
        # Remove context if not requested
        if not include_context and 'context_window' in result:
            del result['context_window']
        
        return result
        
    except Exception as e:
        logger.error(f"Error in litellm_model_info: {str(e)}")
        return format_error_response(e, f"Failed to get info for model {model}")


@mcp.tool(
    name="litellm_estimate_cost",
    description="Estimate the cost of a completion request before executing"
)
async def litellm_estimate_cost(
    model: str,
    prompt_tokens: int,
    max_completion_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Estimate the cost of a completion request.
    
    Args:
        model: Model identifier
        prompt_tokens: Number of prompt tokens
        max_completion_tokens: Maximum completion tokens (default: 1000)
    
    Returns:
        Cost estimate with breakdown
    """
    try:
        model = validate_model_name(model)
        
        # Default completion tokens if not specified
        if max_completion_tokens is None:
            max_completion_tokens = 1000
        
        # Get model info for pricing
        info = get_model_info(model)
        
        # Calculate costs
        prompt_cost = 0.0
        completion_cost = 0.0
        
        if 'input_cost_per_token' in info:
            prompt_cost = prompt_tokens * info['input_cost_per_token']
        
        if 'output_cost_per_token' in info:
            completion_cost = max_completion_tokens * info['output_cost_per_token']
        
        estimate = {
            'model': model,
            'prompt_tokens': prompt_tokens,
            'estimated_completion_tokens': max_completion_tokens,
            'total_tokens': prompt_tokens + max_completion_tokens,
            'prompt_cost': prompt_cost,
            'completion_cost': completion_cost,
            'total_cost': prompt_cost + completion_cost,
        }
        
        return format_cost_estimate(estimate)
        
    except Exception as e:
        logger.error(f"Error in litellm_estimate_cost: {str(e)}")
        return format_error_response(e, f"Failed to estimate cost for model {model}")


@mcp.tool(
    name="litellm_track_usage",
    description="Get usage statistics and costs for current session"
)
async def litellm_track_usage(
    time_range: Optional[str] = "session",
    group_by: Optional[str] = "total",
) -> Dict[str, Any]:
    """
    Get usage statistics for the current session.
    
    Args:
        time_range: Time range ('session', 'hour', 'day', 'week')
        group_by: Group results by ('model', 'provider', 'total')
    
    Returns:
        Usage statistics with cost breakdown
    """
    try:
        global usage_stats
        
        # Prepare stats based on grouping
        stats = {
            'period': time_range,
            'session_start': usage_stats['session_start'],
            'total_requests': usage_stats['total_requests'],
            'total_tokens': usage_stats['total_tokens'],
            'total_cost': usage_stats['total_cost'],
        }
        
        if group_by == 'model':
            stats['by_model'] = usage_stats['by_model']
        elif group_by == 'provider':
            stats['by_provider'] = usage_stats['by_provider']
        else:  # total
            stats['by_model'] = usage_stats['by_model']
            stats['by_provider'] = usage_stats['by_provider']
        
        return format_usage_stats(stats)
        
    except Exception as e:
        logger.error(f"Error in litellm_track_usage: {str(e)}")
        return format_error_response(e, "Failed to get usage statistics")


@mcp.tool(
    name="litellm_embed",
    description="Generate embeddings for text using any provider"
)
async def litellm_embed(
    model: str,
    input: str | List[str],
    encoding_format: Optional[str] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate embeddings for text.
    
    Args:
        model: Embedding model (e.g., 'text-embedding-ada-002')
        input: Text or list of texts to embed
        encoding_format: Encoding format
        user: User identifier
    
    Returns:
        Embeddings with metadata
    """
    try:
        model = validate_model_name(model)
        
        # Build kwargs
        kwargs = {
            'model': model,
            'input': input,
        }
        
        if encoding_format:
            kwargs['encoding_format'] = encoding_format
        if user:
            kwargs['user'] = user
        
        # Generate embeddings
        response = await aembedding(**kwargs)
        
        # Update usage stats
        if hasattr(response, 'usage'):
            total_tokens = response.usage.get('total_tokens', 0)
            # Estimate cost (embedding costs are typically lower)
            estimated_cost = total_tokens * 0.0001  # Rough estimate
            update_usage_stats(model, total_tokens, estimated_cost)
        
        return format_embedding_response(response)
        
    except Exception as e:
        logger.error(f"Error in litellm_embed: {str(e)}")
        return format_error_response(e, f"Failed to generate embeddings with model {model}")


@mcp.tool(
    name="litellm_generate_image",
    description="Generate images using various providers (DALL-E, Stable Diffusion, etc.)"
)
async def litellm_generate_image(
    model: str,
    prompt: str,
    n: Optional[int] = 1,
    size: Optional[str] = "1024x1024",
    quality: Optional[str] = "standard",
    style: Optional[str] = None,
    response_format: Optional[str] = "url",
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate images using various providers.
    
    Args:
        model: Image model (e.g., 'dall-e-3', 'dall-e-2')
        prompt: Image generation prompt
        n: Number of images to generate (1-10)
        size: Image size (e.g., '1024x1024', '512x512')
        quality: Image quality ('standard' or 'hd')
        style: Image style ('vivid' or 'natural')
        response_format: Response format ('url' or 'b64_json')
        user: User identifier
    
    Returns:
        Generated images with metadata
    """
    try:
        model = validate_model_name(model)
        
        # Validate inputs
        if not prompt or len(prompt.strip()) == 0:
            raise ValueError("Prompt cannot be empty")
        
        if n < 1 or n > 10:
            raise ValueError("Number of images must be between 1 and 10")
        
        # Build kwargs
        kwargs = {
            'model': model,
            'prompt': prompt,
            'n': n,
            'size': size,
            'quality': quality,
            'response_format': response_format,
        }
        
        if style:
            kwargs['style'] = style
        if user:
            kwargs['user'] = user
        
        # Generate images
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            image_generation, 
            prompt,
            model,
            n,
            quality,
            response_format,
            size,
            style,
            user
        )
        
        # Update usage stats (rough estimate for image generation)
        estimated_cost = n * 0.02  # Rough estimate per image
        update_usage_stats(model, 0, estimated_cost)
        
        return format_image_response(response)
        
    except Exception as e:
        logger.error(f"Error in litellm_generate_image: {str(e)}")
        return format_error_response(e, f"Failed to generate image with model {model}")


def create_server():
    """Create and return the MCP server instance."""
    return mcp


# Entry point for running the server
if __name__ == "__main__":
    import sys
    server = create_server()
    server.run(transport="stdio")