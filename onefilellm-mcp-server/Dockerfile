# Lightweight Dockerfile for OneFileLLM MCP Server
FROM cgr.dev/chainguard/wolfi-base AS builder

# Accept GitHub token as build argument
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

# Install required system packages (minimal)
RUN apk update && apk add --no-cache \
  python-3.12 py3.12-pip \
  git \
  gcc \
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
RUN addgroup mcp && adduser -D -G mcp mcp
USER mcp

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the server as a module
ENTRYPOINT ["python", "-m", "onefilellm_mcp"]
