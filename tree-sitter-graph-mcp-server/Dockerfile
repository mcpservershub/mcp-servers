# Ultra-minimal Multi-stage Dockerfile for Tree-sitter MCP Server
# Stage 1: Rust builder - Build static tree-sitter-graph binary
FROM cgr.dev/chainguard/wolfi-base AS rust-builder

# Install Rust toolchain and build dependencies
RUN apk update && apk add rust gcc glibc-dev

# Build tree-sitter-graph with release optimizations
# Using release profile and link-time optimizations for smaller binary
ENV CARGO_PROFILE_RELEASE_LTO=true \
  CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1 \
  CARGO_PROFILE_RELEASE_OPT_LEVEL=3

RUN cargo install --features cli \
  --root /tmp/cargo-install \
  --target x86_64-unknown-linux-gnu \
  --profile release \
  tree-sitter-graph && \
  # Aggressively strip the binary
  strip -s /tmp/cargo-install/bin/tree-sitter-graph && \
  # Clean up cargo cache
  rm -rf /root/.cargo/registry /root/.cargo/git

# Stage 2: Python builder - Create minimal Python package for tsg
FROM cgr.dev/chainguard/wolfi-base AS python-builder

WORKDIR /build

# Install Python build dependencies
RUN apk update && apk add python-3.12 py3.12-pip gcc glibc-dev

# Copy only essential package files
COPY pyproject.toml ./
COPY src/ ./src/

# Create a minimal virtual environment
RUN python -m venv /opt/venv --without-pip --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into site-packages (keep dist-info for runtime metadata)
RUN python -m pip install --no-cache-dir --target /opt/venv/lib/python3.12/site-packages \
  --no-compile mcp && \
  # Copy the source package directly
  cp -r src/tree_sitter_graph_mcp /opt/venv/lib/python3.12/site-packages/ && \
  # Remove only safe-to-remove files (keep .dist-info for package metadata)
  find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
  find /opt/venv -type f -name "*.pyc" -delete && \
  find /opt/venv -type f -name "*.pyo" -delete && \
  find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# Stage 3: Compile language parsers
FROM cgr.dev/chainguard/wolfi-base AS parser-builder

# Install gcc for compiling parsers
RUN apk update && apk add gcc glibc-dev

WORKDIR /parsers

# Copy language files
COPY languages/ ./languages/

# Pre-compile all parsers as shared libraries if possible
# This step would need the actual tree-sitter CLI to work properly
# For now, we'll just keep the source files

# Stage 4: Final minimal runtime
FROM cgr.dev/chainguard/wolfi-base AS final

# Install absolute minimum runtime dependencies
# Using python-3.12-base instead of full python-3.12
RUN apk update && apk add --no-cache python-3.12-base libgcc gcc glibc-dev && \
  rm -rf /var/cache/apk/* /tmp/*

# Create non-root user
RUN addgroup -g 1000 mcp && adduser -u 1000 -D -G mcp mcp

# Setup directory structure
WORKDIR /app
RUN mkdir -p /home/mcp/.cargo/bin /home/mcp/.config/tree-sitter && \
  chown -R mcp:mcp /home/mcp /app

# Copy tree-sitter-graph static binary
COPY --from=rust-builder --chown=mcp:mcp /tmp/cargo-install/bin/tree-sitter-graph /home/mcp/.cargo/bin/

# Copy config
COPY --chown=mcp:mcp config.json /home/mcp/.config/tree-sitter/config.json

# Copy minimal Python environment
COPY --from=python-builder --chown=mcp:mcp /opt/venv/lib/python3.12/site-packages /usr/lib/python3.12/site-packages

# Copy language parsers (required for functionality)
COPY --from=parser-builder --chown=mcp:mcp /parsers/languages ./languages

# Copy source code
COPY --chown=mcp:mcp src/tree_sitter_graph_mcp /app/tree_sitter_graph_mcp

# Environment setup
ENV PATH="/home/mcp/.cargo/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH="/app" \
  PYTHONHOME="" \
  PYTHONNOUSERSITE=1

USER mcp

# Direct execution without venv
ENTRYPOINT ["python3.12", "-m", "tree_sitter_graph_mcp.server"]
