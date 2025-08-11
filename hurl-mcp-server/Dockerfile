# Use Chainguard Wolfi base image
FROM cgr.dev/chainguard/wolfi-base

# Install runtime dependencies
RUN apk update && apk add \
  wget \
  curl \
  libxml2 \
  python-3.12 \
  py3.12-pip 

RUN ln -s /usr/lib/libxml2.so /usr/lib/libxml2.so.2

# Download and install Hurl pre-built binary (gnu version)
RUN HURL_VERSION="7.0.0" \
  && mkdir -p /tmp \
  && cd /tmp \
  && wget "https://github.com/Orange-OpenSource/hurl/releases/download/${HURL_VERSION}/hurl-${HURL_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
  # && tar -xzf "hurl-${HURL_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
  && tar -xvf hurl-${HURL_VERSION}-x86_64-unknown-linux-gnu.tar.gz \
  && mv hurl-${HURL_VERSION}-x86_64-unknown-linux-gnu/bin/hurl /usr/bin/ \
  && rm -rf /tmp/hurl-* 

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY hurl_mcp ./hurl_mcp

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user (using adduser for Alpine-like systems)
RUN adduser -D -u 1000 -h /home/mcp mcp && chown -R mcp:mcp /app
USER mcp

# Set the entrypoint
ENTRYPOINT ["python", "-m", "hurl_mcp.server"]
