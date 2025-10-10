# Multi-stage Dockerfile for makefile-mcp

# Stage 1: Build environment
FROM cgr.dev/chainguard/wolfi-base AS builder

# Install build dependencies
RUN apk update && apk add python-3.12 py3.12-pip 

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml makefile_mcp.py ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
  pip install build && \
  pip install -e .

# Stage 2: Runtime environment
FROM cgr.dev/chainguard/wolfi-base

# Install make CLI (runtime dependency)
RUN apk update && apk add python-3.12 \
  make 

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application
COPY --from=builder /app/makefile_mcp.py /app/
COPY pyproject.toml /app/

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Run the MCP server
ENTRYPOINT ["python", "/app/makefile_mcp.py"]
