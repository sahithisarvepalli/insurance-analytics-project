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

# Step 3: Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
pre-commit install --install-hooks || echo "⚠️  Pre-commit setup failed, continuing..."

# Step 4: Run database initialization
echo ""
bash .devcontainer/init-db.sh
