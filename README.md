# Insurance Analytics

[![CI](https://github.com/sahithisarvepalli/insurance-analytics-project/actions/workflows/ci-postgres.yml/badge.svg)](https://github.com/sahithisarvepalli/insurance-analytics-project/actions/workflows/ci-postgres.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=coverage)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

End-to-end insurance analytics platform built with Python + PostgreSQL. A SAS/DB2 practitioner's sandbox for production-quality Python — ETL pipelines, KPI aggregation, ML modeling, and Excel reporting over synthetic claims data.

---

## Pipeline

```
generate_synthetic → load (CSV → PG) → transform (KPIs) → model (ML) → report (Excel)
```

| Step | Module | SAS Equivalent |
|------|--------|---------------|
| Synthetic data | `src/generate_synthetic.py` | `PROC SURVEYSELECT` / `PROC SQL RAND()` |
| Load | `src/load.py` | `PROC IMPORT` / `LIBNAME` engine |
| KPI aggregation | `src/transform.py` | `PROC MEANS` / `PROC SQL GROUP BY` |
| ML model | `src/model.py` | `PROC LOGISTIC` |
| Excel report | `src/report.py` | `ODS Excel` |

---

## Quick Start

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# PostgreSQL (Docker)
docker run --name insurdb -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=insurdb \
  -p 5432:5432 -d postgres:15
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb

# Schema + data
make db-init
make data-gen && make load-data

# Run pipeline
python -m src.transform
python -m src.model
python -m src.report --out outputs/insurance_summary.xlsx
```

Dev container (recommended for teams): [docs/setup.md](docs/setup.md)

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make setup` | Full init (db + data) |
| `make test` | pytest with coverage |
| `make lint` | flake8 + pylint |
| `make format` | black + isort |
| `make check-types` | mypy |
| `make quality` | bandit + radon |
| `make check` | All of the above |
| `make run-jupyterlab` | JupyterLab on :8888 |
| `make data-gen` | Regenerate synthetic CSVs |
| `make db-reset` | Drop + recreate schema |

Run `make help` for the full list.

---

## Repository Structure

```
src/            Production source — ETL, ML, reporting
tests/          Integration tests (pytest + live PostgreSQL)
sql/            DDL schema and KPI query templates
data/           Synthetic CSV files
outputs/        Generated reports and metrics
notebooks/      Jupyter exploration and visualisation
concepts/       11 standalone Python learning modules
sas-python-examples/  SAS ↔ Python reference translations
docs/           Detailed guides (setup, architecture, quality, git)
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/setup.md](docs/setup.md) | Local & dev container setup |
| [docs/architecture.md](docs/architecture.md) | Pipeline, DB schema, design decisions |
| [docs/quality_guide.md](docs/quality_guide.md) | Linting, formatting, code quality tools |
| [docs/git.md](docs/git.md) | Git workflow and branching |
| [concepts/README.md](concepts/README.md) | 11 Python learning modules |
| [notebooks/README.md](notebooks/README.md) | Jupyter notebook usage |

---

## License

MIT — see [LICENSE](LICENSE)
