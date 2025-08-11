# Node.js Project Makefile Example
# Demonstrates Node.js/npm project automation

# Node and package managers
NODE := node
NPM := npm
YARN := yarn
PNPM := pnpm
NPX := npx

# Use npm by default, can override with PACKAGE_MANAGER=yarn or PACKAGE_MANAGER=pnpm
PACKAGE_MANAGER ?= npm

# Directories
SRC_DIR := src
DIST_DIR := dist
TEST_DIR := tests
PUBLIC_DIR := public
NODE_MODULES := node_modules

# Files
PACKAGE_JSON := package.json
PACKAGE_LOCK := package-lock.json
TSCONFIG := tsconfig.json
ENV_FILE := .env
ENV_EXAMPLE := .env.example

# Commands based on package manager
ifeq ($(PACKAGE_MANAGER),yarn)
	INSTALL_CMD := $(YARN) install
	RUN_CMD := $(YARN)
	ADD_CMD := $(YARN) add
	REMOVE_CMD := $(YARN) remove
	LOCK_FILE := yarn.lock
else ifeq ($(PACKAGE_MANAGER),pnpm)
	INSTALL_CMD := $(PNPM) install
	RUN_CMD := $(PNPM)
	ADD_CMD := $(PNPM) add
	REMOVE_CMD := $(PNPM) remove
	LOCK_FILE := pnpm-lock.yaml
else
	INSTALL_CMD := $(NPM) install
	RUN_CMD := $(NPM) run
	ADD_CMD := $(NPM) install
	REMOVE_CMD := $(NPM) uninstall
	LOCK_FILE := $(PACKAGE_LOCK)
endif

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: install dev build test lint format type-check clean start \
        docker-build docker-run deploy ci setup help watch debug \
        audit fix upgrade env

# Install dependencies
install: $(PACKAGE_JSON)
	@echo "Installing dependencies with $(PACKAGE_MANAGER)..."
	$(INSTALL_CMD)
	@echo "Dependencies installed"

# Install including dev dependencies
install-dev: $(PACKAGE_JSON)
	@echo "Installing all dependencies..."
	$(INSTALL_CMD)
	@echo "All dependencies installed"

# Setup environment
setup: install env
	@echo "Project setup complete"

# Create .env from example
env:
	@if [ ! -f $(ENV_FILE) ] && [ -f $(ENV_EXAMPLE) ]; then \
		echo "Creating .env file from .env.example..."; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo ".env file created - please update with your values"; \
	else \
		echo ".env file already exists or no .env.example found"; \
	fi

# Development server
dev: install
	@echo "Starting development server..."
	$(RUN_CMD) dev

# Watch mode
watch: install
	@echo "Starting watch mode..."
	$(RUN_CMD) watch

# Production build
build: install test
	@echo "Building for production..."
	$(RUN_CMD) build
	@echo "Build complete in $(DIST_DIR)/"

# Start production server
start: build
	@echo "Starting production server..."
	$(RUN_CMD) start

# Run tests
test: install
	@echo "Running tests..."
	$(RUN_CMD) test

# Run tests with coverage
test-coverage: install
	@echo "Running tests with coverage..."
	$(RUN_CMD) test:coverage

# Run tests in watch mode
test-watch: install
	@echo "Running tests in watch mode..."
	$(RUN_CMD) test:watch

# Linting
lint: install
	@echo "Running linter..."
	$(RUN_CMD) lint

# Fix linting issues
lint-fix: install
	@echo "Fixing linting issues..."
	$(RUN_CMD) lint:fix

# Format code
format: install
	@echo "Formatting code..."
	$(RUN_CMD) format

# Type checking (for TypeScript projects)
type-check: install
	@echo "Running type checker..."
	@if [ -f $(TSCONFIG) ]; then \
		$(RUN_CMD) type-check || $(NPX) tsc --noEmit; \
	else \
		echo "No TypeScript configuration found"; \
	fi

