# Engels Development Makefile

.PHONY: help install dev test lint typecheck clean docker-up docker-down db-migrate

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -e ".[dev]"
	cd frontend && npm install

dev: ## Start development environment
	docker compose up -d db redis ollama
	python -m uvicorn backend.src.api:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=backend/src --cov-report=html --cov-report=term

lint: ## Run linters
	ruff check backend/src tests
	black --check backend/src tests

format: ## Format code
	ruff check backend/src tests --fix
	black backend/src tests

typecheck: ## Run type checking
	mypy backend/src tests

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

docker-up: ## Start all Docker containers
	docker compose up -d

docker-down: ## Stop all Docker containers
	docker compose down

docker-logs: ## Show container logs
	docker compose logs -f

db-migrate: ## Run database migrations
	@echo "Database schema is applied via init.sql on container startup"
	@echo "For manual migrations, use Alembic or custom scripts"

setup-ollama: ## Pull required Ollama models
	docker exec engels-ollama ollama pull qwen2.5:7b
	docker exec engels-ollama ollama pull llama3:8b

reset-db: ## Reset database (WARNING: deletes all data)
	docker compose down -v postgres_data
	docker compose up -d db

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

backend-worker: ## Start Celery worker
	celery -A backend.src.celery_app worker --loglevel=info -Q local_ollama,mcp_external

backend-flower: ## Start Flower monitoring UI
	celery -A backend.src.celery_app flower --port=5555

security-check: ## Run security checks
	@echo "Running security audit..."
	pip-audit || true
	npm audit --prefix frontend || true
