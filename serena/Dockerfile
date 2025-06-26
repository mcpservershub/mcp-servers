FROM cgr.dev/chainguard/wolfi-base:latest AS dev

# Switch to root, set sane Python env
WORKDIR /workspace/serena
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

# Install OS build-tools for compiling any C extensions
RUN apk update && apk add --no-cache python-3.11 py3.11-pip py3.11-setuptools git openssh-client go

RUN go install golang.org/x/tools/gopls@latest

# Copy only the metadata + source for install
COPY pyproject.toml README.md /workspace/serena/
COPY src/ /workspace/serena/src/

# Create virtualenv, install the package in editable mode
RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH

RUN pip install --no-cache-dir -e .[all-extras]


# If you have a console-script entrypoint, e.g. [project.scripts] serena=serena.__main__:main
# CMD ["serena-mcp-server", "--project", "genval"]
CMD ["serena-mcp-server"]
