#!/bin/bash
# Comprehensive code quality check script
# Run all linting, formatting, and quality checks

set -euo pipefail

echo "=================================================="
echo "🛡️  Insurance Analytics - Code Quality Check"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    error "pyproject.toml not found. Run from project root."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
status "Python version: $PYTHON_VERSION"

# Check if dependencies are installed
status "Checking dependencies..."
if ! python -c "import ruff, mypy, bandit, radon" >/dev/null 2>&1; then
    error "Code quality dependencies not installed. Run: pip install -e .[dev]"
    exit 1
fi
success "Dependencies OK"

echo ""

# 1. Format checking
status "Checking code formatting..."
if ruff format --check --diff src tests examples/concepts >/dev/null 2>&1; then
    success "Ruff formatting OK"
else
    error "Code needs formatting. Run: make format"
    ruff format --check --diff src tests examples/concepts || true
fi

echo ""

# 2. Linting
status "Running linters..."
if ruff check src tests examples/concepts >/dev/null 2>&1; then
    success "Ruff linting OK"
else
    warning "Ruff issues found (may be auto-fixable with: ruff check --fix)"
    ruff check src tests examples/concepts || true
fi

if pylint src tests examples/concepts >/dev/null 2>&1; then
    success "Pylint OK"
else
    warning "Pylint issues found"
    pylint src tests examples/concepts || true
fi

echo ""

# 3. Type checking
status "Running type checking..."
if mypy src >/dev/null 2>&1; then
    success "Type checking OK"
else
    error "Type checking failed"
    mypy src || true
fi

echo ""

# 4. Security scanning
status "Running security analysis..."
if bandit -r src -c pyproject.toml >/dev/null 2>&1; then
    success "Security scan OK"
else
    warning "Security issues found"
    bandit -r src -c pyproject.toml || true
fi

echo ""

# 5. Complexity analysis
status "Running complexity analysis..."
if radon cc src -a -nb >/dev/null 2>&1; then
    success "Complexity analysis OK"
else
    warning "High complexity detected"
    radon cc src -a -nb || true
fi

if radon mi src -nb >/dev/null 2>&1; then
    success "Maintainability index OK"
else
    warning "Low maintainability detected"
    radon mi src -nb || true
fi

echo ""

# 6. Documentation checks
status "Checking documentation..."
if pydocstyle src >/dev/null 2>&1; then
    success "Documentation style OK"
else
    warning "Documentation style issues"
    pydocstyle src || true
fi

echo ""

# 7. Dead code detection
status "Checking for dead code..."
if vulture src >/dev/null 2>&1; then
    success "No dead code detected"
else
    warning "Potential dead code found"
    vulture src || true
fi

echo ""

# Summary
echo "=================================================="
echo "✅ Code quality check completed!"
echo ""
echo "Quick fixes:"
echo "  make format     # Auto-format code"
echo "  make lint       # Run all linters"
echo "  make check      # Run full quality suite"
echo "=================================================="
