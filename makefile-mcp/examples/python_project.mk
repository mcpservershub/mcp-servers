# Python Project Makefile Example
# Demonstrates Python project automation

# Python interpreter
PYTHON := python3.12
PIP := $(PYTHON) -m pip
VENV := .venv
VENV_ACTIVATE := . $(VENV)/bin/activate

# Project settings
PROJECT_NAME := myproject
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
DIST_DIR := dist

# Tools
BLACK := $(VENV)/bin/black
MYPY := $(VENV)/bin/mypy
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
COVERAGE := $(VENV)/bin/coverage

# Files
PYTHON_FILES := $(shell find $(SRC_DIR) $(TEST_DIR) -name "*.py" 2>/dev/null || echo "")
REQUIREMENTS := requirements.txt
DEV_REQUIREMENTS := requirements-dev.txt

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: all venv install install-dev test coverage lint format type-check clean \
        build publish docs serve-docs docker run debug profile help

# Setup virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(VENV_ACTIVATE) && $(PIP) install --upgrade pip setuptools wheel
	@echo "Virtual environment created at $(VENV)"

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	$(VENV_ACTIVATE) && $(PIP) install -r $(REQUIREMENTS)
	@echo "Dependencies installed"

install-dev: install
	@echo "Installing development dependencies..."
	$(VENV_ACTIVATE) && $(PIP) install -r $(DEV_REQUIREMENTS)
	@echo "Development dependencies installed"

# Run tests
test: install-dev
	@echo "Running tests..."
	$(VENV_ACTIVATE) && $(PYTEST) $(TEST_DIR) -v --color=yes

# Run tests with coverage
coverage: install-dev
	@echo "Running tests with coverage..."
	$(VENV_ACTIVATE) && $(COVERAGE) run -m pytest $(TEST_DIR)
	$(VENV_ACTIVATE) && $(COVERAGE) report -m
	$(VENV_ACTIVATE) && $(COVERAGE) html
	@echo "Coverage report generated in htmlcov/"

# Linting
lint: install-dev
	@echo "Running linters..."
	$(VENV_ACTIVATE) && $(RUFF) check $(SRC_DIR) $(TEST_DIR)
	@echo "Linting complete"

# Format code
format: install-dev
	@echo "Formatting code..."
	$(VENV_ACTIVATE) && $(BLACK) $(SRC_DIR) $(TEST_DIR)
	$(VENV_ACTIVATE) && $(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "Formatting complete"

# Type checking
type-check: install-dev
	@echo "Running type checker..."
	$(VENV_ACTIVATE) && $(MYPY) $(SRC_DIR)
	@echo "Type checking complete"

# Quality checks (all checks)
check: lint type-check test
	@echo "All quality checks passed!"

# Build package
build: clean
	@echo "Building package..."
	$(VENV_ACTIVATE) && $(PYTHON) -m build
	@echo "Package built in $(DIST_DIR)/"

# Publish to PyPI
publish: build
	@echo "Publishing to PyPI..."
	$(VENV_ACTIVATE) && $(PYTHON) -m twine upload $(DIST_DIR)/*
	@echo "Package published"

# Generate documentation
docs: install-dev
	@echo "Generating documentation..."
	$(VENV_ACTIVATE) && cd $(DOCS_DIR) && $(MAKE) html
	@echo "Documentation generated in $(DOCS_DIR)/_build/html/"

# Serve documentation locally
serve-docs: docs
	@echo "Serving documentation at http://localhost:8000"
	$(VENV_ACTIVATE) && $(PYTHON) -m http.server 8000 --directory $(DOCS_DIR)/_build/html/

# Docker operations
docker-build:
	@echo "Building Docker image..."
	docker build -t $(PROJECT_NAME):latest .
	@echo "Docker image built"

docker-run: docker-build
	@echo "Running Docker container..."
	docker run -it --rm $(PROJECT_NAME):latest

# Run application
run: install
	@echo "Running application..."
	$(VENV_ACTIVATE) && $(PYTHON) -m $(PROJECT_NAME)

# Debug mode
debug: install-dev
	@echo "Running in debug mode..."
	$(VENV_ACTIVATE) && $(PYTHON) -m pdb -m $(PROJECT_NAME)

# Profile application
profile: install-dev
	@echo "Profiling application..."
	$(VENV_ACTIVATE) && $(PYTHON) -m cProfile -o profile.stats -m $(PROJECT_NAME)
	$(VENV_ACTIVATE) && $(PYTHON) -m pstats profile.stats
	@echo "Profile data saved to profile.stats"

# Database operations
db-init:
	@echo "Initializing database..."
	$(VENV_ACTIVATE) && $(PYTHON) -m $(PROJECT_NAME).db init
	@echo "Database initialized"

db-migrate:
	@echo "Running database migrations..."
	$(VENV_ACTIVATE) && $(PYTHON) -m $(PROJECT_NAME).db migrate
	@echo "Migrations complete"

db-seed:
	@echo "Seeding database..."
	$(VENV_ACTIVATE) && $(PYTHON) -m $(PROJECT_NAME).db seed
	@echo "Database seeded"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(DIST_DIR) build/ *.egg-info
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	@echo "Clean complete"

# Update dependencies
update-deps: venv
	@echo "Updating dependencies..."
	$(VENV_ACTIVATE) && $(PIP) list --outdated
	$(VENV_ACTIVATE) && $(PIP) install --upgrade -r $(REQUIREMENTS)
	@echo "Dependencies updated"

# Freeze dependencies
freeze: venv
	@echo "Freezing dependencies..."
	$(VENV_ACTIVATE) && $(PIP) freeze > requirements-frozen.txt
	@echo "Dependencies frozen to requirements-frozen.txt"

# Security scan
security: install-dev
	@echo "Running security scan..."
	$(VENV_ACTIVATE) && $(PIP) install safety
	$(VENV_ACTIVATE) && safety check --json
	@echo "Security scan complete"

# Help
help:
	@echo "Python Project Makefile"
	@echo "======================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make venv         - Create virtual environment"
	@echo "  make install      - Install project dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run          - Run the application"
	@echo "  make debug        - Run in debug mode"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checker"
	@echo "  make check        - Run all quality checks"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build        - Build distribution package"
	@echo "  make publish      - Publish to PyPI"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Generate documentation"
	@echo "  make serve-docs   - Serve documentation locally"
	@echo ""
	@echo "Database:"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Run migrations"
	@echo "  make db-seed      - Seed database"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make update-deps  - Update dependencies"
	@echo "  make freeze       - Freeze dependencies"
	@echo "  make security     - Run security scan"
	@echo ""
	@echo "Variables:"
	@echo "  PYTHON=$(PYTHON)"
	@echo "  VENV=$(VENV)"