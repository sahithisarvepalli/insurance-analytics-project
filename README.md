# 📊 Insurance Analytics – Production Grade Monorepo

Modern, end-to-end **insurance analytics** project using **Python 3.11 + PostgreSQL 15**. Mirrors real-world SAS workflows with synthetic data generation, ETL pipelines, KPI aggregation, ML modeling, and Excel reporting. Includes interactive Jupyter notebooks, comprehensive test coverage, and GitHub Actions CI/CD.

**Quick Access:**
- 🚀 **Quick Start**: [Local Setup](#-quick-start--local-setup-without-dev-container) | [Dev Container](#-dev-container-recommended-for-teams)
- 📓 **Notebooks**: [notebooks/README.md](notebooks/README.md) | `make run-jupyterlab`
- 🧠 **Learning**: [concepts/README.md](concepts/README.md) – 11 learning modules
- 🎯 **Make Commands**: `make help` for all available tasks

---

## ✨ Key Features

✅ **End-to-End Data Pipeline**
- Synthetic members/providers/claims data generation  
- CSV → Database loading via SQLAlchemy + pandas
- Data transformations, joins, and KPI aggregation

✅ **Interactive Notebooks**
- Jupyter & JupyterLab support  
- Data exploration and visualization
- Model development and testing

✅ **Machine Learning**
- High-cost claimant classification model
- Feature engineering & model evaluation
- Export predictions to database

✅ **Professional Reporting**
- Multi-sheet Excel workbooks with formatting
- Charts, KPI dashboards, summary statistics

✅ **Production Ready**
- PostgreSQL with schema and indexes
- Comprehensive pytest test suite
- Black/flake8/isort code quality checks
- GitHub Actions CI/CD pipeline
- Full type hints with mypy

✅ **Developer Experience**
- Dev Container with auto-setup
- Makefile for all common tasks
- Detailed documentation and examples
- SAS → Python comparison examples

---

## 🗂 Repository Structure

```
insurance-analytics-project/
│
├── 📋 ROOT FILES
├── Makefile                        # All tasks: setup, test, lint, jupyter, etc.
├── requirements.txt                # Python dependencies (50+ packages)
├── .env.example                    # Database configuration template
├── LICENSE                         # MIT License
│
├── 🔧 CONFIGURATION
├── .devcontainer/
│   ├── devcontainer.json          # VS Code dev container config
│   └── docker-compose.yml         # PostgreSQL + services
├── .github/workflows/              # GitHub Actions CI/CD
├── config/
│   └── db.yaml                    # Database settings template
│
├── 📦 SOURCE CODE (Main Application)
├── src/
│   ├── __init__.py
│   ├── generate_synthetic.py      # Create realistic claims data
│   ├── load.py                    # CSV → Database loading
│   ├── transform.py               # Data transformations & KPIs
│   ├── model.py                   # ML model training & prediction
│   ├── report.py                  # Excel report generation
│   ├── seed.py                    # Database seeding utility
│   ├── utils.py                   # Shared utilities & DB connections
│
├── 🗄️ DATABASE
├── sql/
│   ├── ddl_create_tables.sql      # Schema definition (members, claims, etc.)
│   └── kpi_queries.sql            # SQL templates for analytics
│
├── 📚 DATA & OUTPUTS
├── data/                          # Generated & sample CSV files
│   ├── sample_members.csv         # Member demographics
│   ├── sample_providers.csv       # Healthcare providers
│   └── sample_claims.csv          # Insurance claims records
├── outputs/                       # Generated reports & metrics
│   ├── insurance_summary.xlsx     # Excel reports with charts
│   ├── kpis.csv                   # Aggregated KPIs
│   └── model_metrics.txt          # Model performance metrics
│
├── 📓 JUPYTER NOTEBOOKS
├── notebooks/
│   ├── README.md                  # [How to use notebooks]
│   ├── 01_exploratory_analysis/   # Data exploration
│   ├── 02_feature_engineering/    # Feature creation
│   ├── 03_modeling/               # Model development
│   ├── 04_reporting/              # Dashboard generation
│   └── outputs/                   # Notebook artifacts
│
├── 🎓 LEARNING MODULES
├── concepts/                      # 11 foundational Python/data modules
│   ├── README.md                  # [Learning path guide]
│   ├── 01_argparse_basics.py      # CLI argument parsing
│   ├── 02_csv_read_write.py       # CSV operations
│   ├── 03_db_connection.py        # Database connectivity
│   ├── 04_pandas_transform.py     # Data transformation
│   ├── 05_synthetic_data.py       # Fake data generation
│   ├── 06_ml_basics.py            # ML fundamentals
│   ├── 07_logging.py              # Application logging
│   ├── 08_config_loading.py       # YAML/config management
│   ├── 09_excel_report.py         # Report generation
│   ├── 10_testing_basics.py       # Unit testing
│   └── 11_date_handling.py        # Date/time utilities
│
├── 📖 REFERENCE EXAMPLES
├── sas-python-examples/           # SAS → Python translations
│   ├── sas/
│   │   └── employees_analysis.sas # Sample SAS code
│   └── python/
│       ├── employees_analysis.py  # Python equivalent
│       └── sample_debug.py        # Debugging techniques
│
├── 🧪 TESTS
├── tests/
│   ├── test_db.py                 # Database connectivity tests
│   └── (more tests)
│
└── 📄 DOCUMENTATION
├── docs/
│   ├── git.md                     # Git workflow guide
│   └── (more docs)
```

---

## 🚀 Quick Start – Local Setup (Without Dev Container)

Fastest way to get running locally:

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Git

### Steps

**1. Clone & Navigate**
```bash
git clone <repo-url>
cd insurance-analytics-project
```

**2. Install Dependencies**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Start PostgreSQL** (using Docker)
```bash
docker run --name insurdb \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=insurdb \
  -p 5432:5432 -d postgres:15
```

**4. Configure Database**
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/insurdb
# On Windows: set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/insurdb

# Create schema
psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS insurance;"
psql "$DATABASE_URL" -f sql/ddl_create_tables.sql
```

**5. Generate & Load Data**
```bash
python -m src.generate_synthetic --rows-members 2000 --rows-providers 300 --rows-claims 5000 --out-dir data/
python -m src.load --from-csv --members data/sample_members.csv --providers data/sample_providers.csv --claims data/sample_claims.csv
```

**6. Run the Pipeline**
```bash
python -m src.transform          # KPI calculations
python -m src.model             # Train ML model
python -m src.report --out outputs/insurance_summary.xlsx
```

**7. Explore with Jupyter** (Optional)
```bash
make run-jupyterlab  # http://localhost:8888
```

---

## 🐳 Dev Container (Recommended for Teams)

Best option for consistent development across team members.

### Prerequisites
- VS Code
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Docker/Docker Desktop

### Setup (One Click!)

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd insurance-analytics-project
   ```

2. **Open in VS Code**
   ```bash
   code .
   ```

3. **Reopen in Container**
   - VS Code shows a prompt: **"Reopen in Container"** → Click it
   - OR use Command Palette: `Cmd/Ctrl + Shift + P` → `Dev Containers: Reopen in Container`

4. **Wait for Setup** (3-5 minutes)
   - Docker builds the container
   - Python dependencies installed
   - PostgreSQL initialized
   - Synthetic data generated
   - Ready to use!

### What Happens Automatically
✅ Python 3.11 + PostgreSQL 15 set up  
✅ All dependencies from `requirements.txt` installed  
✅ Database schema created  
✅ Sample data generated (2000 members, 300 providers, 5000 claims)  
✅ VS Code extensions installed (Python, Jupyter, Git, etc.)  
✅ Jupyter kernel configured  
✅ Black formatter & linters configured

### After Setup
```bash
# Try any of these:
make run-jupyterlab    # Start Jupyter Lab
make test              # Run all tests
make lint              # Check code quality
make format            # Auto-format code
python -m src.model    # Run ML model
```

---

## 🛠 Make Commands – All Available Tasks

```bash
make help              # Show all commands
make install           # Install/upgrade all dependencies
make clean             # Clean cache and artifacts
make test              # Run tests with coverage
make lint              # Check code quality (flake8, pylint)
make format            # Auto-format code (black, isort)
make check-types       # Type checking (mypy)
make check             # Run all checks (lint + types + tests)
make run-jupyter       # Start Jupyter Notebook (port 8889)
make run-jupyterlab    # Start JupyterLab (port 8888) ⭐ Recommended
make db-init           # Initialize database schema
make db-reset          # Reset database (drop & recreate)
make data-gen          # Generate synthetic data
make load-data         # Load CSV data into database
make setup             # Full setup (install + db + data)
```

---

## 📓 Interactive Notebooks

The `notebooks/` folder contains Jupyter notebooks for data exploration and analysis.

**Quick Start:**
```bash
make run-jupyterlab    # Open http://localhost:8888
```

**Available Notebooks:**
- `01_exploratory_analysis/` – Data exploration & visualization
- `02_feature_engineering/` – Feature creation & transformation
- `03_modeling/` – Model development & testing
- `04_reporting/` – Dashboard & report generation

**Features:**
✅ Auto-loaded with project dependencies  
✅ Database connection configured  
✅ Access to all `src/` modules  
✅ Auto-reload enabled for code changes  

**Example Notebook Code:**
```python
import pandas as pd
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# Query data
df = pd.read_sql("SELECT * FROM insurance.claim LIMIT 10", engine)
df.head()
```

See [notebooks/README.md](notebooks/README.md) for detailed guide.

---

## 🎓 Learning Modules (concepts/)

11 standalone Python modules teaching core concepts needed for this project:

| Module | Topic | Time |
|--------|-------|------|
| `01_argparse_basics.py` | CLI argument parsing | 10 min |
| `02_csv_read_write.py` | CSV file operations | 10 min |
| `03_db_connection.py` | Database connectivity | 15 min |
| `04_pandas_transform.py` | Data transformation | 20 min |
| `05_synthetic_data.py` | Fake data generation | 15 min |
| `06_ml_basics.py` | ML fundamentals | 30 min |
| `07_logging.py` | Application logging | 10 min |
| `08_config_loading.py` | YAML configuration | 15 min |
| `09_excel_report.py` | Report generation | 15 min |
| `10_testing_basics.py` | Unit testing | 20 min |
| `11_date_handling.py` | Date/time utilities | 10 min |

**Run any module:**
```bash
python concepts/01_argparse_basics.py --help
python concepts/04_pandas_transform.py
```

See [concepts/README.md](concepts/README.md) for learning path.

---

## 📊 Project Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Insurance Analytics Pipeline              │
└─────────────────────────────────────────────────────────────┘

1. GENERATE SYNTHETIC DATA
   └─ src/generate_synthetic.py
      Creates realistic members, providers, claims CSVs

2. LOAD INTO DATABASE
   └─ src/load.py
      CSV → PostgreSQL using SQLAlchemy + pandas

3. TRANSFORM & CALCULATE KPIs
   └─ src/transform.py
      Joins, aggregations, KPIs (frequency, severity, loss ratio)
      Results → insurance.kpi_summary table

4. TRAIN ML MODEL
   └─ src/model.py
      Feature engineering → Classification model
      Predicts: high-cost claimants
      Saves predictions → database

5. GENERATE REPORTS
   └─ src/report.py
      KPIs + charts → Multi-sheet Excel workbook
      Output: outputs/insurance_summary.xlsx

6. JUPYTER EXPLORATION (Optional)
   └─ notebooks/
      Interactive analysis & visualization
```

---

## 🗄️ Database Schema

PostgreSQL tables in `insurance` schema:

| Table | Purpose |
|-------|---------|
| `members` | Patient demographics (age, gender, etc.) |
| `providers` | Healthcare provider details |
| `claims` | Insurance claims (date, amount, type) |
| `claims_enhanced` | Transformed claims with enrichment |
| `kpi_summary` | Aggregated KPIs by member/provider |
| `model_predictions` | ML model predictions |

See [sql/ddl_create_tables.sql](sql/ddl_create_tables.sql) for full schema.

---

## 🧪 Testing & Code Quality

**Run Tests:**
```bash
make test              # Run all tests with coverage
pytest tests/ -v       # Verbose output
pytest tests/test_db.py -k "test_connection" # Specific test
```

**Code Quality Checks:**
```bash
make lint              # pylint + flake8
make check-types       # mypy type checking
make format            # Auto-fix with black + isort
make check             # All quality checks
```

**Test Coverage:**
```bash
pytest --cov=src --cov-report=html
# Opens htmlcov/index.html in browser
```

---

## �️ Code Quality & Linting

Comprehensive code quality tooling for professional development:

### 🔧 Available Tools

**Formatting & Style:**
- **Black** – Uncompromising code formatter (100 char lines)
- **isort** – Import sorting with black compatibility
- **docformatter** – Docstring formatting
- **Ruff** – Fast Python linter and formatter

**Linting & Analysis:**
- **flake8** – Style guide enforcement + complexity checks
- **pylint** – Comprehensive static analysis
- **mypy** – Static type checking
- **bandit** – Security vulnerability scanning
- **radon** – Cyclomatic complexity analysis
- **xenon** – Strict complexity limits
- **vulture** – Dead code detection
- **cohesion** – Module cohesion analysis

**Pre-commit Hooks:**
- **pre-commit** – Automated quality checks on commit
- Configured with 12+ hooks for comprehensive validation

### 🚀 Quick Commands

```bash
# Format all code
make format

# Run all linters
make lint

# Type checking
make check-types

# Code quality analysis
make quality

# Security scanning
make security

# Complexity analysis
make complexity

# Documentation checks
make docs

# Run pre-commit hooks
make pre-commit

# Run everything
make check
```

### 📊 Dev Container Integration

VS Code extensions automatically installed:
- Python, Pylance, debugpy
- Black, isort, flake8, mypy, pylint
- Jupyter, SQL Tools, GitLens
- Markdown linting, spell checker
- Docker, Git Graph, Todo Tree

**Auto-formatting on save** enabled for:
- Python (black + isort)
- JSON/YAML (prettier)
- Markdown (prettier)

### 🔍 CI/CD Quality Gates

GitHub Actions runs comprehensive checks:

**Lint Job:**
- Pre-commit hooks validation
- Code formatting verification
- Static analysis (pylint, mypy, bandit)
- Complexity and maintainability metrics

**Test Job:**
- pytest with coverage reporting
- Codecov integration
- JUnit XML reports

**SonarCloud Analysis:**
- Code quality metrics
- Security hotspots
- Technical debt analysis
- Coverage integration

### 📋 Configuration Files

- `pyproject.toml` – Centralized tool configuration
- `.pre-commit-config.yaml` – Pre-commit hook definitions
- `sonar-project.properties` – SonarCloud analysis settings
- `requirements.txt` – All development dependencies

### 🎯 Quality Standards

**Code Style:**
- PEP 8 compliant with Black formatting
- 100 character line length
- Import sorting with isort
- Comprehensive docstrings

**Type Safety:**
- Full type hints required
- mypy strict mode enabled
- No `Any` types without justification

**Security:**
- Bandit security scanning
- Dependency vulnerability checks
- No hardcoded secrets

**Complexity:**
- Cyclomatic complexity < 10
- Function length < 50 lines
- Module cohesion > 0.7

**Testing:**
- 80%+ code coverage required
- Unit tests for all functions
- Integration tests for pipelines

---

## �🔄 GitHub Actions CI/CD

Automated workflow on every push/PR:

1. ✅ **Install Dependencies** – from `requirements.txt`
2. ✅ **Lint Code** – flake8, pylint
3. ✅ **Type Check** – mypy
4. ✅ **Run Tests** – pytest with coverage
5. ✅ **Generate Data** – synthetic datasets
6. ✅ **Run Pipeline** – transform, model, report

See `.github/workflows/` for configuration.

---

## 📚 SAS ↔ Python Examples

Reference translations of common SAS workflows:

**SAS Code:** `sas-python-examples/sas/employees_analysis.sas`  
**Python Code:** `sas-python-examples/python/employees_analysis.py`

Good for:
- Learning Python equivalents of SAS PROC SQL, PROC MEANS, etc.
- Understanding data manipulation patterns
- Debugging

---

## 🆘 Troubleshooting

### Database Connection Issues
```bash
# Check environment variable
echo $DATABASE_URL

# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Manually connect (dev container or local)
psql "$DATABASE_URL" -c "SELECT version();"
```

### Jupyter Kernel Not Found
```bash
# Reinstall kernel
python -m ipykernel install --user --name=insurance --display-name="Insurance Analytics"

# List available kernels
jupyter kernelspec list
```

### Large Data Issues
```bash
# Generate smaller dataset
python -m src.generate_synthetic --rows-members 100 --rows-claims 500 --out-dir data/

# Or clear database
make db-reset
```

### Port Already in Use
```bash
# Use different port
jupyter lab --port=8890

# Or find process using port
lsof -i :8888
kill -9 <PID>
```

---

## 📋 Environment Variables

Create `.env` (or use in dev container):
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/insurdb
JUPYTER_ENABLE_LAB=yes
PYTHONPATH=/workspaces/insurance-analytics-project
```

See [.env.example](.env.example) for all options.

---

## 🤝 Contributing

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes & test**
   ```bash
   make format
   make check
   ```

3. **Commit & push**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   git push origin feature/my-feature
   ```

4. **Create Pull Request** on GitHub

---

## 📄 License

MIT License – See [LICENSE](LICENSE)

---

## 🚀 Next Steps

1. ✅ Choose your setup: [Local](#-quick-start--local-setup-without-dev-container) or [Dev Container](#-dev-container-recommended-for-teams)
2. ✅ Run `make help` to see all available commands
3. ✅ Launch Jupyter: `make run-jupyterlab`
4. ✅ Explore [concepts/](concepts/README.md) for learning modules
5. ✅ Read [notebooks/README.md](notebooks/README.md) for notebook usage

---

**Questions?** Check docs/, concepts/, or sas-python-examples/ for examples.  
**Happy analyzing!** 📊
