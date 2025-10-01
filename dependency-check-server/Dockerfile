# Multi-stage Dockerfile for Dependency Check MCP Server

# Stage 1: Download and setup Dependency Check
FROM cgr.dev/chainguard/wolfi-base AS dev

WORKDIR /work

# Install required tools (Wolfi uses apk, not apt-get)
RUN apk update && apk add --no-cache \
  curl \
  unzip \
  bash

# Download Dependency Check
# First get the current version, then download it
RUN DC_VERSION=$(curl -s https://dependency-check.github.io/DependencyCheck/current.txt) && \
  echo "Downloading Dependency Check version: $DC_VERSION" && \
  curl -Ls \
  "https://github.com/dependency-check/DependencyCheck/releases/download/v${DC_VERSION}/dependency-check-${DC_VERSION}-release.zip" \
  --output dependency-check.zip && \
  unzip dependency-check.zip && \
  ls -la && \
  rm dependency-check.zip && \
  mkdir -p /opt && \
  mv dependency-check /opt/dependency-check || mv dependency-check-* /opt/dependency-check && \
  chmod +x /opt/dependency-check/bin/dependency-check.sh && \
  ls -la /opt/dependency-check/bin/

# Stage 2: Python MCP Server with language runtimes
FROM cgr.dev/chainguard/wolfi-base AS final

# Copy Dependency Check from previous stage
COPY --from=dev /opt/dependency-check /opt/dependency-check

# Install Java runtime (required for Dependency Check) and other dependencies
RUN apk update && apk add --no-cache \
  openjdk-17 \
  openjdk-17-jre \
  bash \
  git \
  nodejs \
  npm \
  go \
  ruby \
  ruby-dev \
  php \
  python-3.12 \
  py3.12-pip

# Install .NET runtime for assembly scanning
RUN apk add --no-cache dotnet-8-runtime

# Set JAVA in PATH
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk
ENV PATH "$PATH:${JAVA_HOME}/bin"


# Ensure dependency-check.sh is executable
RUN chmod +x /opt/dependency-check/bin/dependency-check.sh

# Set working directory
WORKDIR /app

# Copy Python package files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
  python3 -m pip install --no-cache-dir -e .


# Create data directory for vulnerability database
RUN mkdir -p /data/dependency-check && \
    chmod 777 /data/dependency-check

# Set environment variables
ENV DEPENDENCY_CHECK_HOME=/opt/dependency-check
ENV PATH="${DEPENDENCY_CHECK_HOME}/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH:-}"
ENV DEPENDENCY_CHECK_DATA=/data/dependency-check
ENV DISABLE_AUTO_UPDATE=false
ENV JAVA_OPTS="-Xmx4G"


# Volume for persistent data
VOLUME ["/data/dependency-check"]

# Volume for scanning projects
VOLUME ["/workspace"]

# Set the default command
CMD ["python3", "-m", "src.dependency_check_mcp.server"]
