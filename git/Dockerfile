# Build stage
FROM cgr.dev/chainguard/python:latest-dev AS build

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
COPY pyproject.toml pyproject.toml
# COPY . /app
RUN pip install --no-cache-dir -e .

FROM cgr.dev/chainguard/wolfi-base

WORKDIR /app

RUN apk update && apk add git python-3.12 py3.12-pip py3.12-setuptools
COPY src/ /app/src

COPY --from=build /app/venv /app/venv 
ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT ["mcp-server-git"]






