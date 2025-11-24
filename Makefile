<<<<<<< HEAD
.PHONY: help install install-dev test lint format clean docker-build docker-run deploy

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '$(BLUE)Legion AI System - Development Commands$(NC)'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================
# Installation
# ============================================

install: ## Install production dependencies
	@echo '$(BLUE)Installing production dependencies...$(NC)'
	pip install --upgrade pip
	pip install -r requirements.txt
	playwright install chromium
	@echo '$(GREEN)✓ Installation complete$(NC)'

install-dev: ## Install development dependencies
	@echo '$(BLUE)Installing development dependencies...$(NC)'
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pre-commit pytest-cov black ruff mypy bandit
	playwright install chromium firefox webkit
	pre-commit install
	@echo '$(GREEN)✓ Development setup complete$(NC)'

# ============================================
# Code Quality
# ============================================

lint: ## Run all linters
	@echo '$(BLUE)Running linters...$(NC)'
	@echo '$(YELLOW)1. Ruff linting...$(NC)'
	ruff check src/ tests/
	@echo '$(YELLOW)2. Type checking with mypy...$(NC)'
	mypy src/legion
	@echo '$(YELLOW)3. Security scan with bandit...$(NC)'
	bandit -r src/ -c pyproject.toml
	@echo '$(GREEN)✓ All linting passed$(NC)'

format: ## Auto-format code
	@echo '$(BLUE)Formatting code...$(NC)'
	black src/ tests/
	ruff check --fix src/ tests/
	@echo '$(GREEN)✓ Code formatted$(NC)'

pre-commit: ## Run pre-commit on all files
	@echo '$(BLUE)Running pre-commit hooks...$(NC)'
	pre-commit run --all-files

# ============================================
# Testing
# ============================================

test: ## Run all tests
	@echo '$(BLUE)Running tests...$(NC)'
	pytest tests/ -v --cov=src/legion --cov-report=html --cov-report=term-missing
	@echo '$(GREEN)✓ Tests passed$(NC)'

test-unit: ## Run unit tests only
	@echo '$(BLUE)Running unit tests...$(NC)'
	pytest tests/ -v -m "unit and not integration" --cov=src/legion

test-integration: ## Run integration tests only
	@echo '$(BLUE)Running integration tests...$(NC)'
	pytest tests/ -v -m "integration" --cov=src/legion

test-watch: ## Run tests in watch mode
	@echo '$(BLUE)Running tests in watch mode...$(NC)'
	ptw -- tests/ -v

coverage: ## Generate coverage report
	@echo '$(BLUE)Generating coverage report...$(NC)'
	pytest tests/ --cov=src/legion --cov-report=html
	@echo '$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)'

# ============================================
# Docker
# ============================================

docker-build: ## Build Docker image
	@echo '$(BLUE)Building Docker image...$(NC)'
	docker build -t legion:2.0 -t legion:latest .
	@echo '$(GREEN)✓ Docker image built$(NC)'

docker-run: ## Run Docker container
	@echo '$(BLUE)Running Docker container...$(NC)'
	docker run -d --name legion-ai \
		--env-file .env \
		-p 8001:8001 \
		-p 9090:9090 \
		-v legion-data:/data \
		legion:latest
	@echo '$(GREEN)✓ Container started$(NC)'

docker-stop: ## Stop Docker container
	@echo '$(BLUE)Stopping Docker container...$(NC)'
	docker stop legion-ai
	docker rm legion-ai
	@echo '$(GREEN)✓ Container stopped$(NC)'

docker-compose-up: ## Start all services with docker-compose
	@echo '$(BLUE)Starting services with docker-compose...$(NC)'
	docker-compose up -d
	@echo '$(GREEN)✓ Services started$(NC)'
	@echo '$(YELLOW)MCP Server: http://localhost:8001$(NC)'
	@echo '$(YELLOW)Prometheus: http://localhost:9091$(NC)'
	@echo '$(YELLOW)Grafana: http://localhost:3000 (admin/legion)$(NC)'

docker-compose-down: ## Stop all services
	@echo '$(BLUE)Stopping services...$(NC)'
	docker-compose down
	@echo '$(GREEN)✓ Services stopped$(NC)'

