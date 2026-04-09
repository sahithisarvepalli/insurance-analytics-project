.PHONY: help install clean test lint format check-types check run-jupyter run-jupyterlab db-init db-reset kaggle-load setup dw-load dashboard open-dashboard serve-dashboard pipeline-local pipeline-client pipeline-all quality security complexity docs pre-commit airflow-up airflow-down airflow-logs

help:
	@echo "📊 Insurance Analytics - Production Grade Monorepo"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make clean          - Clean build artifacts and cache"
	@echo "  make test           - Run tests with coverage"
	@echo "  make lint           - Run linters (ruff, pylint)"
	@echo "  make format         - Format code (ruff format + ruff check --fix)"
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
	@echo "  make kaggle-load    - Load Kaggle dataset into database (uses cached CSV — no credentials needed)"
	@echo "  make setup          - Full setup (db + kaggle data)"
	@echo "  make dw-load            - Load DuckDB data warehouse (outputs/insurance_dw.duckdb)"
	@echo "  make dashboard          - Generate interactive HTML dashboard (outputs/dashboard.html)"
	@echo "  make serve-dashboard    - Serve dashboard at http://localhost:8000 — VS Code 'Open in Browser' goes directly to charts"
	@echo "  make open-dashboard     - Generate dashboard and open it in the default browser"
	@echo "  make pipeline-local     - Run full local pipeline: transform -> model -> DW -> dashboard"
	@echo "  make pipeline-client    - Run pipeline for one client: CLIENT_CONFIG=... CLIENT_ID=... CLIENT_NAME=..."
	@echo "  make pipeline-all       - Run pipelines for all clients, serve combined landing page"
	@echo "  make airflow-up         - Start Airflow stack (webserver + scheduler)"
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
	rm -rf build/
	find . -type f -name 'pylint-report.txt' -delete
	find . -type f -name 'bandit-report.json' -delete
	@echo "✅ Cleaned"

test:
	@echo "🧪 Running tests..."
	mkdir -p build/reports
	pytest tests/ -v --cov=src --cov-report=html:build/reports/htmlcov --cov-report=term-missing --cov-report=xml:build/reports/coverage.xml --junitxml=build/reports/junit-report.xml
	@echo "✅ Tests passed"

lint:
	@echo "🔍 Running linters..."
	ruff check src tests examples/concepts
	pylint src tests examples/concepts || true
	@echo "✅ Linting completed"

format:
	@echo "🪄 Formatting code..."
	ruff format src tests examples/concepts
	ruff check --fix src tests examples/concepts
	find src tests examples/concepts -name "*.py" -exec docformatter --in-place --wrap-summaries=100 --wrap-descriptions=100 {} \;
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
	docformatter --check --wrap-summaries=100 --wrap-descriptions=100 src tests examples/concepts
	@echo "✅ Documentation checks completed"

pre-commit:
	@echo "🔗 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks passed"

quality-check:
	@echo "🛡️  Running comprehensive quality check..."
	./scripts/check_quality.sh
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
	psql $$DATABASE_URL -f src/sql/ddl_create_tables.sql
	@echo "✅ Database initialized"

db-reset:
	@echo "🔄 Resetting database..."
	psql $$DATABASE_URL -c "DROP SCHEMA IF EXISTS insurance CASCADE;"
	psql $$DATABASE_URL -c "CREATE SCHEMA insurance;"
	psql $$DATABASE_URL -f src/sql/ddl_create_tables.sql
	@echo "✅ Database reset"

kaggle-load:
	@echo "📥 Loading Kaggle dataset (1,338 claims — uses cached CSV, no credentials needed)..."
	python -m src.load --kaggle-config config/kaggle.yaml
	@echo "✅ Kaggle data loaded — run 'make pipeline-local' to generate the dashboard"

setup: install db-init kaggle-load
	@echo "✅ Full setup complete!"

dw-load:
	@echo "🏛️  Loading DuckDB data warehouse..."
	python -m src.dw_load
	@echo "✅ DW loaded → outputs/insurance_dw.duckdb"

