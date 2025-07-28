# Use Chainguard's Wolfi base image
FROM cgr.dev/chainguard/wolfi-base:latest

# Install required packages
RUN apk add --no-cache \
  python-3.12 \
  py3.12-pip \
  curl

RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/bin

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml setup.py README.md ./
COPY src/ ./src/
COPY setup.py ./setup.py
COPY init-db.sh ./

# Create a non-root user
RUN adduser -D -u 1000 mcp-user

# Install the MCP server
RUN pip install --no-cache-dir -e . --break-system-packages

# Set environment variables for Grype database location
ENV GRYPE_DB_CACHE_DIR=/tmp/grype
ENV GRYPE_DB_AUTO_UPDATE=false

# Create cache directory with proper permissions
RUN mkdir -p /tmp/grype && chown -R mcp-user:mcp-user /tmp/grype

# Pre-download Grype database as root to the shared location
RUN GRYPE_DB_CACHE_DIR=/tmp/grype grype db update && \
    chown -R mcp-user:mcp-user /tmp/grype

# Switch to non-root user
USER mcp-user

# Ensure the database is accessible by running a test command as the user
RUN grype db status || echo "Database will be initialized on first run"

# Set the entrypoint to use our init script
ENTRYPOINT ["/app/init-db.sh"]

# Default command runs the MCP server
CMD ["grype-mcp-server"]