docker-logs: ## View Docker logs
	docker-compose logs -f legion

# ============================================
# Development
# ============================================

run: ## Run Legion locally
	@echo '$(BLUE)Starting Legion AI System...$(NC)'
	python -m src.main

run-mcp: ## Run MCP server
	@echo '$(BLUE)Starting MCP server...$(NC)'
	python -m src.legion.mcp.server

shell: ## Open Python shell with Legion loaded
	@echo '$(BLUE)Opening Python shell...$(NC)'
	python -i -c "from src.legion import LegionCore; core = LegionCore(); print('Legion loaded. Use: core')"

# ============================================
# Cleaning
# ============================================

clean: ## Remove build artifacts and cache
	@echo '$(BLUE)Cleaning build artifacts...$(NC)'
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	@echo '$(GREEN)✓ Cleaned$(NC)'

clean-docker: ## Remove Docker images and volumes
	@echo '$(BLUE)Cleaning Docker resources...$(NC)'
	docker-compose down -v
	docker rmi legion:2.0 legion:latest 2>/dev/null || true
	@echo '$(GREEN)✓ Docker cleaned$(NC)'

# ============================================
# Documentation
# ============================================

docs: ## Generate API documentation
	@echo '$(BLUE)Generating documentation...$(NC)'
	# TODO: Add sphinx or mkdocs
	@echo '$(YELLOW)Documentation generation not yet implemented$(NC)'

# ============================================
# CI/CD
# ============================================

ci: lint test ## Run CI pipeline locally
	@echo '$(GREEN)✓ CI checks passed$(NC)'

build: clean install test ## Full build pipeline
	@echo '$(GREEN)✓ Build complete$(NC)'

# ============================================
# Utilities
# ============================================

env-check: ## Check environment configuration
	@echo '$(BLUE)Checking environment...$(NC)'
	@python -c "import sys; print(f'Python: {sys.version}')"
	@python -c "import playwright; print('Playwright: ✓')"
	@python -c "import openai; print('OpenAI: ✓')"
	@python -c "import supabase; print('Supabase: ✓')"
	@echo '$(GREEN)✓ Environment OK$(NC)'

version: ## Show version
	@python -c "from src.legion import __version__; print(f'Legion v{__version__}')"
=======
.PHONY: help install install-dev lint format test test-unit test-integration coverage clean docker-build docker-run docker-compose-up docker-compose-down docker-logs run run-mcp shell ci build

help:
	@echo "Legion AI Development Commands"
	@echo "================================"
	@echo "make install           - Install production dependencies"
	@echo "make install-dev       - Install dev dependencies + pre-commit"
	@echo "make lint              - Run linting (Ruff + Mypy + Bandit)"
	@echo "make format            - Auto-format code (Black + Ruff)"
	@echo "make test              - Run all tests with coverage"
	@echo "make test-unit         - Run unit tests only"
	@echo "make test-integration  - Run integration tests"
	@echo "make coverage          - Generate coverage report"
	@echo "make clean             - Clean cache and build artifacts"
	@echo "make docker-build      - Build Docker image"
	@echo "make docker-run        - Run Docker container"
	@echo "make docker-compose-up - Start full stack with docker-compose"
	@echo "make docker-compose-down - Stop docker-compose"
	@echo "make run               - Run Legion locally"
	@echo "make ci                - Run full CI pipeline"
	@echo "make build             - Clean + install + test"

install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt
	pre-commit install

lint:
	ruff check src/ tests/ examples/
	mypy src/ --strict
	bandit -r src/

format:
	black src/ tests/ examples/
	ruff check --fix src/ tests/ examples/

test:
	pytest -v --cov=src/legion --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

coverage:
	pytest --cov=src/legion --cov-report=html
	@echo "Coverage report generated: htmlcov/index.html"

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

docker-build:
	docker build -t legion:latest -t legion:2.0.0 .

docker-run:
	docker run -d -p 8001:8001 -p 9090:9090 --name legion-app legion:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

run:
	python -m legion.mcp

run-mcp:
	python -m legion.mcp --port 8001

shell:
	python

ci: clean install-dev lint test
	@echo "CI pipeline completed successfully"

build: clean install test
	@echo "Build completed successfully"
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
