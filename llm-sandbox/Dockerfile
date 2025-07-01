
FROM cgr.dev/chainguard/wolfi-base:latest

ARG GITHUB_TOKEN

WORKDIR /app

ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1

RUN apk update && apk add --no-cache python-3.12 py3.12-pip git

# Configure Git to use the provided token for any HTTPS access to github.com.
# Instead of passingthe Token to clone the repo,
# it tells git to rewrite github.com URLs to include the token.
# RUN git config --global url."https://oauth2:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"

#RUN git config --global url."https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
# RUN git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"

COPY pyproject.toml .
COPY . .

RUN pip install --no-cache-dir -e '.[mcp-docker]'
# Set the command to run your application
# CMD ["python", "-m", "llm_sandbox.mcp_server"]
# CMD ["python",  "/app/llm_sandbox/mcp_server/server.py"]


