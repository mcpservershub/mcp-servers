.PHONY: help install dev test clean docker-build docker-run format lint

help:
	@echo "Available commands:"
	@echo "  make install      Install the package"
	@echo "  make dev          Install with development dependencies"
	@echo "  make test         Run tests"
	@echo "  make clean        Clean build artifacts"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run Docker container"
	@echo "  make format       Format code with black"
	@echo "  make lint         Lint code with ruff"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=ctags_mcp --cov-report=html --cov-report=term

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.tags" -delete
	find . -type f -name "tags" ! -path "./tests/fixtures/*" -delete

docker-build:
	docker build -t universal-ctags-mcp-server:latest .

docker-run:
	docker run -it --rm -v $(PWD):/workspace universal-ctags-mcp-server:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

format:
	black src/ tests/

lint:
	ruff check src/ tests/

quality: format lint

run:
	python -m ctags_mcp.server

inspector:
	./scripts/test_with_inspector.sh