dashboard:
	@echo "📊 Generating interactive HTML dashboard..."
	pip install -q -r requirements-dashboard.txt
	python -m src.generate_html_report \
		--output-dir outputs \
		--client-name "Insurance Analytics" \
		--out outputs/dashboard.html
	@echo "✅ Dashboard → outputs/dashboard.html"

open-dashboard: dashboard
	@echo "🌐 Opening dashboard in browser..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open outputs/dashboard.html; \
	elif command -v open >/dev/null 2>&1; then \
		open outputs/dashboard.html; \
	else \
		echo "Dashboard saved to outputs/dashboard.html — open it manually in your browser."; \
	fi

serve-dashboard:
	@echo "📊 Dashboard → http://localhost:8000  (VS Code 'Open in Browser' goes directly to charts)"
	@echo "   Press Ctrl+C to stop."
	python scripts/serve_dashboard.py --dir outputs

pipeline-local:
	@echo "🚀 Running full local pipeline (uses data already in PostgreSQL)..."
	@echo "   Tip: run 'make kaggle-load' first to load the Kaggle dataset."
	python -m src.transform --output-dir outputs
	python -m src.model     --output-dir outputs
	python -m src.dw_load   --output-dir outputs --dw-path outputs/insurance_dw.duckdb
	$(MAKE) dashboard
	@echo "✅ Local pipeline complete — run 'make serve-dashboard' to view results."

# Run the full pipeline for a single client.  Accepts variables:
#   CLIENT_CONFIG    — path to the client CSV or kaggle YAML config
#   CLIENT_ID        — short id used as the output sub-folder name
#   CLIENT_NAME      — human-readable name shown on the dashboard
#   KAGGLE_DATASET   — (optional) override active_dataset in kaggle.yaml
# Examples:
#   make pipeline-client CLIENT_CONFIG=config/clients/client_a.yaml CLIENT_ID=client_a CLIENT_NAME="Acme Health Plans"
#   make pipeline-client CLIENT_CONFIG=config/kaggle.yaml KAGGLE_DATASET=insurance_claims CLIENT_ID=client_b CLIENT_NAME="MedTrust Group"
pipeline-client:
	@echo "🚀 [$(CLIENT_ID)] Loading data..."
	@if echo "$(CLIENT_CONFIG)" | grep -q 'clients/'; then \
		python -m src.load --client-config $(CLIENT_CONFIG); \
	else \
		python -m src.load --kaggle-config $(CLIENT_CONFIG) $(if $(KAGGLE_DATASET),--kaggle-dataset $(KAGGLE_DATASET),); \
	fi
	@echo "🚀 [$(CLIENT_ID)] Running transform → model → DW → dashboard..."
	python -m src.transform --output-dir outputs/$(CLIENT_ID)
	python -m src.model     --output-dir outputs/$(CLIENT_ID)
	python -m src.dw_load   --output-dir outputs/$(CLIENT_ID) --dw-path outputs/$(CLIENT_ID)/insurance_dw.duckdb
	pip install -q -r requirements-dashboard.txt
	python -m src.generate_html_report \
		--output-dir outputs/$(CLIENT_ID) \
		--client-name "$(CLIENT_NAME)" \
		--out outputs/$(CLIENT_ID)/dashboard.html
	@echo "✅ [$(CLIENT_ID)] Done → outputs/$(CLIENT_ID)/dashboard.html"

pipeline-all:
	@echo "🚀 Running pipeline for all clients..."
	$(MAKE) pipeline-client CLIENT_CONFIG=config/kaggle.yaml KAGGLE_DATASET=insurance_charges    CLIENT_ID=client_a CLIENT_NAME="Acme Health Plans"
	$(MAKE) pipeline-client CLIENT_CONFIG=config/kaggle.yaml KAGGLE_DATASET=healthcare_admissions CLIENT_ID=client_b CLIENT_NAME="MedTrust Group"
	@echo "✅ All pipelines complete — run 'make serve-dashboard' to view all dashboards."

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
