# Multi-stage Dockerfile for Dependency Check MCP Server

# Stage 1: Download and setup Dependency Check
FROM openjdk:11-jre-slim as dependency-check
WORKDIR /opt

# Install required tools
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download Dependency Check
ENV DC_VERSION=9.0.7
RUN curl -L -o dependency-check.zip \
    https://github.com/jeremylong/DependencyCheck/releases/download/v${DC_VERSION}/dependency-check-${DC_VERSION}-release.zip \
    && unzip dependency-check.zip \
    && rm dependency-check.zip \
    && mv dependency-check /opt/dependency-check

# Stage 2: Python MCP Server with language runtimes
FROM python:3.12-slim

# Copy Dependency Check from previous stage
COPY --from=dependency-check /opt/dependency-check /opt/dependency-check

# Install Java runtime (required for Dependency Check)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install language runtimes for better scanning support
RUN apt-get update && apt-get install -y \
    # Version control
    git \
    # JavaScript/Node.js
    nodejs \
    npm \
    # Go
    golang \
    # Ruby
    ruby \
    ruby-dev \
    # Rust
    cargo \
    # PHP
    php \
    php-cli \
    # Common build tools
    build-essential \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install .NET runtime for assembly scanning
RUN apt-get update && apt-get install -y \
    wget \
    && wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update && apt-get install -y \
    dotnet-runtime-8.0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python package files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /data/dependency-check /workspace /output

# Set environment variables
ENV DEPENDENCY_CHECK_HOME=/opt/dependency-check
ENV PATH="${DEPENDENCY_CHECK_HOME}/bin:${PATH}"
ENV PYTHONPATH=/app:${PYTHONPATH}

# Create a non-root user
RUN useradd -m -u 1000 mcp-user \
    && chown -R mcp-user:mcp-user /app /data /workspace /output

# Switch to non-root user
USER mcp-user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Set the default command
CMD ["python", "-m", "src.dependency_check_mcp.server"]