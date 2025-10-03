# Multi-stage Dockerfile for fd-mcp-server

# Stage 1: Builder stage
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install fd-find and build dependencies
RUN apk update && apk add python-3.12 py3.12-pip fd uv



# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install dependencies using uv
RUN uv pip install --system --no-cache -e .

# Stage 2: Runtime stage
FROM cgr.dev/chainguard/wolfi-base AS final

# Install fd-find in runtime
RUN apk update && apk add python-3.12 uv fd

# Create symlink for fd if it's named fdfind
# Create non-root user for security
RUN addgroup mcp && adduser -D -G mcp mcp

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/lib/python3.12/site-packages /usr/lib/python3.12/site-packages

# Copy application code
COPY --chown=mcp:mcp src ./src

# Switch to non-root user
USER mcp

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose MCP server (stdio-based, no network port)
# The server communicates via stdin/stdout

# Health check to verify fd is available
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD fd --version || exit 1

# Run the MCP server
CMD ["python", "-m", "src.fd_mcp_server"]
