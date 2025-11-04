# Makefile for AI Recruiter Agent Microservice
# Simplifies common development tasks

.PHONY: help install test run clean lint format docker-build docker-run deploy

help:  ## Show this help message
	@echo "AI Recruiter Agent - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

test:  ## Run all tests
	pytest test_microservice.py -v

test-cov:  ## Run tests with coverage report
	pytest test_microservice.py -v --cov=. --cov-report=html --cov-report=term
	@echo "\nCoverage report generated in htmlcov/index.html"

run:  ## Run the microservice locally
	python main.py

example:  ## Run example usage script
	python example_usage.py

lint:  ## Run linter (flake8)
	flake8 *.py --max-line-length=100 --exclude=venv,env

format:  ## Format code with black
	black *.py

type-check:  ## Run type checking with mypy
	mypy *.py --ignore-missing-imports

clean:  ## Clean up generated files
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:  ## Build Docker image
	docker build -t ai-recruiter-agent:latest .

docker-run:  ## Run Docker container locally
	docker run -p 8080:8080 \
		-e GOOGLE_API_KEY=${GOOGLE_API_KEY} \
		-e ENVIRONMENT=development \
		ai-recruiter-agent:latest

docker-test:  ## Test Docker container
	docker run --rm ai-recruiter-agent:latest pytest test_microservice.py -v

deploy:  ## Deploy to Google Cloud Run (requires GCP setup)
	@read -p "Enter GCP Project ID: " project_id; \
	read -p "Enter GCP Region [us-central1]: " region; \
	region=$${region:-us-central1}; \
	./deploy.sh $$project_id $$region

dev:  ## Run in development mode with auto-reload
	uvicorn main:app --reload --port 8080

all: clean format lint test  ## Run clean, format, lint, and test
