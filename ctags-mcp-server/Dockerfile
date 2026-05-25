# Multi-stage Dockerfile for Universal CTags MCP Server

# Build stage for CTags - using Alpine for easier build dependencies
FROM cgr.dev/chainguard/wolfi-base AS ctags-builder

# Install build dependencies for CTags
RUN apk add --no-cache \
  make \
  gcc \
  git \
  autoconf \
  automake \
  pkgconf-dev \
  libtool 

# Clone and build Universal CTags (static build for portability)
RUN git clone https://github.com/universal-ctags/ctags.git /tmp/ctags \
  && cd /tmp/ctags \
  && ./autogen.sh \
  && ./configure --prefix=/usr --enable-static \
  && make LDFLAGS="-static" \
  && make install \
  && ls -la /usr/bin/ctags \
  && /usr/bin/ctags --version \
  && ldd /usr/bin/ctags || echo "Binary is statically linked"

# Build stage for Python dependencies
FROM cgr.dev/chainguard/wolfi-base AS python-builder

# Install Python and pip
RUN apk update && apk add \
  python-3.12 \
  python-3.12-dev \
  py3.12-pip \
  gcc \
  build-base

# Build Python dependencies
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python package with dependencies
RUN pip install --no-cache-dir --user . \
  && pip install --no-cache-dir --user python-ctags3

# Runtime stage
FROM cgr.dev/chainguard/wolfi-base AS final

# Install runtime dependencies
RUN apk update && apk add python-3.12 py3.12-pip \
  git 

# Copy Universal CTags binary from ctags-builder
COPY --from=ctags-builder /usr/bin/ctags /usr/bin/ctags
RUN chmod +x /usr/bin/ctags && ls -la /usr/bin/ctags

# Copy Python dependencies from python-builder
COPY --from=python-builder /root/.local /root/.local

# Copy application code
WORKDIR /app
COPY src/ ./src/
COPY pyproject.toml README.md ./

# Set Python path and CTags binary location
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV CTAGS_BINARY=/usr/bin/ctags

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory to workspace
WORKDIR /workspace

# Health check on port 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import ctags_mcp; print('healthy')" || exit 1

# Expose MCP default port (optional, for documentation)
EXPOSE 3000

# Run the MCP server
CMD ["python", "-m", "ctags_mcp.server"]
