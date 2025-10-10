FROM cgr.dev/chainguard/wolfi-base

# Install dependencies
RUN apk update && apk add python-3.12 py3.12-pip \
  curl jq

# Install Inspektor-Gadget
RUN ARCH=amd64 && \
  IG_VERSION=$(curl -s https://api.github.com/repos/inspektor-gadget/inspektor-gadget/releases/latest | jq -r .tag_name) && \
  curl -sL https://github.com/inspektor-gadget/inspektor-gadget/releases/download/${IG_VERSION}/ig-linux-${ARCH}-${IG_VERSION}.tar.gz | tar -C /usr/bin -xzf - ig

# Create app directory
WORKDIR /app

# Copy application files
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user (but container needs to run as root for eBPF)
# This is just for the file ownership
RUN addgroup mcp && adduser -D -G mcp mcp

RUN chown -R mcp:mcp /app

# Environment variables
ENV IG_BINARY_PATH=/usr/bin/ig \
  MCP_SERVER_NAME=inspektor-gadget \
  LOG_LEVEL=INFO

# The container must run as root for eBPF capabilities
USER root

# Entry point - run the MCP server module directly
ENTRYPOINT ["python", "-m", "inspektor_mcp"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ig version || exit 1
