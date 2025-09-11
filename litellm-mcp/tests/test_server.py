"""Tests for LiteLLM MCP Server."""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

# Mock litellm before importing server
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from litellm_mcp.server import (
    litellm_complete,
    litellm_complete_with_fallback,
    litellm_list_models,
    litellm_model_info,
    litellm_estimate_cost,
    litellm_track_usage,
    litellm_embed,
    litellm_generate_image,
    usage_stats,
)


@pytest.fixture
def mock_completion_response():
    """Mock completion response from LiteLLM."""
    response = Mock()
    response.model = "gpt-3.5-turbo"
    response.created = 1234567890
    response.id = "test-id"
    response.choices = [
        Mock(
            message=Mock(content="Test response", role="assistant"),
            finish_reason="stop"
        )
    ]
    response.usage = {
        'prompt_tokens': 10,
        'completion_tokens': 20,
        'total_tokens': 30
    }
    return response


@pytest.fixture
def mock_embedding_response():
    """Mock embedding response from LiteLLM."""
    response = Mock()
    response.model = "text-embedding-ada-002"
    response.data = [
        Mock(embedding=[0.1, 0.2, 0.3], index=0)
    ]
    response.usage = {
        'prompt_tokens': 5,
        'total_tokens': 5
    }
    return response


@pytest.fixture
def mock_image_response():
    """Mock image generation response from LiteLLM."""
    response = Mock()
    response.created = 1234567890
    response.data = [
        Mock(url="https://example.com/image.png")
    ]
    return response


@pytest.mark.asyncio
async def test_litellm_complete(mock_completion_response):
    """Test basic completion functionality."""
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_completion_response
        
        result = await litellm_complete(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100
        )
        
        assert result['model'] == "gpt-3.5-turbo"
        assert result['content'] == "Test response"
        assert result['role'] == "assistant"
        assert result['finish_reason'] == "stop"
        assert result['usage']['total_tokens'] == 30
        
        # Verify the call was made correctly
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs['model'] == "gpt-3.5-turbo"
        assert call_kwargs['temperature'] == 0.7
        assert call_kwargs['max_tokens'] == 100


@pytest.mark.asyncio
async def test_litellm_complete_with_streaming(mock_completion_response):
    """Test completion with streaming enabled."""
    # Create mock streaming chunks
    chunks = [
        Mock(choices=[Mock(delta=Mock(content="Test"), finish_reason=None)]),
        Mock(choices=[Mock(delta=Mock(content=" response"), finish_reason="stop")]),
    ]
    
    async def async_generator():
        for chunk in chunks:
            yield chunk
    
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = async_generator()
        
        # For this test, we'll assume the last chunk is returned
        chunks[-1].model = "gpt-3.5-turbo"
        chunks[-1].created = 1234567890
        chunks[-1].id = "test-id"
        chunks[-1].usage = {'total_tokens': 30}
        
        result = await litellm_complete(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            stream=True
        )
        
        # The implementation collects chunks and returns the last one
        assert result is not None


@pytest.mark.asyncio
async def test_litellm_complete_with_fallback(mock_completion_response):
    """Test completion with fallback models."""
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        # First call fails, second succeeds
        mock_acompletion.side_effect = [
            Exception("Model failed"),
            mock_completion_response
        ]
        
        result = await litellm_complete_with_fallback(
            models=["gpt-4", "gpt-3.5-turbo"],
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5
        )
        
        assert result['model'] == "gpt-3.5-turbo"
        assert result['content'] == "Test response"
        assert result['fallback_info']['model_used'] == "gpt-3.5-turbo"
        assert result['fallback_info']['models_tried'] == ["gpt-4", "gpt-3.5-turbo"]
        
        # Verify both models were tried
        assert mock_acompletion.call_count == 2


@pytest.mark.asyncio
async def test_litellm_complete_with_fallback_all_fail():
    """Test fallback when all models fail."""
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = Exception("All models failed")
        
        result = await litellm_complete_with_fallback(
            models=["gpt-4", "gpt-3.5-turbo"],
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert 'error' in result
        assert result['error']['type'] == 'Exception'
        assert "All models failed" in result['error']['message']


@pytest.mark.asyncio
async def test_litellm_list_models():
    """Test listing available models."""
    mock_models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "text-embedding-ada-002"]
    
    with patch('litellm_mcp.server.get_valid_models') as mock_get_models:
        with patch('litellm_mcp.server.get_model_info') as mock_get_info:
            mock_get_models.return_value = mock_models
            mock_get_info.return_value = {
                'litellm_provider': 'openai',
                'mode': 'chat',
                'supports_function_calling': True,
                'supports_vision': False
            }
            
            result = await litellm_list_models()
            
            assert 'models' in result
            assert 'total_count' in result
            assert len(result['models']) > 0
            assert result['models'][0]['model'] in mock_models


@pytest.mark.asyncio
async def test_litellm_list_models_with_filters():
    """Test listing models with filters."""
    mock_models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "text-embedding-ada-002"]
    
    with patch('litellm_mcp.server.get_valid_models') as mock_get_models:
        with patch('litellm_mcp.server.get_model_info') as mock_get_info:
            mock_get_models.return_value = mock_models
            mock_get_info.return_value = {
                'litellm_provider': 'openai',
                'mode': 'chat',
                'supports_function_calling': True,
                'supports_vision': False
            }
            
            result = await litellm_list_models(provider="openai", capability="chat")
            
            assert 'filters_applied' in result
            assert result['filters_applied']['provider'] == "openai"
            assert result['filters_applied']['capability'] == "chat"


