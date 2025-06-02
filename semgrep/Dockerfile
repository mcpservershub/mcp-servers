FROM cgr.dev/chainguard/wolfi-base AS dev

WORKDIR /app

RUN apk update && apk add semgrep python-3.12 py3.12-pip py3.12-setuptools 
RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


# Final stage
FROM cgr.dev/chainguard/python:latest AS final

WORKDIR /app

COPY . .

COPY --from=dev /usr/bin/semgrep /usr/bin/semgrep
COPY --from=dev /app/venv /app/venv

ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT [ "python" "server.py" ]
CMD [ "-t", "streamable-http"]
