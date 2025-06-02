# Build stage
FROM cgr.dev/chainguard/wolfi-base AS build

WORKDIR /app

RUN apk update && apk add git python-3.12 py3.12-pip py3.12-setuptools 
RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
# COPY requirements.txt requirements.txt
COPY . /app
RUN pip install -r requirements.txt

FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

RUN apk update && apk add git
COPY src/ .

COPY --from=build /app/venv /app/venv 
ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT [ "python", "git_mcp_server" ]






