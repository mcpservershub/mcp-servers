FROM cgr.dev/chainguard/wolfi-base AS build

WORKDIR /app

RUN apk update && apk add python-3.10 py3.10-pip py3.10-setuptools 
RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
# COPY requirements.txt requirements.txt
COPY . /app
RUN pip install -r requirements.txt

# Final stage
FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

COPY server.py config.py /app/

COPY --from=build /app/venv /app/venv 
ENV PATH="/app/venv/bin:$PATH"

EXPOSE 8000
# Command to run the server
CMD ["python", "-m", "server"]
