# Multi-stage Dockerfile for Genval MCP Server
# Optimized for size and security

# =============================================================================
# Stage 1: Download and install Genval
# =============================================================================
FROM cgr.dev/chainguard/wolfi-base AS genval-builder

# Install dependencies for building Genval
RUN apk add --no-cache go git make bash curl

# Clone and build Genval
WORKDIR /build
RUN git clone -b pre-main https://github.com/intelops/genval.git . && \
  make build

# =============================================================================
# Stage 2: Build Python dependencies
# =============================================================================
FROM cgr.dev/chainguard/wolfi-base AS python-builder

RUN apk update && apk add python-3.12 py3.12-pip uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create virtual environment and install dependencies
# Non-editable install for production - copies code into .venv
RUN uv venv /opt/venv && \
  . /opt/venv/bin/activate && \
  uv pip install --no-cache-dir .

# =============================================================================
# Stage 3: Final runtime image
# =============================================================================
FROM cgr.dev/chainguard/wolfi-base

# Install runtime dependencies
RUN apk update && apk add python-3.12 py3.12-pip \
  git \
  curl

# Copy Genval binary from builder
COPY --from=genval-builder /build/bin/genval /usr/local/bin/genval

# Copy Python virtual environment from builder
# With non-editable install, .venv contains all source code
COPY --from=python-builder /opt/venv /opt/venv

# No need to copy src/ separately - it's already in .venv
WORKDIR /app

# Set Python path to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1


# Switch to non-root user
USER nonroot

# Create workspace directory
# RUN mkdir -p /home/mcp/workspace
# WORKDIR /home/mcp/workspace

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD genval version || exit 1

# Set entrypoint - use the installed console script
# The script is created by pip/uv during install and placed in .venv/bin
ENTRYPOINT ["genval-mcp-server"]

