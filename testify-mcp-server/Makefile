# Testify MCP Server Makefile

.PHONY: build test clean docker docker-run deps fmt vet lint install dev

# Variables
BINARY_NAME=testify-mcp-server
MAIN_PATH=./cmd/testify-mcp-server
DOCKER_IMAGE=testify-mcp-server
VERSION?=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
LDFLAGS=-ldflags "-X main.version=$(VERSION)"

# Default target
all: clean deps fmt vet test build

# Install dependencies
deps:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Run go vet
vet:
	@echo "Running go vet..."
	go vet ./...

# Run tests
test:
	@echo "Running tests..."
	go test -v -race -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Run tests with short flag
test-short:
	@echo "Running short tests..."
	go test -v -short ./...

# Build binary
build:
	@echo "Building $(BINARY_NAME)..."
	CGO_ENABLED=0 go build $(LDFLAGS) -o $(BINARY_NAME) $(MAIN_PATH)

# Build for production (optimized)
build-prod:
	@echo "Building $(BINARY_NAME) for production..."
	CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags '-w -s -X main.version=$(VERSION)' -o $(BINARY_NAME) $(MAIN_PATH)

# Install binary to $GOPATH/bin
install:
	@echo "Installing $(BINARY_NAME)..."
	go install $(LDFLAGS) $(MAIN_PATH)

# Clean build artifacts
clean:
	@echo "Cleaning..."
	go clean
	rm -f $(BINARY_NAME)
	rm -f coverage.out coverage.html
	rm -rf data/
	rm -rf tmp/
	docker rmi $(DOCKER_IMAGE) 2>/dev/null || true

# Run linting
lint:
	@echo "Running linter..."
	@command -v golangci-lint >/dev/null 2>&1 || { \
		echo "golangci-lint not installed. Installing..."; \
		go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest; \
	}
	golangci-lint run

# Build Docker image
docker:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(VERSION) .
	docker tag $(DOCKER_IMAGE):$(VERSION) $(DOCKER_IMAGE):latest

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker run -it --rm \
		-v $(PWD)/workspace:/workspace:rw \
		-v $(PWD)/data:/app/data:rw \
		-p 8080:8080 \
		$(DOCKER_IMAGE):latest

# Start with docker-compose
docker-compose-up:
	@echo "Starting services with docker-compose..."
	docker-compose up -d

# Stop docker-compose services
docker-compose-down:
	@echo "Stopping services..."
	docker-compose down

# Development mode - run with hot reload
dev:
	@echo "Starting development server..."
	@command -v air >/dev/null 2>&1 || { \
		echo "air not installed. Installing..."; \
		go install github.com/cosmtrek/air@latest; \
	}
	air

# Run benchmarks
bench:
	@echo "Running benchmarks..."
	go test -bench=. -benchmem ./...

# Generate test coverage report
coverage:
	@echo "Generating coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Run with example project
run-example:
	@echo "Running server with example project..."
	mkdir -p workspace/example
	./$(BINARY_NAME) -work-dir=./workspace/example -debug

# Generate mock files (if using mockery)
mocks:
	@echo "Generating mocks..."
	@command -v mockery >/dev/null 2>&1 || { \
		echo "mockery not installed. Installing..."; \
		go install github.com/vektra/mockery/v2@latest; \
	}
	mockery --all --output ./mocks

# Security scan
security:
	@echo "Running security scan..."
	@command -v gosec >/dev/null 2>&1 || { \
		echo "gosec not installed. Installing..."; \
		go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest; \
	}
	gosec ./...

# Check for vulnerabilities
vuln:
	@echo "Checking for vulnerabilities..."
	@command -v govulncheck >/dev/null 2>&1 || { \
		echo "govulncheck not installed. Installing..."; \
		go install golang.org/x/vuln/cmd/govulncheck@latest; \
	}
	govulncheck ./...

# Generate documentation
docs:
	@echo "Generating documentation..."
	@command -v godoc >/dev/null 2>&1 || { \
		echo "godoc not installed. Installing..."; \
		go install golang.org/x/tools/cmd/godoc@latest; \
	}
	@echo "Starting documentation server at http://localhost:6060"
	godoc -http=:6060

# Release preparation
release-prep: clean deps fmt vet lint test build-prod
	@echo "Release preparation complete!"

# Cross-compile for multiple platforms
cross-compile:
	@echo "Cross-compiling for multiple platforms..."
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-linux-amd64 $(MAIN_PATH)
	GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o $(BINARY_NAME)-linux-arm64 $(MAIN_PATH)
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-darwin-amd64 $(MAIN_PATH)
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(BINARY_NAME)-darwin-arm64 $(MAIN_PATH)
	GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-windows-amd64.exe $(MAIN_PATH)

# Help
help:
	@echo "Available targets:"
	@echo "  build         - Build the binary"
	@echo "  build-prod    - Build optimized binary for production"
	@echo "  test          - Run tests with coverage"
	@echo "  test-short    - Run short tests"
	@echo "  clean         - Clean build artifacts"
	@echo "  deps          - Install dependencies"
	@echo "  fmt           - Format code"
	@echo "  vet           - Run go vet"
	@echo "  lint          - Run linter"
	@echo "  install       - Install binary to GOPATH/bin"
	@echo "  docker        - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  docker-compose-up   - Start with docker-compose"
	@echo "  docker-compose-down - Stop docker-compose services"
	@echo "  dev           - Start development server with hot reload"
	@echo "  bench         - Run benchmarks"
	@echo "  coverage      - Generate coverage report"
	@echo "  run-example   - Run server with example project"
	@echo "  security      - Run security scan"
	@echo "  vuln          - Check for vulnerabilities"
	@echo "  docs          - Start documentation server"
	@echo "  release-prep  - Prepare for release"
	@echo "  cross-compile - Cross-compile for multiple platforms"
	@echo "  help          - Show this help message"