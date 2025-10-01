# Official SuperBOL Dockerfile following the wiki instructions
# https://github.com/OCamlPro/superbol-studio-oss/wiki/SuperBOL-LSP

# Stage 1: Build SuperBOL using official method
FROM ubuntu:22.04 AS superbol-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    ca-certificates \
    unzip \
    pkg-config \
    libgmp-dev \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Install opam using official installer with non-interactive mode
RUN curl -fsSL https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh -o install_opam.sh && \
    echo '/usr/local/bin' | bash install_opam.sh

# Initialize opam and create switch
RUN opam init --disable-sandboxing -y && \
    opam switch create superbol-studio 4.14.1

# Clone SuperBOL and install
WORKDIR /opt
RUN git clone https://github.com/OCamlPro/superbol-studio-oss.git
WORKDIR /opt/superbol-studio-oss

# Install drom and SuperBOL
RUN eval $(opam env --switch=superbol-studio) && \
    opam install drom -y && \
    drom install --switch superbol-studio -y

# Verify SuperBOL installation and create launcher script
RUN eval $(opam env --switch=superbol-studio) && \
    opam exec --switch superbol-studio -- superbol-free --version && \
    echo '#!/bin/bash' > /usr/local/bin/superbol && \
    echo 'cd /opt/superbol-studio-oss' >> /usr/local/bin/superbol && \
    echo 'eval $(opam env --switch=superbol-studio)' >> /usr/local/bin/superbol && \
    echo 'exec opam exec --switch superbol-studio -- superbol-free "$@"' >> /usr/local/bin/superbol && \
    chmod +x /usr/local/bin/superbol

# Test the launcher
RUN /usr/local/bin/superbol --version

# Stage 2: Python runtime with MCP Server
FROM python:3.12-slim AS mcp-server

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install opam in runtime stage with non-interactive mode
RUN curl -fsSL https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh -o install_opam.sh && \
    echo '/usr/local/bin' | bash install_opam.sh

# Copy SuperBOL installation from builder
COPY --from=superbol-builder /root/.opam /root/.opam
COPY --from=superbol-builder /opt/superbol-studio-oss /opt/superbol-studio-oss
COPY --from=superbol-builder /usr/local/bin/superbol /usr/local/bin/superbol

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create workspace and cache directories
RUN mkdir -p /workspace /cache

# Set environment variables
ENV WORKSPACE_ROOT=/workspace \
    MCP_LSP_CACHE_DIR=/cache \
    PYTHONUNBUFFERED=1 \
    SUPERBOL_PATH=/usr/local/bin/superbol \
    PATH="/usr/local/bin:${PATH}"

# Verify SuperBOL installation in final stage
RUN superbol --version

# Default command to run the MCP server
CMD ["python", "-m", "multilspy_mcp.server"]