#!/bin/bash
# Master initialization script for Insurance Analytics dev container
# Runs after container creation to set up environment and database

set -euo pipefail

# Export DATABASE_URL from devcontainer config
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@db:5432/insurdb}"
export PYTHONPATH="${PYTHONPATH:-/workspaces/insurance-analytics-project}"

echo "=================================================="
echo "🚀 Insurance Analytics - Dev Container Setup"
echo "=================================================="

# Step 0: Ensure PostgreSQL client tools exist (psql, pg_isready).
# The app container now uses a prebuilt Python image for faster startup.
if ! command -v psql >/dev/null 2>&1 || ! command -v pg_isready >/dev/null 2>&1; then
    echo "🧰 Installing PostgreSQL client tools..."
    sudo apt-get update -y >/dev/null
    sudo apt-get install -y postgresql-client >/dev/null
fi

# Step 1: Ensure .gitconfig is a regular file, not a directory.
# VS Code Dev Containers copies the host ~/.gitconfig into the container; if
# the host path was accidentally created as a directory this step prevents Git
# from failing with "Is a directory" / "unexpected end of parent stream".
echo "🔧 Cleaning up git configuration..."
for _gcfg in "${HOME:-/root}/.gitconfig" /home/vscode/.gitconfig; do
    if [ -d "$_gcfg" ]; then
        rm -rf "$_gcfg"
        touch "$_gcfg"
    fi
done
unset _gcfg
git config --global --add safe.directory /workspaces/insurance-analytics-project || true

# Step 2: Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel >/dev/null
pip install -r requirements.txt
pip install -e .[dev]

# Step 2b: Install Apache Airflow (for DAG linting in pre-commit)
# Uses the official constraint file to prevent dependency conflicts
echo "🌊 Installing Apache Airflow (for linting)..."
AIRFLOW_VERSION=2.10.4
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.11.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}" || \
    echo "⚠️  Airflow install failed — DAG linting may show import errors"

# Airflow's constraint file downgrades SQLAlchemy to 1.x, which breaks pandas 2.x.
# Re-pin SQLAlchemy to the version required by requirements.txt.
echo "🔧 Re-pinning SQLAlchemy>=2.0 (overrides Airflow constraint)..."
pip install "SQLAlchemy>=2.0.0,<3.0.0" --upgrade --quiet || \
    echo "⚠️  SQLAlchemy re-pin failed"

# Step 3: Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
pre-commit install --install-hooks || echo "⚠️  Pre-commit setup failed, continuing..."

# Step 4: Run database initialization
echo ""
if bash .devcontainer/init-db.sh; then
    echo "✅ Database initialization complete"
else
    echo "⚠️  Database initialization failed (DB may not be ready yet)."
    echo "    Run 'make setup' inside the container once PostgreSQL is available."
fi
