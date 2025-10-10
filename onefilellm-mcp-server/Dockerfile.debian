# Lightweight Dockerfile for OneFileLLM MCP Server
FROM python:3.12-alpine

# Accept GitHub token as build argument
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

# Install required system packages (minimal)
RUN apk add --no-cache \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e . && \
    pip cache purge

# Create non-root user
RUN adduser -D -u 1000 mcp
USER mcp

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the server as a module
ENTRYPOINT ["python", "-m", "onefilellm_mcp"]