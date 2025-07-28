# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN go build -o sonarqube-mcp-server main.go

# Runtime stage
FROM cgr.dev/chainguard/static:latest

# Copy the binary from the builder stage
COPY --from=builder /app/sonarqube-mcp-server /sonarqube-mcp-server

# Set the entrypoint
ENTRYPOINT ["/sonarqube-mcp-server"]

# Default to stdio transport
CMD ["-t", "stdio"]