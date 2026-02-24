DC_FILE := docker-compose.yml
DC := docker-compose -f $(DC_FILE)

.PHONY: run up down build rebuild test lint clean

# run:	
# 	poetry run python run_pipeline.py

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

lint:
	poetry run ruff check .
	poetry run mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +