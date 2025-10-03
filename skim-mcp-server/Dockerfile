# Multi-stage Dockerfile for Skim MCP Server

# ============================================================================
# Stage 1: Build and install skim (sk) from source
# ============================================================================
FROM alpine:3.19 AS skim-builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    bash \
    curl \
    wget

# Clone skim repository
RUN git clone --depth 1 https://github.com/skim-rs/skim.git /skim

WORKDIR /skim

# Make install script executable and run it with bash
RUN chmod +x install && bash ./install

# Verify sk binary exists
RUN test -f /skim/bin/sk && /skim/bin/sk --version

# ============================================================================
# Stage 2: Python build environment
# ============================================================================
FROM python:3.12-alpine AS python-builder

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system --no-cache .

# ============================================================================
# Stage 3: Final runtime image
# ============================================================================
FROM python:3.12-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    fd \
    ripgrep \
    bat \
    git \
    ncurses-terminfo-base

# Copy sk binary from builder stage
COPY --from=skim-builder /skim/bin/sk /usr/local/bin/sk

# Verify sk is executable
RUN sk --version

# Copy Python packages from builder
COPY --from=python-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-builder /app /app

# Set working directory
WORKDIR /workspace

# Set Python path
ENV PYTHONPATH=/app/src:${PYTHONPATH}

# Set environment variables for better skim behavior
ENV TERM=xterm-256color
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Create non-root user
RUN addgroup -g 1000 mcp && \
    adduser -D -u 1000 -G mcp mcp && \
    chown -R mcp:mcp /workspace

USER mcp

# Set entrypoint
ENTRYPOINT ["python", "-m", "skim_mcp_server.server"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD sk --version || exit 1

# Labels
LABEL org.opencontainers.image.title="Skim MCP Server"
LABEL org.opencontainers.image.description="MCP Server for skim (sk) fuzzy finder"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="Skim MCP Server Contributors"
LABEL org.opencontainers.image.source="https://github.com/skim-rs/skim"