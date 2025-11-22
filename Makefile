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
