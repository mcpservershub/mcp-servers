# Multi-stage Dockerfile for GnuCOBOL MCP Server

# Stage 1: Base image with GnuCOBOL compiler
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install GnuCOBOL and system dependencies
RUN apk update && apk add python-3.12 py3.12-pip uv

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml README.md ./
COPY gnucobol_mcp/ ./gnucobol_mcp/

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
  . /opt/venv/bin/activate && \
  uv pip install --no-cache .

# Stage 3: Final runtime image
FROM cgr.dev/chainguard/wolfi-base

# Install runtime dependencies and compilation libraries
RUN apk update && apk add python-3.12 \
  gnucobol \
  gcc \
  gmp \
  gmp-dev \
  ncurses-dev \
  db-dev


# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy project files
WORKDIR /app
# COPY --from=builder /build/gnucobol_mcp ./gnucobol_mcp
# COPY --from=builder /build/pyproject.toml /build/README.md ./

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 

# Verify installations
# RUN cobc --version 

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3.12 -c "import gnucobol_mcp; print('healthy')" || exit 1

# Set up non-root user for security
RUN addgroup mcpuser && adduser -D -G mcpuser mcpuser

USER mcpuser

# Expose STDIO mode (no network ports)
# The MCP server communicates via STDIN/STDOUT

# Set entrypoint to run the MCP server
ENTRYPOINT ["/opt/venv/bin/gnucobol-mcp"]

# Default command (can be overridden)
CMD []

