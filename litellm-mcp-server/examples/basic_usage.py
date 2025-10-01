#!/usr/bin/env python3
"""
Basic usage example for LiteLLM MCP Server.

This example demonstrates how to use the MCP server tools programmatically.
"""

import asyncio
import json
from typing import Dict, Any
import sys
import os

# Add parent directory to path
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
)


async def example_basic_completion():
    """Example: Basic text completion."""
    print("\n=== Basic Completion Example ===")
    
    result = await litellm_complete(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"Model: {result.get('model')}")
    print(f"Response: {result.get('content')}")
    print(f"Tokens used: {result.get('usage', {}).get('total_tokens')}")
    
    return result


async def example_fallback_completion():
    """Example: Completion with fallback models."""
    print("\n=== Fallback Completion Example ===")
    
    result = await litellm_complete_with_fallback(
        models=["gpt-4", "gpt-3.5-turbo", "claude-3-haiku-20240307"],
        messages=[
            {"role": "user", "content": "Explain quantum computing in one sentence."}
        ],
        temperature=0.5,
        max_tokens=100
    )
    
    if 'error' not in result:
        print(f"Model used: {result.get('fallback_info', {}).get('model_used')}")
        print(f"Response: {result.get('content')}")
        print(f"Models tried: {result.get('fallback_info', {}).get('models_tried')}")
    else:
        print(f"Error: {result['error']['message']}")
    
    return result


async def example_list_models():
    """Example: List available models."""
    print("\n=== List Models Example ===")
    
    # List all OpenAI chat models
    result = await litellm_list_models(
        provider="openai",
        capability="chat"
    )
    
    print(f"Found {result['total_count']} models")
    print("\nFirst 5 models:")
    for model in result['models'][:5]:
        print(f"  - {model['model']} ({model['provider']})")
    
    return result


async def example_model_info():
    """Example: Get detailed model information."""
    print("\n=== Model Info Example ===")
    
    result = await litellm_model_info(
        model="gpt-4",
        include_pricing=True,
        include_context=True
    )
    
    print(f"Model: {result['model']}")
    print(f"Provider: {result['provider']}")
    print(f"Supports function calling: {result.get('supports_function_calling')}")
    
    if 'pricing' in result:
        print(f"Input cost per token: ${result['pricing']['input_cost_per_token']}")
        print(f"Output cost per token: ${result['pricing']['output_cost_per_token']}")
    
    if 'context_window' in result:
        print(f"Max tokens: {result['context_window']['max_tokens']}")
    
    return result


async def example_cost_estimation():
    """Example: Estimate cost before making a request."""
    print("\n=== Cost Estimation Example ===")
    
    result = await litellm_estimate_cost(
        model="gpt-4",
        prompt_tokens=1000,
        max_completion_tokens=500
    )
    
    print(f"Model: {result['model']}")
    print(f"Prompt tokens: {result['token_counts']['prompt_tokens']}")
    print(f"Est. completion tokens: {result['token_counts']['estimated_completion_tokens']}")
    print(f"Estimated total cost: ${result['estimated_cost']['total_cost']:.4f}")
    
    return result


async def example_embeddings():
    """Example: Generate text embeddings."""
    print("\n=== Embeddings Example ===")
    
    result = await litellm_embed(
        model="text-embedding-ada-002",
        input="The quick brown fox jumps over the lazy dog."
    )
    
    print(f"Model: {result['model']}")
    print(f"Number of embeddings: {len(result['embeddings'])}")
    if result['embeddings']:
        print(f"Embedding dimensions: {len(result['embeddings'][0]['embedding'])}")
    print(f"Tokens used: {result.get('usage', {}).get('total_tokens')}")
    
    return result


async def example_image_generation():
    """Example: Generate an image."""
    print("\n=== Image Generation Example ===")
    
    result = await litellm_generate_image(
        model="dall-e-2",  # Using dall-e-2 for example
        prompt="A serene Japanese garden with cherry blossoms and a koi pond",
        size="512x512",
        n=1
    )
    
    if 'error' not in result:
        print(f"Images generated: {len(result['images'])}")
        if result['images']:
            for i, img in enumerate(result['images']):
                if 'url' in img:
                    print(f"Image {i+1} URL: {img['url']}")
                elif 'b64_json' in img:
                    print(f"Image {i+1}: Base64 encoded")
    else:
        print(f"Error: {result['error']['message']}")
    
    return result


async def example_usage_tracking():
    """Example: Track usage and costs."""
    print("\n=== Usage Tracking Example ===")
    
    # Make a few requests first
    await litellm_complete(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    
    # Check usage
    result = await litellm_track_usage(
        time_range="session",
        group_by="model"
    )
    
    print(f"Total requests: {result['total_requests']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Total cost: ${result['total_cost']:.4f}")
    
    if result.get('by_model'):
        print("\nUsage by model:")
        for model, stats in result['by_model'].items():
            print(f"  {model}:")
            print(f"    Requests: {stats['requests']}")
            print(f"    Tokens: {stats['tokens']}")
            print(f"    Cost: ${stats['cost']:.4f}")
    
    return result


async def main():
    """Run all examples."""
    print("=" * 50)
    print("LiteLLM MCP Server - Usage Examples")
    print("=" * 50)
    
    # Check if API keys are configured
    import os
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
        print("\n⚠️  Warning: No API keys detected in environment variables.")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY to run these examples.")
        print("\nYou can set them by:")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    try:
        # Run examples
        await example_basic_completion()
        await example_fallback_completion()
        await example_list_models()
        await example_model_info()
        await example_cost_estimation()
        await example_embeddings()
        # Uncomment to test image generation (requires DALL-E access)
        # await example_image_generation()
        await example_usage_tracking()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())