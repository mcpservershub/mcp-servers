FROM cgr.dev/chainguard/wolfi-base AS dev

WORKDIR /app

RUN apk update && apk add semgrep python-3.12 py3.12-pip py3.12-setuptools 
RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .


# Final stage
FROM cgr.dev/chainguard/python:latest AS final

WORKDIR /app

COPY src/ /app/src/

COPY --from=dev /usr/bin/semgrep /usr/bin/semgrep
COPY --from=dev /app/venv /app/venv

ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT ["semgrep-mcp"]
CMD [ "-t", "streamable-http"]
