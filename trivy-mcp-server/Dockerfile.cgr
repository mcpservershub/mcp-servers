# Use Chainguard's Wolfi base image
FROM cgr.dev/chainguard/wolfi-base:latest

# Install required packages
RUN apk add --no-cache \
  python-3.12 \
  py3.12-pip \
  trivy

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml setup.py README.md ./
COPY src/ ./src/

# Create a non-root user
RUN adduser -D -u 1000 mcp-user

# Install the MCP server
RUN pip install --no-cache-dir -e . --break-system-packages

# Switch to non-root user
USER mcp-user

# Set the entrypoint to shell for better subprocess handling
ENTRYPOINT ["/bin/sh", "-c"]

# Default command runs the MCP server
CMD ["trivy-mcp-server"]
