# Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 15+ | Database (or Docker) |
| Git | any | Source control |
| Docker | any | Dev container / local PG |

---

## Option A — Local Setup

```bash
# 1. Clone
git clone <repo-url>
cd insurance-analytics-project

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install
pip install -r requirements.txt
pip install -e .                   # installs src/ as a package

# 4. PostgreSQL via Docker
docker run --name insurdb \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=insurdb \
  -p 5432:5432 -d postgres:15

# 5. Environment variable
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb

# 6. Kaggle credentials (required to download the dataset)
export KAGGLE_USERNAME=your_kaggle_username
export KAGGLE_KEY=your_kaggle_api_key
# Alternatively, place ~/.kaggle/kaggle.json (downloaded from kaggle.com → Account → API)

# 7. Schema
psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS insurance;"
psql "$DATABASE_URL" -f sql/ddl_create_tables.sql

# 8. Data — download from Kaggle and load into the database
python -m src.load --kaggle-config config/kaggle.yaml

# 9. Run pipeline
python -m src.transform
python -m src.model
python -m src.report --out outputs/insurance_summary.xlsx
```

---

## Option B — Dev Container (recommended for teams)

### Prerequisites
- VS Code + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Docker Desktop

### Steps

1. Clone the repo and open in VS Code: `code .`
2. When prompted, click **Reopen in Container** (or `Ctrl+Shift+P` → *Dev Containers: Reopen in Container*)
3. Wait ~3–5 minutes for the first build

The container automatically:
- Installs Python 3.11 + all dependencies
- Starts PostgreSQL 15
- Creates the schema and seeds synthetic data
- Configures the Jupyter kernel and VS Code extensions

After the build, everything is ready — run `make help` to see all tasks.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Full SQLAlchemy URL (overrides all below) |
| `DB_HOST` | `localhost` | Postgres host |
| `DB_PORT` | `5432` | Postgres port |
| `DB_USER` | `postgres` | Postgres user |
| `DB_PASS` | `postgres` | Postgres password |
| `DB_NAME` | `insurdb` | Database name |
| `KAGGLE_USERNAME` | — | Kaggle account username (required for data ingest) |
| `KAGGLE_KEY` | — | Kaggle API key (required for data ingest) |
| `KAGGLE_CONFIG` | `config/kaggle.yaml` | Path to the Kaggle dataset YAML config |

Copy `.env.example` to `.env` for local development (never commit `.env`).

---

## Running Tests

```bash
make test                          # all tests with coverage
pytest tests/ -v -m integration   # integration tests only (requires live DB)
pytest --cov=src --cov-report=html # HTML coverage report → htmlcov/index.html
```

---

## Troubleshooting

**DB connection refused**
```bash
pg_isready -h localhost -p 5432
echo $DATABASE_URL
psql "$DATABASE_URL" -c "SELECT version();"
```

**Jupyter kernel not found**
```bash
python -m ipykernel install --user --name=insurance --display-name="Insurance Analytics"
jupyter kernelspec list
```

**Port already in use**
```bash
lsof -i :8888 && kill -9 <PID>
jupyter lab --port=8890
```

**Duplicate data after re-running load**
The load uses `TRUNCATE … RESTART IDENTITY CASCADE` before each insert — re-running is safe and idempotent. Reset with `make db-reset` if you need a fully clean slate.
