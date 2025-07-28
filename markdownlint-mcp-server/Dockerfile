FROM cgr.dev/chainguard/wolfi-base:latest

# Install Python 3.12 and required packages
RUN apk add --no-cache \
  python-3.12 \
  py3.12-pip \
  nodejs \
  npm 


# Install markdownlint-cli globally
RUN npm install -g markdownlint-cli

# Set working directory
WORKDIR /app

# Copy application files
COPY pyproject.toml pyproject.toml
COPY setup.py setup.py
COPY src ./src

# Install Python dependencies
RUN python3.12 -m pip install --no-cache-dir -e .

# Set environment variables
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Run the MCP server
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["markdownlint-mcp"]