# Run all checks
check: lint type-check test
	@echo "All checks passed!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(DIST_DIR) coverage/ .next/ .nuxt/ .cache/
	rm -rf $(NODE_MODULES)
	rm -f $(LOCK_FILE)
	@echo "Clean complete"

# Security audit
audit: install
	@echo "Running security audit..."
	$(NPM) audit || $(YARN) audit || $(PNPM) audit

# Fix security issues
audit-fix: install
	@echo "Fixing security vulnerabilities..."
	$(NPM) audit fix || $(YARN) audit fix || $(PNPM) audit --fix

# Update dependencies
upgrade: install
	@echo "Checking for updates..."
	$(NPX) npm-check-updates -u
	$(INSTALL_CMD)
	@echo "Dependencies updated"

# Docker build
docker-build:
	@echo "Building Docker image..."
	docker build -t node-app:latest .
	@echo "Docker image built"

# Docker run
docker-run: docker-build
	@echo "Running Docker container..."
	docker run -it --rm -p 3000:3000 node-app:latest

# Docker compose
docker-compose-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

docker-compose-down:
	@echo "Stopping services..."
	docker-compose down

# Deploy to production
deploy: build
	@echo "Deploying to production..."
	@if [ -f deploy.sh ]; then \
		./deploy.sh; \
	else \
		echo "No deploy.sh script found"; \
		echo "Add your deployment commands here"; \
	fi

# CI pipeline
ci: install lint type-check test build
	@echo "CI pipeline complete!"

# Debug mode
debug: install
	@echo "Starting in debug mode..."
	$(NODE) --inspect $(SRC_DIR)/index.js

# Generate documentation
docs: install
	@echo "Generating documentation..."
	$(RUN_CMD) docs || $(NPX) jsdoc -c jsdoc.json

# Serve documentation
serve-docs: docs
	@echo "Serving documentation at http://localhost:8080"
	$(NPX) http-server ./docs -p 8080

# Database operations
db-migrate:
	@echo "Running database migrations..."
	$(RUN_CMD) migrate

db-seed:
	@echo "Seeding database..."
	$(RUN_CMD) seed

db-reset:
	@echo "Resetting database..."
	$(RUN_CMD) db:reset

# Bundle analysis
analyze: build
	@echo "Analyzing bundle..."
	$(RUN_CMD) analyze || $(NPX) webpack-bundle-analyzer $(DIST_DIR)/stats.json

# Performance testing
perf: build
	@echo "Running performance tests..."
	$(NPX) lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json

# Storybook (for component libraries)
storybook: install
	@echo "Starting Storybook..."
	$(RUN_CMD) storybook

build-storybook: install
	@echo "Building Storybook..."
	$(RUN_CMD) build-storybook

# Help
help:
	@echo "Node.js Project Makefile"
	@echo "========================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install      - Install dependencies"
	@echo "  make setup        - Complete project setup"
	@echo "  make env          - Create .env from .env.example"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development server"
	@echo "  make watch        - Start watch mode"
	@echo "  make debug        - Start in debug mode"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run tests"
	@echo "  make test-coverage- Run tests with coverage"
	@echo "  make test-watch   - Run tests in watch mode"
	@echo "  make lint         - Run linter"
	@echo "  make lint-fix     - Fix linting issues"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checker"
	@echo "  make check        - Run all checks"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build        - Build for production"
	@echo "  make start        - Start production server"
	@echo "  make deploy       - Deploy to production"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make audit        - Run security audit"
	@echo "  make audit-fix    - Fix security issues"
	@echo "  make upgrade      - Update dependencies"
	@echo "  make analyze      - Analyze bundle size"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run migrations"
	@echo "  make db-seed      - Seed database"
	@echo "  make db-reset     - Reset database"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Generate documentation"
	@echo "  make serve-docs   - Serve documentation"
	@echo "  make storybook    - Start Storybook"
	@echo ""
	@echo "Variables:"
	@echo "  PACKAGE_MANAGER=$(PACKAGE_MANAGER) (npm|yarn|pnpm)"
	@echo "  NODE=$(NODE)"