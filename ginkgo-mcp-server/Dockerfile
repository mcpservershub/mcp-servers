# Multi-stage Dockerfile for Ginkgo MCP Server using Chainguard images

# Stage 1: Builder
FROM cgr.dev/chainguard/go:latest-dev AS builder

# Set working directory
WORKDIR /build

# Copy go mod files first (better layer caching)
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the entire source tree
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/

# Build the application (CGO_ENABLED=0 for static binary)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
  -a \
  -ldflags='-w -s -extldflags "-static"' \
  -o ginkgo-mcp-server \
  ./cmd/ginkgo-mcp-server

# Stage 2: Runtime with Go toolchain (needed for running Ginkgo tests)
FROM cgr.dev/chainguard/go:latest

# Set working directory
WORKDIR /workspace

# Copy binary from builder
COPY --from=builder /build/ginkgo-mcp-server /app/ginkgo-mcp-server

# Install Ginkgo CLI
RUN go install github.com/onsi/ginkgo/v2/ginkgo@latest

# Set environment variables
ENV PATH="/home/nonroot/go/bin:${PATH}"
ENV WORK_DIR="/workspace"
ENV DATA_DIR="/app/data"
ENV GO111MODULE="on"

# Create necessary directories with proper permissions
USER root
RUN mkdir -p /app/data /workspace && \
  chown -R nonroot:nonroot /app /workspace

# Switch to non-root user (Chainguard images use 'nonroot' user)
USER nonroot

# Set entrypoint
ENTRYPOINT ["/app/ginkgo-mcp-server"]

# Default arguments
CMD ["-work-dir", "/workspace", "-data-dir", "/app/data"]
