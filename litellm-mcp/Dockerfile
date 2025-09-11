# Multi-stage Dockerfile for LiteLLM MCP Server

# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src ./src

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install the package and dependencies
RUN uv pip install --no-cache .

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    mkdir -p /app /home/mcp/.cache && \
    chown -R mcp:mcp /app /home/mcp

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=mcp:mcp src ./src

# Create config directory
RUN mkdir -p /app/config && chown -R mcp:mcp /app/config

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import litellm_mcp; print('Health check passed')" || exit 1

# Labels
LABEL org.opencontainers.image.title="LiteLLM MCP Server"
LABEL org.opencontainers.image.description="MCP Server for LiteLLM - Unified interface for 100+ LLM providers"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="LiteLLM MCP Server"

# Default command - run the MCP server
CMD ["python", "-m", "litellm_mcp.server"]