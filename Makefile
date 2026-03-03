DC_FILE := docker-compose.yml
DC := docker-compose -f $(DC_FILE)

.PHONY: run up down build rebuild test lint clean install

run-crawl:
	poetry run python run_crawler.py crawl

run-search:
	poetry run python run_crawler.py search "$(QUERY)"

run-stats:
	poetry run python run_crawler.py stats

run-generate-samples:
	poetry run python run_crawler.py generate-samples

up:
	$(DC) up

up-detached:
	$(DC) up -d

down:
	$(DC) down

build:
	$(DC) build

rebuild:
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up

fix:
	poetry run ruff check . --fix

lint:
	poetry run ruff check .
	poetry run mypy .

format:
	poetry run ruff format .

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=app --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov

install:
	poetry install
	poetry run pre-commit install

help:
	@echo "Available commands:"
	@echo "  run-crawl           - Run crawler"
	@echo "  run-search QUERY=... - Search documents"
	@echo "  run-stats           - Show database statistics"
	@echo "  run-generate-samples - Generate test files"
	@echo "  up                  - Start Docker container"
	@echo "  down                - Stop Docker container"
	@echo "  build               - Build Docker image"
	@echo "  lint                - Run linters"
	@echo "  format              - Format code"
	@echo "  test                - Run tests"
	@echo "  clean               - Clean cache files"
	@echo "  install             - Install dependencies"
