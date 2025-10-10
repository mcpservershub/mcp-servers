# Use Python 3.12 slim image for smaller size
FROM cgr.dev/chainguard/wolfi-base

RUN apk update && apk add python-3.12 py3.12-pip uv 
# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN uv pip install --system .

# Set default environment variables
ENV MEILI_HTTP_ADDR=http://meilisearch:7700
ENV MEILI_MASTER_KEY=""

# Run the MCP server
CMD ["python", "-m", "src.meilisearch_mcp"]
