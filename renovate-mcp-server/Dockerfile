FROM cgr.dev/chainguard/wolfi-base:latest AS build

# Install build dependencies
RUN apk update && apk add --no-cache renovate \
  python-3.12 \
  py3-pip \
  py3-setuptools \
  nodejs \
  npm

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH

# Copy requirements
COPY pyproject.toml ./
COPY src/ ./src/

# Create wheel
RUN pip install -e .


USER nobody

# Run the MCP server
CMD ["python", "-m", "renovate_mcp.server"]
