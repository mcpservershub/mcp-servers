
# FROM cgr.dev/chainguard/wolfi-base AS dev
FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app
# RUN apk update && apk add python-3.12 py3.12-pip py3.12-setuptools

RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
COPY src/ /app/src
COPY pyproject.toml pyproject.toml

RUN pip install -e .

CMD ["gitingest-mcp"]
