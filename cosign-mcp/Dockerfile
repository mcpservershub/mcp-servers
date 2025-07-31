FROM cgr.dev/chainguard/wolfi-base:latest

# Install Python 3.12 and required packages
RUN apk update && \
  apk add --no-cache \
  python-3.12 \
  py3.12-pip \
  curl \
  cosign

# # Install Cosign
# RUN mkdir -p /usr/local/bin && \
#   curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o /usr/local/bin/cosign && \
#   chmod +x /usr/local/bin/cosign

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY README.md .

# Install dependencies using system Python
RUN python3.12 -m pip install -e . --break-system-packages

# Set Python path
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create a non-root user
RUN adduser -D -u 1000 mcp-user && \
  chown -R mcp-user:mcp-user /app

# Switch to non-root user
USER mcp-user

# Set the entry point
ENTRYPOINT ["python3.12", "-m", "src.server"]
