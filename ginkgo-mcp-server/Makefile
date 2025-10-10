.PHONY: help build test clean run docker-build docker-run install lint fmt vet

# Variables
BINARY_NAME=ginkgo-mcp-server
DOCKER_IMAGE=ginkgo-mcp-server
VERSION=1.0.0
BUILD_DIR=./bin
GO_FILES=$(shell find . -name '*.go' -type f -not -path "./vendor/*")

# Default target
help:
	@echo "Available targets:"
	@echo "  build         - Build the binary"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean build artifacts"
	@echo "  run           - Run the server locally"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  install       - Install dependencies"
	@echo "  lint          - Run linter"
	@echo "  fmt           - Format code"
	@echo "  vet           - Run go vet"

# Build the binary
build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	@go build -o $(BUILD_DIR)/$(BINARY_NAME) ./cmd/ginkgo-mcp-server
	@echo "Binary built: $(BUILD_DIR)/$(BINARY_NAME)"

# Build for production (optimized)
build-prod:
	@echo "Building $(BINARY_NAME) for production..."
	@mkdir -p $(BUILD_DIR)
	@CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
		-a -installsuffix cgo \
		-ldflags='-w -s -extldflags "-static"' \
		-o $(BUILD_DIR)/$(BINARY_NAME) \
		./cmd/ginkgo-mcp-server
	@echo "Production binary built: $(BUILD_DIR)/$(BINARY_NAME)"

# Run tests
test:
	@echo "Running tests..."
	@go test -v -race -cover ./...

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	@go test -v -race -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -f coverage.out coverage.html
	@rm -f $(BINARY_NAME)
	@echo "Clean complete"

# Run the server locally
run:
	@echo "Running $(BINARY_NAME)..."
	@go run ./cmd/ginkgo-mcp-server -work-dir=. -data-dir=./data -debug

# Install dependencies
install:
	@echo "Installing dependencies..."
	@go mod download
	@go mod tidy
	@echo "Dependencies installed"

# Build Docker image
docker-build:
	@echo "Building Docker image $(DOCKER_IMAGE):$(VERSION)..."
	@docker build -t $(DOCKER_IMAGE):$(VERSION) -t $(DOCKER_IMAGE):latest .
	@echo "Docker image built: $(DOCKER_IMAGE):$(VERSION)"

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	@docker-compose up -d
	@echo "Container started. Use 'docker-compose logs -f' to view logs"

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	@docker-compose down
	@echo "Container stopped"

# Run linter (requires golangci-lint)
lint:
	@echo "Running linter..."
	@if command -v golangci-lint > /dev/null; then \
		golangci-lint run ./...; \
	else \
		echo "golangci-lint not installed. Install it from https://golangci-lint.run/"; \
	fi

# Format code
fmt:
	@echo "Formatting code..."
	@gofmt -w $(GO_FILES)
	@echo "Code formatted"

# Run go vet
vet:
	@echo "Running go vet..."
	@go vet ./...
	@echo "Vet complete"

# Generate mocks (if using mockery)
mocks:
	@echo "Generating mocks..."
	@if command -v mockery > /dev/null; then \
		mockery --all --dir ./pkg --output ./mocks; \
	else \
		echo "mockery not installed. Install it with: go install github.com/vektra/mockery/v2@latest"; \
	fi

# Run all checks
check: fmt vet lint test
	@echo "All checks passed!"