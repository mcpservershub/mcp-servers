# Multi-stage Dockerfile for Tree-sitter MCP Server
# Stage 1: Builder - Install dependencies and build the package
FROM cgr.dev/chainguard/wolfi-base AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apk update && apk add python-3.12 py3.12-pip

# Copy package files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel

# Install the package with all dependencies
# Using tree-sitter 0.20.4 for compatibility with tree-sitter-languages
# TODO: Verify treesitter version
RUN pip install -e .

# Stage 2: Runtime - Minimal image with only runtime requirements
FROM cgr.dev/chainguard/wolfi-base AS final

# Install runtime dependencies including Rust toolchain
RUN apk update && apk add python-3.12 rust gcc

# Set PATH to include cargo bin directory
ENV PATH="/root/.cargo/bin:${PATH}"

# Install tree-sitter-graph CLI
RUN cargo install --features cli tree-sitter-graph

# Set working directory
WORKDIR /app

# COPY languages/ ./languages

# Create non-root user for security
RUN addgroup mcp && adduser -D -G mcp mcp

# Copy cargo binaries to mcp user's home and set ownership
RUN mkdir -p /home/mcp/.cargo/bin && \
  cp /root/.cargo/bin/tree-sitter-graph /home/mcp/.cargo/bin/ && \
  chown -R mcp:mcp /home/mcp/.cargo

# Create the tree-sitter config directory for mcp user
# RUN mkdir -p /home/mcp/.config/tree-sitter && chown -R mcp:mcp /home/mcp/.config

# Copy the config.json file to the tree-sitter config directory
# COPY --chown=mcp:mcp config.json /home/mcp/.config/tree-sitter/config.json
# Copy virtual environment from builder (includes installed package)
COPY --from=builder --chown=mcp:mcp /opt/venv /opt/venv

# Copy the entire build directory which has the installed package
COPY --from=builder --chown=mcp:mcp /build /app

# Set environment variables
ENV PATH="/opt/venv/bin:/home/mcp/.cargo/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Switch to non-root user
USER mcp

# Default command - run the MCP server
ENTRYPOINT ["python", "-m"]
CMD ["treesitter_mcp_new.server"]
