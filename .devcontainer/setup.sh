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

# Step 1: Clean up .gitconfig if it's a directory
echo "🔧 Cleaning up git configuration..."
rm -rf /home/vscode/.gitconfig
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

# Airflow's constraint file downgrades SQLAlchemy, packaging, pathspec, and dill,
# which conflict with the project's requirements. Re-pin them back after Airflow install.
echo "🔧 Re-pinning packages downgraded by Airflow constraints..."
pip install \
    "SQLAlchemy>=2.0.0,<3.0.0" \
    "packaging>=24.0" \
    "pathspec>=1.0.0" \
    "dill>=0.3.6" \
    --upgrade --quiet || \
    echo "⚠️  Re-pin failed"

# Step 3: Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
pre-commit install --install-hooks || echo "⚠️  Pre-commit setup failed, continuing..."

# Step 4: Run database initialization
echo ""
bash .devcontainer/init-db.sh
