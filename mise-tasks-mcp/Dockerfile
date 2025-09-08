# Chainguard-based multi-stage Dockerfile for mise-tasks-mcp

# Build stage using standard Python image
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install build dependencies
RUN pip install --no-cache-dir build

# Build the package
RUN python -m build --wheel

# Runtime stage using Chainguard Python
FROM cgr.dev/chainguard/python:latest

# Install runtime dependencies including bash for npm compatibility
USER root
RUN apk update && \
    apk add --no-cache \
        curl \
        git \
        bash \
        ca-certificates && \
    rm -rf /var/cache/apk/*

# Install mise
RUN curl https://mise.run | sh && \
    mv ~/.local/bin/mise /usr/local/bin/mise

# Create app directory
RUN mkdir -p /app && \
    chown -R nonroot:nonroot /app

WORKDIR /app

# Copy built wheel from builder
COPY --from=builder --chown=nonroot:nonroot /build/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Switch to non-root user
USER nonroot

# Set environment
ENV PYTHONUNBUFFERED=1
ENV MISE_DATA_DIR=/app/.mise
ENV MISE_CONFIG_DIR=/app/.config/mise
ENV MISE_CACHE_DIR=/app/.cache/mise

# Create necessary directories
RUN mkdir -p $MISE_DATA_DIR $MISE_CONFIG_DIR $MISE_CACHE_DIR

# Run the server
ENTRYPOINT ["python", "-m", "mise_tasks_mcp.server"]