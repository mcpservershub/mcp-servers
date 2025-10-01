# Use standard Python image for better compatibility
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies and build the package
RUN pip install --no-cache-dir -e .

# Production stage using Python slim runtime
FROM python:3.12-slim

# Install system dependencies needed for ast-grep-cli
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ast-grep CLI tool using pip
RUN pip install --no-cache-dir ast-grep-cli

# Set working directory
WORKDIR /app

# Copy the built package from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /app/src/ ./src/

# Clean up build dependencies to reduce image size
RUN apt-get remove -y build-essential curl && \
    apt-get autoremove -y && \
    apt-get clean

# Set Python path
ENV PYTHONPATH=/app/src

# Expose the default MCP port
EXPOSE 3000

# Set the entrypoint
ENTRYPOINT ["python", "-m", "ast_grep_mcp.server"]