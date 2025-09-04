# Makefile for NFG Analytics Orchestrator

.PHONY: setup test run docker-build docker-run clean

# Setup environment and install dependencies
setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

# Run tests
test:
	pytest

# Run the application
run:
	python run.py

# Build Docker image
docker-build:
	docker build -t nfg-orchestrator .

# Run Docker container
docker-run:
	docker run -p 8000:8000 --env-file .env nfg-orchestrator

# Run with Docker Compose
docker-up:
	docker-compose up -d

# Stop Docker Compose
docker-down:
	docker-compose down

# Clean up temporary files
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
