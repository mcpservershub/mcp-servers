# Multi-stage Dockerfile for HTTPie MCP Server
# Optimized for size, security, and build speed

# Stage 1: Builder - Install dependencies and build
FROM cgr.dev/chainguard/wolfi-base AS builder

# Set build arguments
ARG UV_VERSION=0.5.0

# Install system dependencies needed for building
RUN apk update && apk add python-3.12 py3.12-pip uv 


# Set working directory
WORKDIR /build

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
COPY README.md ./

# Copy source code
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install the package and dependencies
RUN uv pip install -e .


# Stage 2: Runtime - Minimal production image
FROM cgr.dev/chainguard/wolfi-base AS runtime

RUN apk update && apk add python-3.12 httpie

# Install HTTPie and runtime dependencies
# HTTPie needs to be available in the runtime environment
# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --from=builder /build/src /app/src
COPY --from=builder /build/pyproject.toml /app/
COPY --from=builder /build/README.md /app/
COPY --from=builder /usr/bin/uv /usr/bin/uv

# Set environment variables
ENV PATH="/opt/venv/bin:${PATH}" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/app/src

# Set working directory
WORKDIR /app


# Health check (if needed for orchestration)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from httpie_mcp.httpie_client import HTTPieClient; HTTPieClient(verify_installation=True)" || exit 1

# Set entry point
ENTRYPOINT ["python", "-m", "httpie_mcp.server"]

