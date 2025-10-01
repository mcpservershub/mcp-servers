# Multi-stage Dockerfile for Taskfile MCP Server

# Stage 1: Build environment
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install build dependencies
RUN apk update && apk add python-3.12 py3.12-pip

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
  pip install -e .

# Stage 2: Runtime environment
FROM cgr.dev/chainguard/wolfi-base

# Install runtime dependencies
RUN apk update && apk add python-3.12 py3.12-pip task

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
WORKDIR /app
COPY --from=builder /app/src ./src
COPY pyproject.toml .

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN addgroup mcp && adduser -D -G mcp mcp 

RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD task --version || exit 1

# Default command to run the MCP server
ENTRYPOINT ["python", "-m", "src.server"]
