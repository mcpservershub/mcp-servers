# LiteLLM MCP Server

A powerful MCP (Model Context Protocol) server that provides unified access to 100+ LLM providers through LiteLLM. This server enables seamless integration with OpenAI, Anthropic, Google, AWS Bedrock, Azure, and many other LLM providers using a single, consistent interface.

## Features

- 🚀 **Universal LLM Access**: Connect to 100+ LLM providers with a single interface
- 🔄 **Automatic Fallback**: Intelligent fallback to alternative models on failure
- 💰 **Cost Tracking**: Real-time cost estimation and usage tracking
- 🎯 **Smart Routing**: Optimize for cost, latency, or balanced performance
- 🖼️ **Multi-Modal Support**: Text completion, embeddings, and image generation
- 📊 **Model Discovery**: Browse and filter available models by capability
- 🔒 **Secure**: Environment-based API key management
- 🐳 **Docker Ready**: Production-ready containerized deployment

## Available Tools

### 1. `litellm_complete`
Complete text using any LLM provider through LiteLLM.

**Parameters:**
- `model` (string, required): Model identifier (e.g., 'gpt-4', 'claude-3-sonnet')
- `messages` (array, required): List of message objects with 'role' and 'content'
- `temperature` (number, optional): Sampling temperature (0-2)
- `max_tokens` (integer, optional): Maximum tokens to generate
- `top_p` (number, optional): Top-p sampling (0-1)
- `stream` (boolean, optional): Enable streaming response
- `stop` (array, optional): Stop sequences
- `presence_penalty` (number, optional): Presence penalty (-2 to 2)
- `frequency_penalty` (number, optional): Frequency penalty (-2 to 2)
- `user` (string, optional): User identifier

### 2. `litellm_complete_with_fallback`
Complete text with automatic fallback to alternative models on failure.

**Parameters:**
- `models` (array, required): Ordered list of models to try
- `messages` (array, required): List of message objects
- `temperature` (number, optional): Sampling temperature
- `max_tokens` (integer, optional): Maximum tokens to generate
- `retry_strategy` (string, optional): 'sequential' or 'random' (default: 'sequential')

### 3. `litellm_list_models`
List all available LLM models with their providers and capabilities.

**Parameters:**
- `provider` (string, optional): Filter by provider (e.g., 'openai', 'anthropic')
- `capability` (string, optional): Filter by capability ('chat', 'completion', 'embedding', 'image')

### 4. `litellm_model_info`
Get detailed information about a specific model including costs and limits.

**Parameters:**
- `model` (string, required): Model identifier
- `include_pricing` (boolean, optional): Include pricing information (default: true)
- `include_context` (boolean, optional): Include context window information (default: true)

### 5. `litellm_estimate_cost`
Estimate the cost of a completion request before executing.

**Parameters:**
- `model` (string, required): Model identifier
- `prompt_tokens` (integer, required): Number of prompt tokens
- `max_completion_tokens` (integer, optional): Maximum completion tokens (default: 1000)

### 6. `litellm_track_usage`
Get usage statistics and costs for current session.

**Parameters:**
- `time_range` (string, optional): Time range ('session', 'hour', 'day', 'week')
- `group_by` (string, optional): Group results by ('model', 'provider', 'total')

### 7. `litellm_embed`
Generate embeddings for text using any provider.

**Parameters:**
- `model` (string, required): Embedding model (e.g., 'text-embedding-ada-002')
- `input` (string/array, required): Text or list of texts to embed
- `encoding_format` (string, optional): Encoding format
- `user` (string, optional): User identifier

### 8. `litellm_generate_image`
Generate images using various providers (DALL-E, Stable Diffusion, etc.).

