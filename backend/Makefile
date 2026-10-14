.PHONY: help install run lint type-check test migrate build-image clean

help:
	@echo "Findr Backend Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies with uv"
	@echo ""
	@echo "Development:"
	@echo "  make run            Start FastAPI server (localhost:8000)"
	@echo "  make lint           Run ruff linter and formatter"
	@echo "  make type-check     Run mypy type checker"
	@echo "  make test           Run pytest test suite"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run Alembic migrations"
	@echo "  make migrate-create Create a new migration"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove cache and build artifacts"

install:
	@echo "Installing dependencies with uv..."
	uv sync

run:
	@echo "Starting FastAPI development server..."
	uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	@echo "Running ruff linter and formatter..."
	uv run ruff check --fix src tests
	uv run ruff format src tests

type-check:
	@echo "Running mypy type checker..."
	uv run mypy src tests

test:
	@echo "Running pytest..."
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	@echo "Running unit tests only..."
	uv run pytest tests/unit -v

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration -v -m integration

migrate:
	@echo "Running Alembic migrations..."
	uv run alembic upgrade head

migrate-create:
	@echo "Creating a new migration..."
	@read -p "Enter migration description: " desc; \
	uv run alembic revision --autogenerate -m "$$desc"

clean:
	@echo "Cleaning up cache and build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleanup complete"
