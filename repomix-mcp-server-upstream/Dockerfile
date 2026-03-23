FROM cgr.dev/chainguard/wolfi-base

RUN mkdir /repomix
WORKDIR /repomix

COPY . .

# Install system deps + build in a single layer to avoid stale-cache issues
# with rolling wolfi packages
RUN apk update && apk add --no-cache git nodejs npm \
  && npm ci \
  && npm run build \
  && npm link \
  && npm ci --omit=dev \
  && npm cache clean --force

WORKDIR /app

# Check the operation of repomix
RUN repomix --version
RUN repomix --help

ENTRYPOINT ["repomix"]
CMD ["--mcp"]