**Parameters:**
- `model` (string, required): Image model (e.g., 'dall-e-3')
- `prompt` (string, required): Image generation prompt
- `n` (integer, optional): Number of images (1-10, default: 1)
- `size` (string, optional): Image size (default: '1024x1024')
- `quality` (string, optional): Image quality ('standard' or 'hd')
- `style` (string, optional): Image style ('vivid' or 'natural')
- `response_format` (string, optional): Response format ('url' or 'b64_json')
- `user` (string, optional): User identifier

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/litellm-mcp-server.git
cd litellm-mcp-server

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/litellm-mcp-server.git
cd litellm-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: At least one provider API key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_API_KEY=...
AZURE_API_BASE=https://your-resource.openai.azure.com/
GOOGLE_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION_NAME=us-east-1

# Optional: Configuration
LITELLM_DEFAULT_MODEL=gpt-3.5-turbo
LITELLM_DEFAULT_TEMPERATURE=0.7
LITELLM_DEFAULT_MAX_TOKENS=2000
LITELLM_ENABLE_CACHE=true
LITELLM_DAILY_BUDGET_LIMIT=10.0
```

### Configuration File (Optional)

Create a `config.yaml` file:

```yaml
# API Keys
openai_api_key: ${OPENAI_API_KEY}
anthropic_api_key: ${ANTHROPIC_API_KEY}

# Default settings
default_model: gpt-3.5-turbo
default_temperature: 0.7
default_max_tokens: 2000

# Router configuration
enable_fallback: true
fallback_models:
  - gpt-3.5-turbo
  - claude-3-haiku-20240307
routing_strategy: cost-optimized

# Budget settings
enable_budget_tracking: true
daily_budget_limit: 10.0
alert_threshold: 0.8

# Cache settings
enable_cache: true
cache_ttl: 3600
```

## Running the Server

### Standalone

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the server
python -m litellm_mcp.server
```

### Using Docker

```bash
# Build the Docker image
docker build -t litellm-mcp-server .

# Run the container
docker run -it \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  litellm-mcp-server
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  litellm-mcp:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AZURE_API_KEY=${AZURE_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./config.yaml:/app/config/config.yaml:ro
    restart: unless-stopped
```

Run with:
```bash
docker-compose up
```

## MCP Configuration

### For Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "litellm": {
      "command": "python",
      "args": ["-m", "litellm_mcp.server"],
      "cwd": "/path/to/litellm-mcp-server",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### For Docker Container

```json
{
  "mcpServers": {
    "litellm": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "OPENAI_API_KEY=${OPENAI_API_KEY}",
        "-e", "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
        "litellm-mcp-server"
      ]
    }
  }
}
```

## Testing with MCP Inspector

Install MCP Inspector:
```bash
npm install -g @modelcontextprotocol/inspector
```

Run the inspector:
```bash
mcp-inspector python -m litellm_mcp.server
```

### Quick Tool Reference for Testing

| Tool | Description | Required Args | Example |
|------|-------------|---------------|---------|
| **litellm_complete** | Complete text using any LLM | `model`, `messages` | See example 1 below |
| **litellm_complete_with_fallback** | Complete with automatic fallback | `models`, `messages` | See example 2 below |
| **litellm_list_models** | List available models | None (all optional) | See example 3 below |
| **litellm_model_info** | Get model details & pricing | `model` | See example 4 below |
| **litellm_estimate_cost** | Estimate request cost | `model`, `prompt_tokens` | See example 5 below |
| **litellm_track_usage** | Get usage statistics | None (all optional) | See example 6 below |
| **litellm_embed** | Generate text embeddings | `model`, `input` | See example 7 below |
| **litellm_generate_image** | Generate images | `model`, `prompt` | See example 8 below |

### Test Examples

#### 1. Basic Completion
Complete text using any supported LLM provider.
```json
{
  "tool": "litellm_complete",
  "arguments": {
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }
}
```

#### 2. Completion with Fallback
Automatically fallback to alternative models if primary fails.
```json
{
  "tool": "litellm_complete_with_fallback",
  "arguments": {
    "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-haiku-20240307"],
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms"}
    ],
    "temperature": 0.5
  }
}
```

#### 3. List Available Models
Discover all available models, optionally filtered by provider or capability.
```json
{
  "tool": "litellm_list_models",
  "arguments": {
    "provider": "openai",
    "capability": "chat"
  }
}
```

