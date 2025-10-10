FROM cgr.dev/chainguard/wolfi-base

RUN apk update && apk add git nodejs npm

RUN mkdir /repomix
WORKDIR /repomix

# Install dependencies and build repomix, then link the package to the global scope
# To reduce the size of the layer, npm ci and npm link are executed in the same RUN command
COPY . .
RUN npm ci \
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
