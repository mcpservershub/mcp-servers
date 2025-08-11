# Multi-stage Dockerfile for Tree MCP Server

# Stage 1: Build environment
FROM python:3.12-slim AS builder

# Install system dependencies and tree command
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    tree && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install MCP dependencies and the package itself
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "mcp[cli]" && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime environment
FROM python:3.12-slim

# Install only tree command (minimal runtime dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends tree && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user
RUN useradd -m -u 1000 mcpuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV MCP_ENV=production
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Change to non-root user
USER mcpuser

# Health check to ensure tree command is available
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD tree --version || exit 1

# Run the MCP server as a module
ENTRYPOINT ["python", "-m", "tree_mcp.server"]