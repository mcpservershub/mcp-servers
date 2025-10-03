# Multi-stage Dockerfile for Ginkgo MCP Server

# Stage 1: Builder
FROM golang:1.24-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates gcc musl-dev

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
    -ldflags='-w -s -extldflags "-static"' \
    -o ginkgo-mcp-server \
    ./cmd/ginkgo-mcp-server

# Stage 2: Runtime
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    git \
    bash

# Install Go toolchain (required for running Ginkgo tests)
COPY --from=golang:1.24-alpine /usr/local/go /usr/local/go

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GO111MODULE="on"

# Install Ginkgo CLI
RUN go install github.com/onsi/ginkgo/v2/ginkgo@latest

# Add ginkgo to PATH
ENV PATH="/go/bin:${PATH}"

# Create app user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Create necessary directories
RUN mkdir -p /app/data /workspace && \
    chown -R appuser:appuser /app /workspace /go

# Copy binary from builder
COPY --from=builder --chown=appuser:appuser /build/ginkgo-mcp-server /app/ginkgo-mcp-server

# Switch to non-root user
USER appuser

# Set working directory
WORKDIR /workspace

# Expose environment variables
ENV WORK_DIR="/workspace"
ENV DATA_DIR="/app/data"

# Health check (not applicable for stdio mode, but useful for future HTTP support)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#   CMD [ "sh", "-c", "ps aux | grep ginkgo-mcp-server | grep -v grep" ]

# Set entrypoint
ENTRYPOINT ["/app/ginkgo-mcp-server"]

# Default arguments
CMD ["-work-dir", "/workspace", "-data-dir", "/app/data"]