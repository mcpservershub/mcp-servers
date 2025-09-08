# Multi-stage Dockerfile for mise-tasks-mcp

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install build dependencies
RUN pip install --no-cache-dir build

# Build the package
RUN python -m build --wheel

# Runtime stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install mise
RUN curl https://mise.run | sh && \
    mv ~/.local/bin/mise /usr/local/bin/mise

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    mkdir -p /app && \
    chown -R mcp:mcp /app

WORKDIR /app

# Copy built wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Switch to non-root user
USER mcp

# Set environment
ENV PYTHONUNBUFFERED=1
ENV MISE_DATA_DIR=/app/.mise
ENV MISE_CONFIG_DIR=/app/.config/mise
ENV MISE_CACHE_DIR=/app/.cache/mise

# Create necessary directories
RUN mkdir -p $MISE_DATA_DIR $MISE_CONFIG_DIR $MISE_CACHE_DIR

# Expose MCP default port (if needed)
EXPOSE 5000

# Run the server
CMD ["python", "-m", "mise_tasks_mcp.server"]