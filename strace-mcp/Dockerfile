# Use Chainguard's Python image for better security
FROM cgr.dev/chainguard/python:latest-dev AS builder

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv venv && \
  uv pip install -e .

# Use distroless runtime image for smaller size and better security
FROM cgr.dev/chainguard/wolfi-base AS final

# Install strace (required for functionality)
RUN apk add --no-cache python-3.12 py3.12-pip strace
USER nonroot

# Copy the application and dependencies from builder
COPY --from=builder /app /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set Python path
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Run as non-root user (already set in base image)
# The container needs CAP_SYS_PTRACE capability to run strace
# This should be added when running the container with --cap-add SYS_PTRACE

# Expose the MCP server (stdio based, no network port needed)
# The server communicates via stdio

# Set the entrypoint to run the MCP server
ENTRYPOINT ["python", "-m", "strace_mcp.server"]

# Health check - since it's stdio based, we just check if strace is available
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD which strace || exit 1
