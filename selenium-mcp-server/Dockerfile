# Multi-stage Dockerfile for Selenium MCP Server using Chainguard base images

# Build stage - Use Chainguard Python image for building
FROM cgr.dev/chainguard/wolfi-base AS builder

RUN apk update && apk add python-3.12 py3.12-pip uv

# Set working directory
WORKDIR /app


# Copy dependency files
COPY pyproject.toml README.md ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
RUN uv pip install --no-cache-dir .

# Runtime stage - Use minimal Chainguard Python runtime
FROM cgr.dev/chainguard/wolfi-base AS runtime

RUN apk update && apk add python-3.12 py3.12-pip uv

# Install curl for health checks (minimal Chainguard image)
USER root
RUN apk add --no-cache curl

# Create selenium user and group
RUN addgroup -g 1200 selenium && \
  adduser -D -u 1200 -G selenium -s /bin/sh selenium

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy application code BEFORE switching user
COPY src/ ./src/

# Set Python path to include the source directory
ENV PYTHONPATH="/app/src:/app"

# Change ownership after copying
RUN chown -R selenium:selenium /app

# Switch to selenium user
USER selenium

# Set environment variables for Selenium Grid connection
ENV SELENIUM_GRID_HOST="selenium-hub"
ENV SELENIUM_GRID_PORT="4444"
ENV SELENIUM_GRID_URL="http://${SELENIUM_GRID_HOST}:${SELENIUM_GRID_PORT}/wd/hub"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import selenium_mcp; print('OK')" || exit 1

# Expose MCP server (stdio mode - no port needed)
# The server communicates via stdin/stdout

# Default command
CMD ["python", "-m", "selenium_mcp.server"]

# Development stage (optional)
FROM runtime AS development

USER root

# Install additional development tools
RUN apk add --no-cache git

# Install development Python dependencies
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/bin/uv /usr/bin/uv
RUN uv pip install --no-cache-dir pytest pytest-asyncio pytest-mock black isort mypy ruff

USER selenium

# Development command with debug logging
CMD ["python", "-m", "selenium_mcp.server", "--log-level", "DEBUG"]
