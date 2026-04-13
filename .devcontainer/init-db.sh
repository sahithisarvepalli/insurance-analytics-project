#!/bin/bash
# Database initialization script for Insurance Analytics dev container
# This script runs after container creation to set up the database

set -euo pipefail

echo "=================================================="
echo "🚀 Insurance Analytics - Database Initialization"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    error "DATABASE_URL environment variable not set"
    exit 1
fi

# Step 1: Wait for PostgreSQL
status "🔌 Waiting for PostgreSQL..."
max_attempts=30
attempt=0
while ! pg_isready -h db -p 5432 -U postgres &>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        error "PostgreSQL failed to start after $max_attempts attempts"
        exit 1
    fi
    echo -n "."
    sleep 1
done
success "PostgreSQL is ready"

# Step 2: Create schema
status "📚 Creating database schema..."
SCHEMA_OUTPUT=$(psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS insurance;" 2>&1)
SCHEMA_EXIT=$?

if [ $SCHEMA_EXIT -ne 0 ]; then
    error "Failed to create schema"
    echo "Error details:"
    echo "$SCHEMA_OUTPUT"
    exit 1
fi
success "Schema created/verified"

# Step 3: Create tables
status "🗄️  Creating tables..."
DDL_OUTPUT=$(psql "$DATABASE_URL" -f src/sql/ddl_create_tables.sql 2>&1)
DDL_EXIT=$?

if [ $DDL_EXIT -eq 0 ]; then
    success "Tables created/verified"
else
    error "Failed to create tables"
    echo "Error details:"
    echo "$DDL_OUTPUT"
    exit 1
fi

# Step 4: Check if data already exists
status "📊 Checking for existing data..."
row_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM insurance.claim;" 2>/dev/null || echo "0")

if [ "$row_count" -gt 0 ]; then
    success "Found $row_count existing claims - skipping data generation"
else
    # Step 5: Generate synthetic data
    status "🎲 Generating synthetic data..."
    mkdir -p data notebooks/outputs

    GEN_OUTPUT=$(python -m src.generate_synthetic \
        --rows-members 2000 \
        --rows-providers 300 \
        --rows-claims 5000 \
        --out-dir data/ 2>&1)
    GEN_EXIT=$?

    if [ $GEN_EXIT -eq 0 ]; then
        success "Generated synthetic data: 2000 members, 300 providers, 5000 claims"
    else
        error "Failed to generate synthetic data"
        echo "Error details:"
        echo "$GEN_OUTPUT"
        exit 1
    fi

    # Step 6: Load data into database
    status "📥 Loading data into database..."
    LOAD_OUTPUT=$(python -m src.load \
        --from-csv \
        --members data/sample_members.csv \
        --providers data/sample_providers.csv \
        --claims data/sample_claims.csv 2>&1)
    LOAD_EXIT=$?

    if [ $LOAD_EXIT -eq 0 ]; then
        success "Data loaded successfully"
    else
        error "Failed to load data into database"
        echo "Error details:"
        echo "$LOAD_OUTPUT"
        exit 1
    fi
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Database is ready to use:"
echo "  - Schema: insurance"
echo "  - Tables: member, provider, claim"
echo "  - Claims loaded: $row_count"
echo ""
echo "To access JupyterLab:"
echo "  make run-jupyterlab"
echo ""
