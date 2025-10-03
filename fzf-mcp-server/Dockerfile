# Multi-stage Dockerfile for fzf-mcp-server

# Stage 1: Builder
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install system dependencies
RUN apk update && apk add python-3.12 py3.12-pip uv


# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
  . /app/.venv/bin/activate && \
  uv pip install -e .

# Stage 2: Runtime
FROM cgr.dev/chainguard/wolfi-base

# Install runtime dependencies
RUN apk update && apk add python-3.12 py3.12-pip uv fzf git


# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src /app/src

# Set working directory
WORKDIR /app

RUN addgroup mcp && adduser -D -G mcp mcp

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Python path
ENV PYTHONPATH="/app/src:$PYTHONPATH"

USER mcp

# Verify installations
# RUN fzf --version && \
#     python -c "import fzf_mcp_server; print(f'fzf-mcp-server v{fzf_mcp_server.__version__}')"

# Run the MCP server
CMD ["python", "-m", "fzf_mcp_server.server"]
