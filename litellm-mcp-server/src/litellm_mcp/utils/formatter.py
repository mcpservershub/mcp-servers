"""Response formatting utilities for LiteLLM MCP Server."""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime


def format_completion_response(response: Any) -> Dict[str, Any]:
    """Format LiteLLM completion response for MCP."""
    if hasattr(response, 'model_dump'):
        response_dict = response.model_dump()
    elif hasattr(response, 'dict'):
        response_dict = response.dict()
    else:
        response_dict = dict(response)
    
    # Extract key fields
    formatted = {
        'model': response_dict.get('model', 'unknown'),
        'created': response_dict.get('created', int(datetime.now().timestamp())),
        'content': None,
        'role': None,
        'finish_reason': None,
        'usage': None,
        'id': response_dict.get('id', 'unknown'),
    }
    
    # Extract message content
    if 'choices' in response_dict and response_dict['choices']:
        choice = response_dict['choices'][0]
        if 'message' in choice:
            formatted['content'] = choice['message'].get('content')
            formatted['role'] = choice['message'].get('role', 'assistant')
        formatted['finish_reason'] = choice.get('finish_reason')
    
    # Extract usage information
    if 'usage' in response_dict:
        formatted['usage'] = {
            'prompt_tokens': response_dict['usage'].get('prompt_tokens', 0),
            'completion_tokens': response_dict['usage'].get('completion_tokens', 0),
            'total_tokens': response_dict['usage'].get('total_tokens', 0),
        }
    
    return formatted


def format_embedding_response(response: Any) -> Dict[str, Any]:
    """Format LiteLLM embedding response for MCP."""
    if hasattr(response, 'model_dump'):
        response_dict = response.model_dump()
    elif hasattr(response, 'dict'):
        response_dict = response.dict()
    else:
        response_dict = dict(response)
    
    formatted = {
        'model': response_dict.get('model', 'unknown'),
        'embeddings': [],
        'usage': None,
    }
    
    # Extract embeddings
    if 'data' in response_dict:
        for item in response_dict['data']:
            if 'embedding' in item:
                formatted['embeddings'].append({
                    'index': item.get('index', 0),
                    'embedding': item['embedding'],
                })
    
    # Extract usage
    if 'usage' in response_dict:
        formatted['usage'] = {
            'prompt_tokens': response_dict['usage'].get('prompt_tokens', 0),
            'total_tokens': response_dict['usage'].get('total_tokens', 0),
        }
    
    return formatted


def format_image_response(response: Any) -> Dict[str, Any]:
    """Format LiteLLM image generation response for MCP."""
    if hasattr(response, 'model_dump'):
        response_dict = response.model_dump()
    elif hasattr(response, 'dict'):
        response_dict = response.dict()
    else:
        response_dict = dict(response)
    
    formatted = {
        'created': response_dict.get('created', int(datetime.now().timestamp())),
        'images': [],
    }
    
    # Extract image data
    if 'data' in response_dict:
        for item in response_dict['data']:
            image_data = {}
            if 'url' in item:
                image_data['url'] = item['url']
            elif 'b64_json' in item:
                image_data['b64_json'] = item['b64_json']
            if 'revised_prompt' in item:
                image_data['revised_prompt'] = item['revised_prompt']
            formatted['images'].append(image_data)
    
    return formatted


def format_model_info(model: str, info: Dict[str, Any]) -> Dict[str, Any]:
    """Format model information for MCP."""
    formatted = {
        'model': model,
        'provider': info.get('litellm_provider', 'unknown'),
        'mode': info.get('mode', 'chat'),
        'supports_function_calling': info.get('supports_function_calling', False),
        'supports_vision': info.get('supports_vision', False),
    }
    
    # Add pricing information if available
    if 'input_cost_per_token' in info:
        formatted['pricing'] = {
            'input_cost_per_token': info['input_cost_per_token'],
            'output_cost_per_token': info.get('output_cost_per_token', 0),
            'currency': 'USD',
        }
    
    # Add context window information
    if 'max_tokens' in info:
        formatted['context_window'] = {
            'max_tokens': info['max_tokens'],
            'max_input_tokens': info.get('max_input_tokens', info['max_tokens']),
            'max_output_tokens': info.get('max_output_tokens', 4096),
        }
    
    return formatted


def format_cost_estimate(estimate: Dict[str, Any]) -> Dict[str, Any]:
    """Format cost estimate for MCP."""
    return {
        'estimated_cost': {
            'prompt_cost': estimate.get('prompt_cost', 0),
            'completion_cost': estimate.get('completion_cost', 0),
            'total_cost': estimate.get('total_cost', 0),
            'currency': 'USD',
        },
        'token_counts': {
            'prompt_tokens': estimate.get('prompt_tokens', 0),
            'estimated_completion_tokens': estimate.get('estimated_completion_tokens', 0),
            'total_tokens': estimate.get('total_tokens', 0),
        },
        'model': estimate.get('model', 'unknown'),
    }


def format_usage_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Format usage statistics for MCP."""
    return {
        'period': stats.get('period', 'session'),
        'total_requests': stats.get('total_requests', 0),
        'total_tokens': stats.get('total_tokens', 0),
        'total_cost': stats.get('total_cost', 0),
        'by_model': stats.get('by_model', {}),
        'by_provider': stats.get('by_provider', {}),
        'currency': 'USD',
    }


def format_error_response(error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
    """Format error response for MCP."""
    error_response = {
        'error': {
            'type': type(error).__name__,
            'message': str(error),
        }
    }
    
    if context:
        error_response['error']['context'] = context
    
    # Add specific error details for known error types
    if hasattr(error, 'status_code'):
        error_response['error']['status_code'] = error.status_code
    
    if hasattr(error, 'llm_provider'):
        error_response['error']['provider'] = error.llm_provider
    
    return error_response


def format_streaming_chunk(chunk: Any) -> Dict[str, Any]:
    """Format a streaming chunk for MCP."""
    if hasattr(chunk, 'model_dump'):
        chunk_dict = chunk.model_dump()
    elif hasattr(chunk, 'dict'):
        chunk_dict = chunk.dict()
    else:
        chunk_dict = dict(chunk)
    
    formatted = {
        'type': 'stream_chunk',
        'model': chunk_dict.get('model', 'unknown'),
        'content': None,
        'finish_reason': None,
    }
    
    # Extract delta content
    if 'choices' in chunk_dict and chunk_dict['choices']:
        choice = chunk_dict['choices'][0]
        if 'delta' in choice and 'content' in choice['delta']:
            formatted['content'] = choice['delta']['content']
        formatted['finish_reason'] = choice.get('finish_reason')
    
    return formatted