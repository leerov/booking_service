.PHONY: dev test lint

dev:
	@echo "Starting development environment..."
	docker-compose up --build

test:
	@echo "Running tests..."
	pytest -v --tb=short

lint:
	@echo "Running linters..."
	flake8 app tests
	black --check app tests
	isort --check-only app tests

fmt:
	@echo "Formatting code..."
	black app tests
	isort app tests