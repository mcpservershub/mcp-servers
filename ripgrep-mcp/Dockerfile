# Multi-stage Dockerfile for Ripgrep MCP Server

# Stage 1: Builder
FROM cgr.dev/chainguard/wolfi-base AS builder

RUN apk update && apk add python-3.12 py3.12-pip
# Set working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies using pip
RUN python3.12 -m pip install --no-cache-dir . --target=/build/site-packages

# Stage 2: Runtime
FROM cgr.dev/chainguard/wolfi-base AS final

# Install ripgrep and Python
RUN apk update && apk add python-3.12 py3.12-pip ripgrep

# Create non-root user
RUN addgroup mcpuser && adduser -D -G mcpuser mcpuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /build/site-packages /usr/lib/python3.12/site-packages

# Copy application code
COPY --chown=mcpuser:mcpuser src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV RG_BINARY_PATH=/usr/bin/rg
ENV RG_MAX_RESULTS=1000
ENV RG_TIMEOUT=30
ENV RG_DEFAULT_PATH=/workspace
ENV RG_ALLOW_OUTSIDE_WORKSPACE=false

# Create workspace directory
RUN mkdir -p /workspace && chown mcpuser:mcpuser /workspace

# Switch to non-root user
USER mcpuser

# Set the entry point to run the module directly
ENTRYPOINT ["python", "-m", "ripgrep_mcp"]

