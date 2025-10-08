# Build stage
FROM cgr.dev/chainguard/go:latest-dev AS builder

# Install git and build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy the entire source tree first
COPY . .

# Download dependencies (this will use the local go.mod)
RUN go mod download

# Verify the module structure
RUN go mod verify

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build \
  -o testify-mcp-server \
  ./cmd/testify-mcp-server

# Final stage - use golang:alpine to have Go toolchain available for running tests
FROM cgr.dev/chainguard/go:latest


# Copy the binary from builder stage
COPY --from=builder /build/testify-mcp-server /app/testify-mcp-server

# Set default environment variables
ENV WORK_DIR=/workspace
ENV DATA_DIR=/app/data

# Set working directory
WORKDIR /app

# Entrypoint
ENTRYPOINT ["/app/testify-mcp-server"]

# Default command arguments
CMD ["-work-dir", "/workspace", "-data-dir", "/app/data"]