@pytest.mark.asyncio
async def test_litellm_model_info():
    """Test getting model information."""
    mock_info = {
        'litellm_provider': 'openai',
        'mode': 'chat',
        'supports_function_calling': True,
        'supports_vision': False,
        'input_cost_per_token': 0.000001,
        'output_cost_per_token': 0.000002,
        'max_tokens': 4096,
        'max_input_tokens': 3000,
        'max_output_tokens': 1096
    }
    
    with patch('litellm_mcp.server.get_model_info') as mock_get_info:
        mock_get_info.return_value = mock_info
        
        result = await litellm_model_info(model="gpt-3.5-turbo")
        
        assert result['model'] == "gpt-3.5-turbo"
        assert result['provider'] == 'openai'
        assert result['supports_function_calling'] == True
        assert 'pricing' in result
        assert 'context_window' in result
        assert result['context_window']['max_tokens'] == 4096


@pytest.mark.asyncio
async def test_litellm_estimate_cost():
    """Test cost estimation."""
    mock_info = {
        'input_cost_per_token': 0.000001,
        'output_cost_per_token': 0.000002
    }
    
    with patch('litellm_mcp.server.get_model_info') as mock_get_info:
        mock_get_info.return_value = mock_info
        
        result = await litellm_estimate_cost(
            model="gpt-3.5-turbo",
            prompt_tokens=1000,
            max_completion_tokens=500
        )
        
        assert 'estimated_cost' in result
        assert result['estimated_cost']['prompt_cost'] == 0.001
        assert result['estimated_cost']['completion_cost'] == 0.001
        assert result['estimated_cost']['total_cost'] == 0.002
        assert result['token_counts']['prompt_tokens'] == 1000
        assert result['token_counts']['estimated_completion_tokens'] == 500


@pytest.mark.asyncio
async def test_litellm_track_usage():
    """Test usage tracking."""
    # Reset usage stats for testing
    global usage_stats
    usage_stats['total_requests'] = 5
    usage_stats['total_tokens'] = 150
    usage_stats['total_cost'] = 0.005
    usage_stats['by_model'] = {
        'gpt-3.5-turbo': {'requests': 3, 'tokens': 90, 'cost': 0.003},
        'gpt-4': {'requests': 2, 'tokens': 60, 'cost': 0.002}
    }
    
    result = await litellm_track_usage(time_range="session", group_by="model")
    
    assert result['period'] == 'session'
    assert result['total_requests'] == 5
    assert result['total_tokens'] == 150
    assert result['total_cost'] == 0.005
    assert 'by_model' in result
    assert result['by_model']['gpt-3.5-turbo']['requests'] == 3


@pytest.mark.asyncio
async def test_litellm_embed(mock_embedding_response):
    """Test embedding generation."""
    with patch('litellm_mcp.server.aembedding', new_callable=AsyncMock) as mock_aembedding:
        mock_aembedding.return_value = mock_embedding_response
        
        result = await litellm_embed(
            model="text-embedding-ada-002",
            input="Test text for embedding"
        )
        
        assert result['model'] == "text-embedding-ada-002"
        assert 'embeddings' in result
        assert len(result['embeddings']) > 0
        assert result['embeddings'][0]['embedding'] == [0.1, 0.2, 0.3]
        assert result['usage']['total_tokens'] == 5


@pytest.mark.asyncio
async def test_litellm_generate_image(mock_image_response):
    """Test image generation."""
    with patch('litellm_mcp.server.image_generation') as mock_image_gen:
        mock_image_gen.return_value = mock_image_response
        
        with patch('litellm_mcp.server.asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_image_response)
            
            result = await litellm_generate_image(
                model="dall-e-3",
                prompt="A beautiful sunset",
                size="1024x1024",
                n=1
            )
            
            assert 'images' in result
            assert len(result['images']) > 0
            assert result['images'][0]['url'] == "https://example.com/image.png"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in tools."""
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = Exception("API Error")
        
        result = await litellm_complete(
            model="invalid-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert 'error' in result
        assert result['error']['type'] == 'Exception'
        assert "API Error" in result['error']['message']


@pytest.mark.asyncio
async def test_message_validation():
    """Test message validation."""
    # Test with invalid messages
    result = await litellm_complete(
        model="gpt-3.5-turbo",
        messages=[]  # Empty messages
    )
    
    assert 'error' in result
    assert "cannot be empty" in result['error']['message'].lower()
    
    # Test with invalid message format
    result = await litellm_complete(
        model="gpt-3.5-turbo",
        messages=[{"invalid": "format"}]  # Missing role and content
    )
    
    assert 'error' in result


@pytest.mark.asyncio
async def test_model_name_normalization():
    """Test model name normalization."""
    with patch('litellm_mcp.server.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = Mock(
            model="gpt-4",
            choices=[Mock(message=Mock(content="Test", role="assistant"), finish_reason="stop")],
            usage={'total_tokens': 10}
        )
        
        # Test with different model name formats
        result = await litellm_complete(
            model="  gpt4  ",  # With spaces and without dash
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        # The model name should be normalized
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs['model'] == "gpt-4"  # Normalized name