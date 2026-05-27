# Dockerfile for multilspy-mcp-server with C# (OmniSharp) support
# Extends the minimal Dockerfile with .NET SDK for C# language server

FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install .NET SDK 8.0 (required for OmniSharp C# language server)
RUN wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh \
    && chmod +x /tmp/dotnet-install.sh \
    && /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/local/dotnet \
    && ln -s /usr/local/dotnet/dotnet /usr/local/bin/dotnet \
    && rm /tmp/dotnet-install.sh

ENV DOTNET_ROOT=/usr/local/dotnet
ENV PATH="${PATH}:/usr/local/dotnet"
# Skip ICU requirement — libicu is not available in python:3.12-slim (Debian 13)
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Copy and install multilspy-mcp-server
WORKDIR /app
COPY pyproject.toml ./

# Copy source files
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Create workspace and cache directories
RUN mkdir -p /workspace /cache

ENV WORKSPACE_ROOT=/workspace \
  MCP_LSP_CACHE_DIR=/cache \
  PYTHONUNBUFFERED=1


# Default command to run the MCP server
CMD ["python", "-m", "multilspy_mcp"]
