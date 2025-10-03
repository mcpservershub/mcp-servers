# Multistage Dockerfile for Pytest MCP Server
# Stage 1: Build stage with uv for dependency management
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install system dependencies for building
RUN apk update && apk add python-3.12 py3.12-pip uv


# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv venv && \
  . venv/bin/activate && \
  uv pip install -e .

# Stage 2: Production stage
FROM cgr.dev/chainguard/wolfi-base AS production

# Install runtime system dependencies
RUN apk update && apk add python-3.12 py3.12-pip \
  sqlite \
  curl 

RUN addgroup appuser && adduser -D -G appuser appuser

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
  chown -R appuser:appuser /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/venv /app/venv

# Copy source code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser pyproject.toml /app/

# Set working directory and switch to non-root user
WORKDIR /app
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Environment variables
ENV PYTEST_MCP_DB_PATH="/app/data/pytest_mcp.db"
ENV PYTEST_MCP_LOG_LEVEL="INFO"

# Default command
CMD ["python", "-m", "pytest_mcp_server.cli", "serve", "--db-path", "/app/data/pytest_mcp.db"]

# Stage 3: Development stage
FROM production as development

USER root

# Install development dependencies
RUN apk update && apk add \
  vim \
  less \
  htop 

USER appuser

# Install development Python packages
RUN . /app/venv/bin/activate && \
  uv pip install pytest-cov pytest-asyncio black flake8 mypy isort pre-commit

# Override CMD for development
CMD ["python", "-m", "pytest_mcp_server.cli", "serve", "--db-path", "/app/data/pytest_mcp.db"]
