# Multi-stage Dockerfile for spec-kit MCP server

# Stage 1: Build environment
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install system dependencies
RUN apk update && apk add python-3.12 py3.12-pip \
  git \
  uv 

# Add uv to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Create virtual environment and install dependencies
RUN uv venv && \
  . .venv/bin/activate && \
  uv pip install -e .

# Stage 2: Runtime environment
FROM cgr.dev/chainguard/wolfi-base AS final

# Install runtime dependencies
RUN apk update && apk add python-3.12 \
  git 

# Create non-root user
RUN addgroup speckit && adduser -D -G speckit speckit 

# Set working directory
WORKDIR /app

# Copy from builder
COPY --from=builder --chown=speckit:speckit /app/.venv /app/.venv
COPY --from=builder --chown=speckit:speckit /app/src /app/src

# Create workspace directory
RUN mkdir -p /workspace && chown speckit:speckit /workspace

# Create .env file template
RUN echo "SPEC_KIT_REPO_PATH=/workspace" > /app/.env && \
  echo "SPEC_KIT_DEFAULT_AI=claude" >> /app/.env && \
  chown speckit:speckit /app/.env

# Set environment variables
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/src:${PYTHONPATH}"
ENV SPEC_KIT_REPO_PATH="/workspace"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER speckit

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import spec_kit_mcp; print('healthy')" || exit 1

# Expose MCP server port (if needed)
EXPOSE 8080

# Run MCP server
CMD ["python", "-m", "spec_kit_mcp"]