#### 4. Get Model Information
Get detailed information about a specific model including pricing and limits.
```json
{
  "tool": "litellm_model_info",
  "arguments": {
    "model": "gpt-4",
    "include_pricing": true,
    "include_context": true
  }
}
```

#### 5. Estimate Cost
Calculate the estimated cost before making a request.
```json
{
  "tool": "litellm_estimate_cost",
  "arguments": {
    "model": "gpt-4",
    "prompt_tokens": 500,
    "max_completion_tokens": 1000
  }
}
```

#### 6. Track Usage
Monitor usage statistics and costs for the current session.
```json
{
  "tool": "litellm_track_usage",
  "arguments": {
    "time_range": "session",
    "group_by": "model"
  }
}
```

#### 7. Generate Embeddings
Create vector embeddings for text using any supported embedding model.
```json
{
  "tool": "litellm_embed",
  "arguments": {
    "model": "text-embedding-ada-002",
    "input": "The quick brown fox jumps over the lazy dog"
  }
}
```

#### 8. Generate Image
Create images using DALL-E, Stable Diffusion, or other image models.
```json
{
  "tool": "litellm_generate_image",
  "arguments": {
    "model": "dall-e-3",
    "prompt": "A futuristic city with flying cars at sunset",
    "size": "1024x1024",
    "quality": "standard",
    "n": 1
  }
}
```

### Minimal Test Examples (Required Args Only)

```json
// Simplest completion
{"tool": "litellm_complete", "arguments": {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hi"}]}}

// Simplest fallback
{"tool": "litellm_complete_with_fallback", "arguments": {"models": ["gpt-4", "gpt-3.5-turbo"], "messages": [{"role": "user", "content": "Hi"}]}}

// List all models
{"tool": "litellm_list_models", "arguments": {}}

// Model info
{"tool": "litellm_model_info", "arguments": {"model": "gpt-4"}}

// Cost estimate
{"tool": "litellm_estimate_cost", "arguments": {"model": "gpt-4", "prompt_tokens": 100}}

// Usage stats
{"tool": "litellm_track_usage", "arguments": {}}

// Embedding
{"tool": "litellm_embed", "arguments": {"model": "text-embedding-ada-002", "input": "Hello"}}

// Image generation
{"tool": "litellm_generate_image", "arguments": {"model": "dall-e-2", "prompt": "A cat"}}
```

## Supported Providers

This MCP server supports all providers available through LiteLLM, including:

- **OpenAI** (GPT-4, GPT-3.5, DALL-E, Whisper)
- **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
- **Google** (Gemini Pro, PaLM)
- **AWS Bedrock** (Claude, Llama, Mistral, Titan)
- **Azure OpenAI** (All OpenAI models via Azure)
- **Cohere** (Command, Embed)
- **Hugging Face** (Open source models)
- **Replicate** (Various open source models)
- **Together AI** (Open source models)
- **Mistral AI** (Mistral models)
- **Groq** (Fast inference)
- **Perplexity** (Online models)
- **DeepInfra** (Open source models)
- **Ollama** (Local models)
- **And 85+ more providers**

## Development

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=litellm_mcp --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format src/

# Lint code
ruff check src/
```

## Troubleshooting

### Common Issues

1. **No API keys configured:**
   - Ensure at least one provider API key is set in environment variables
   - Check that the `.env` file is in the correct location

2. **Model not found:**
   - Use `litellm_list_models` to see available models
   - Check that the provider for the model is configured

3. **Rate limiting:**
   - The server includes automatic retry logic
   - Configure fallback models for better reliability

4. **Docker connection issues:**
   - Ensure the container has network access
   - Check that API keys are properly passed to the container

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on [LiteLLM](https://github.com/BerriAI/litellm) for universal LLM access
- Uses [MCP](https://modelcontextprotocol.io/) for standardized AI tool integration
- Powered by [FastMCP](https://github.com/jlowin/fastmcp) for easy MCP server creation