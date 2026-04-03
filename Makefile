.PHONY: help install clean test lint format check-types check run-jupyter run-jupyterlab db-init db-reset kaggle-load setup quality security complexity docs pre-commit airflow-up airflow-down airflow-logs

help:
	@echo "📊 Insurance Analytics - Production Grade Monorepo"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make clean          - Clean build artifacts and cache"
	@echo "  make test           - Run tests with coverage"
	@echo "  make lint           - Run linters (flake8, pylint, ruff)"
	@echo "  make format         - Format code (black, isort)"
	@echo "  make check-types    - Run type checking (mypy)"
	@echo "  make quality        - Run code quality checks (bandit, radon, etc.)"
	@echo "  make security       - Run security analysis"
	@echo "  make complexity     - Run complexity analysis"
	@echo "  make docs           - Check and format documentation"
	@echo "  make pre-commit     - Run pre-commit hooks"
	@echo "  make quality-check  - Run comprehensive quality check script"
	@echo "  make check          - Run all checks (lint, type, test, quality)"
	@echo "  make run-jupyter    - Start Jupyter Notebook"
	@echo "  make run-jupyterlab - Start JupyterLab"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-reset       - Reset database"
	@echo "  make kaggle-load    - Download Kaggle dataset and load into database"
	@echo "  make setup          - Full setup (db + kaggle data)"
	@echo "  make airflow-up     - Start Airflow stack (webserver + scheduler)"
	@echo "  make airflow-down   - Stop Airflow stack"
	@echo "  make airflow-logs   - Tail Airflow scheduler logs"

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	pip install -e .[dev]
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
	find . -type d -name 'htmlcov' -delete
	find . -type d -name '.coverage' -delete
	find . -type f -name 'coverage.xml' -delete
	find . -type f -name 'junit-report.xml' -delete
	find . -type f -name 'pylint-report.txt' -delete
	find . -type f -name 'bandit-report.json' -delete
	@echo "✅ Cleaned"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --junitxml=junit-report.xml
	@echo "✅ Tests passed"

lint:
	@echo "🔍 Running linters..."
	flake8 src tests concepts
	ruff check src tests concepts
	pylint src tests concepts || true
	@echo "✅ Linting completed"

format:
	@echo "🪄 Formatting code..."
	isort src tests concepts --profile black
	black src tests concepts --line-length=100
	ruff format src tests concepts
	find src tests concepts -name "*.py" -exec docformatter --in-place --wrap-summaries=100 --wrap-descriptions=100 {} \;
	@echo "✅ Code formatted"

check-types:
	@echo "🔎 Type checking..."
	mypy src --strict
	@echo "✅ Type checking passed"

quality:
	@echo "📊 Running code quality analysis..."
	bandit -r src -c pyproject.toml
	radon cc src -a -nb
	radon mi src -nb
	xenon src --max-average A --max-modules A --max-absolute B
	cohesion -d src
	vulture src || true
	@echo "✅ Quality analysis completed"

security:
	@echo "🔒 Running security analysis..."
	bandit -r src -f txt
	safety check
	@echo "✅ Security analysis completed"

complexity:
	@echo "🧠 Running complexity analysis..."
	radon cc src --json | jq .
	radon mi src --json | jq .
	radon hal src
	@echo "✅ Complexity analysis completed"

docs:
	@echo "📚 Checking documentation..."
	pydocstyle src
	docformatter --check --wrap-summaries=100 --wrap-descriptions=100 src tests concepts
	@echo "✅ Documentation checks completed"

pre-commit:
	@echo "🔗 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks passed"

quality-check:
	@echo "🛡️  Running comprehensive quality check..."
	./check-quality.sh
	@echo "✅ Quality check completed"

check: lint check-types test quality
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

kaggle-load:
	@echo "📥 Downloading and loading Kaggle dataset..."
	python -m src.load --kaggle-config config/kaggle.yaml
	@echo "✅ Kaggle data loaded"

setup: install db-init kaggle-load
	@echo "✅ Full setup complete!"

airflow-up:
	@echo "🚀 Starting Airflow (webserver on http://localhost:8080)..."
	docker network create insurance-network 2>/dev/null || true
	docker compose -f airflow/docker-compose-airflow.yml up -d
	@echo "✅ Airflow started — login: admin / admin"

airflow-down:
	@echo "⏹️  Stopping Airflow..."
	docker compose -f airflow/docker-compose-airflow.yml down
	@echo "✅ Airflow stopped"

airflow-logs:
	docker compose -f airflow/docker-compose-airflow.yml logs -f airflow-scheduler
