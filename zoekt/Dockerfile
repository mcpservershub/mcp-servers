FROM cgr.dev/chainguard/wolfi-base:latest AS builder

# Install build dependencies
RUN apk update && apk add --no-cache \
  go \
  git \
  build-base \
  ca-certificates \
  curl

# Set Go environment variables
ENV GO111MODULE=on \
  CGO_ENABLED=0 \
  GOOS=linux \
  GOARCH=amd64

# Create working directory
WORKDIR /app

# Clone the Zoekt repository
RUN git clone https://github.com/sourcegraph/zoekt.git /app/zoekt

# Build Zoekt CLI tools
WORKDIR /app/zoekt
RUN go mod download && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt ./cmd/zoekt && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-index ./cmd/zoekt-index && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-git-index ./cmd/zoekt-git-index && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-git-clone ./cmd/zoekt-git-clone && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-mirror-github ./cmd/zoekt-mirror-github && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-webserver ./cmd/zoekt-webserver && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-indexserver ./cmd/zoekt-indexserver

# Copy MCP server source code
COPY . /app/mcp-server
WORKDIR /app/mcp-server

# Download MCP server dependencies and build
RUN go mod download && \
  go build -ldflags="-s -w" -o /usr/local/bin/zoekt-mcp-server ./main.go

# Verify all binaries are built
RUN ls -la /usr/local/bin/zoekt*

# Stage 2: Runtime stage using Chainguard static image
FROM cgr.dev/chainguard/static:latest

# Copy CA certificates from builder stage
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy all Zoekt CLI tools from builder stage
COPY --from=builder /usr/local/bin/zoekt /usr/local/bin/zoekt
COPY --from=builder /usr/local/bin/zoekt-index /usr/local/bin/zoekt-index
COPY --from=builder /usr/local/bin/zoekt-git-index /usr/local/bin/zoekt-git-index
# COPY --from=builder /usr/local/bin/zoekt-git-clone /usr/local/bin/zoekt-git-clone
# COPY --from=builder /usr/local/bin/zoekt-mirror-github /usr/local/bin/zoekt-mirror-github
# COPY --from=builder /usr/local/bin/zoekt-webserver /usr/local/bin/zoekt-webserver
# COPY --from=builder /usr/local/bin/zoekt-indexserver /usr/local/bin/zoekt-indexserver

# Copy MCP server binary
COPY --from=builder /usr/local/bin/zoekt-mcp-server /usr/local/bin/zoekt-mcp-server

# Set working directory
WORKDIR /app

# Create directories for Zoekt data (note: static image doesn't have mkdir, so we'll create them via COPY)
# The directories will be created automatically when volumes are mounted

# Set environment variables
ENV PATH="/usr/local/bin:$PATH"
ENV ZOEKT_INDEX_DIR="/app/.zoekt"

# Expose any necessary ports (if needed for debugging)
# EXPOSE 6070

# Use the MCP server as the entrypoint
ENTRYPOINT ["/usr/local/bin/zoekt-mcp-server"]

