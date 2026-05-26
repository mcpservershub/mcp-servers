# Minimal Dockerfile for testing MCP server
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create workspace and cache directories
RUN mkdir -p /workspace /cache

# Set environment variables
ENV WORKSPACE_ROOT=/workspace \
    MCP_LSP_CACHE_DIR=/cache \
    PYTHONUNBUFFERED=1

# Default command to run the MCP server
CMD ["python", "-m", "multilspy_mcp"]