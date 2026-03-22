.PHONY: help install clean test lint format check-types run-jupyter run-jupyterlab db-init db-reset data-gen load-data

help:
	@echo "📊 Insurance Analytics - Production Grade Monorepo"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make clean          - Clean build artifacts and cache"
	@echo "  make test           - Run tests with coverage"
	@echo "  make lint           - Run linters (pylint, flake8)"
	@echo "  make format         - Format code (black, isort)"
	@echo "  make check-types    - Run type checking (mypy)"
	@echo "  make check          - Run all checks (lint, type, test)"
	@echo "  make run-jupyter    - Start Jupyter Notebook"
	@echo "  make run-jupyterlab - Start JupyterLab"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-reset       - Reset database"
	@echo "  make data-gen       - Generate synthetic data"
	@echo "  make load-data      - Load data into database"
	@echo "  make setup          - Full setup (db + data)"

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.mypy_cache' -delete
	find . -type d -name '*.egg-info' -delete
	find . -type d -name 'dist' -delete
	find . -type d -name 'build' -delete
	@echo "✅ Cleaned"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "✅ Tests passed"

lint:
	@echo "🔍 Linting code..."
	flake8 src tests concepts --max-line-length=100
	pylint src tests concepts
	@echo "✅ Linting passed"

format:
	@echo "🪄 Formatting code..."
	isort src tests concepts --profile black
	black src tests concepts --line-length=100
	@echo "✅ Code formatted"

check-types:
	@echo "🔎 Type checking..."
	mypy src --strict
	@echo "✅ Type checking passed"

check: lint check-types test
	@echo "✅ All checks passed"

run-jupyter:
	@echo "📓 Starting Jupyter Notebook on http://localhost:8889"
	@echo "📝 Access: http://localhost:8889 (no password needed)"
	jupyter notebook --ip=0.0.0.0 --port=8889 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' notebooks/

run-jupyterlab:
	@echo "🧪 Starting JupyterLab on http://localhost:8888"
	@echo "📝 Access: http://localhost:8888 (no password needed)"
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' notebooks/

db-init:
	@echo "🗄️  Initializing database..."
	psql $$DATABASE_URL -f sql/ddl_create_tables.sql
	@echo "✅ Database initialized"

db-reset:
	@echo "🔄 Resetting database..."
	psql $$DATABASE_URL -c "DROP SCHEMA IF EXISTS insurance CASCADE;"
	psql $$DATABASE_URL -c "CREATE SCHEMA insurance;"
	psql $$DATABASE_URL -f sql/ddl_create_tables.sql
	@echo "✅ Database reset"

data-gen:
	@echo "🎲 Generating synthetic data..."
	mkdir -p data
	python -m src.generate_synthetic --rows-members 2000 --rows-providers 300 --rows-claims 5000 --out-dir data/
	@echo "✅ Data generated"

load-data:
	@echo "📥 Loading data into database..."
	python -m src.load --from-csv --members data/sample_members.csv --providers data/sample_providers.csv --claims data/sample_claims.csv
	@echo "✅ Data loaded"

setup: install db-init data-gen load-data
	@echo "✅ Full setup complete!"
