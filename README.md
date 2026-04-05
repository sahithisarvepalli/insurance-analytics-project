# Insurance Analytics

[![CI](https://github.com/sahithisarvepalli/insurance-analytics-project/actions/workflows/ci-postgres.yml/badge.svg)](https://github.com/sahithisarvepalli/insurance-analytics-project/actions/workflows/ci-postgres.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=coverage)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=sahithisarvepalli_insurance-analytics-project&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=sahithisarvepalli_insurance-analytics-project)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

End-to-end insurance analytics platform built with Python + PostgreSQL. A SAS/DB2 practitioner's sandbox for production-quality Python — EtLT pipelines, KPI aggregation, ML modeling, DuckDB data warehouse, and Excel reporting over synthetic claims data.

---

## Pipeline

```
kaggle_ingest → [transform, model] → dw_load → report (Excel + HTML dashboard)
```

> **Pattern:** This project uses a hybrid **EtLT** approach. `kaggle_ingest` does light column-mapping ETL before writing to PostgreSQL. Everything downstream — `transform`, `model`, and `dw_load` — follows ELT: raw data loads first, then transformations run inside the system.

| Step | Module | SAS Equivalent |
|------|--------|---------------|
| Kaggle ingest (light ETL) | `src/kaggle_ingest.py` + `src/load.py` | `PROC IMPORT` / `LIBNAME` engine |
| KPI aggregation (ELT) | `src/transform.py` | `PROC MEANS` / `PROC SQL GROUP BY` |
| ML model (ELT) | `src/model.py` | `PROC LOGISTIC` |
| DW load — star schema (ELT) | `src/dw_load.py` | `PROC DATASETS` + summary tables |
| Excel report | `src/report.py` | `ODS Excel` |
| HTML dashboard | `src/generate_html_report.py` | SAS Visual Analytics / ODS HTML |

---

## Quick Start

### Dev Container (recommended — zero setup)

Open this repository in VS Code and choose **Reopen in Container**. The dev container automatically:

- Installs all Python dependencies (`requirements.txt` + the package itself)
- Starts a PostgreSQL 15 service (`db:5432`) and waits for it to be healthy
- Sets `DATABASE_URL` and `PYTHONPATH` environment variables
- Initialises the database schema and pre-commit hooks

Once inside the container, run the pipeline directly — no virtual environment or Docker commands needed:

```bash
# Download Kaggle dataset and load into PostgreSQL
make kaggle-load

# Run the full pipeline
python -m src.transform
python -m src.model
python -m src.dw_load      # build the DuckDB star-schema warehouse
python -m src.report --out outputs/insurance_summary.xlsx
```

> **Note:** `DATABASE_URL` is pre-set to `postgresql://postgres:postgres@db:5432/insurdb`.
> The database host is `db` (the Docker Compose service name), not `localhost`.
> Kaggle credentials (`KAGGLE_USERNAME` / `KAGGLE_KEY`) must be set — see [docs/setup.md](docs/setup.md).

### Local setup (outside dev container)

Only needed if you are not using the dev container:

```bash
pip install -r requirements.txt && pip install -e .

# Start PostgreSQL separately, then export the connection URL
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb

# Export Kaggle credentials
export KAGGLE_USERNAME=your_kaggle_username
export KAGGLE_KEY=your_kaggle_api_key

make db-init
make kaggle-load
```

#### Notebook / visualisation work

Jupyter and visualisation libraries (`matplotlib`, `seaborn`, `plotly`) are intentionally
**not** part of `requirements.txt`.  They are not used by the core pipeline and keeping
them out of the main file keeps Docker image builds and CI runner installs significantly
faster.  Install them on demand:

```bash
pip install -r requirements-notebooks.txt
```

Full setup guide: [docs/setup.md](docs/setup.md)

---

## Reports Dashboard

After every successful `client-analytics` workflow run the pipeline publishes
an interactive dashboard directly on GitHub — **no paid tools required**.

| Access method | How | Interactivity |
|---------------|-----|---------------|
| **GitHub Actions Job Summary** | Open **Actions** → select the completed run → view the **Summary** tab | Tables + KPI cards, visible immediately |
| **HTML artifact** | Open **Actions** → select the run → under **Artifacts**, download `report-<client>-run*` and open `dashboard.html` locally | Full Plotly charts — pan, zoom, hover |
| **GitHub Pages** | Enable once: **Settings → Pages → Source → GitHub Actions**, then open `https://<owner>.github.io/<repo>/` | Persistent URL, per-client dashboards |

> One-time setup for GitHub Pages: **Settings → Pages → Source → GitHub Actions**

See [docs/dashboard.md](docs/dashboard.md) for a full comparison of the current
approach vs industry-standard BI tools (Apache Superset, Grafana, Metabase) and
a recommended migration roadmap.

## Make Commands

| Command | Description |
|---------|-------------|
| `make setup` | Full init (db + Kaggle data) |
| `make test` | pytest with coverage |
| `make lint` | flake8 + pylint + ruff |
| `make format` | black + isort + ruff format |
| `make check-types` | mypy |
| `make quality` | bandit + radon + xenon |
| `make check` | All of the above |
| `make run-jupyterlab` | JupyterLab on :8888 |
| `make kaggle-load` | Download Kaggle dataset and load into DB |
| `make db-reset` | Drop + recreate schema |
| `make airflow-up` | Start Airflow (UI on :8080) |
| `make airflow-down` | Stop Airflow |
| `make airflow-logs` | Tail Airflow scheduler logs |

Run `make help` for the full list.

---

## Repository Structure

```
src/            Production source — EtLT pipeline, ML, reporting, DW load
tests/          Integration tests (pytest + live PostgreSQL)
sql/            DDL schema and KPI query templates
data/           Kaggle-sourced data (cached in data/kaggle/)
outputs/        Generated reports and metrics (kpis.csv, monthly.csv, loss_ratio.csv,
                network_summary.csv, diagnosis_summary.csv, model_metrics.txt,
                insurance_dw.duckdb, *.xlsx)
notebooks/      Jupyter exploration and visualisation
concepts/       11 standalone Python learning modules
sas-python-examples/  SAS ↔ Python reference translations
docs/           Detailed guides (setup, architecture, quality, git)
config/         Database and Kaggle dataset configuration (db.yaml, kaggle.yaml)
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/setup.md](docs/setup.md) | Local & dev container setup |
| [docs/architecture.md](docs/architecture.md) | Pipeline, DB schema, design decisions |
| [docs/orchestration.md](docs/orchestration.md) | Airflow + GitHub Actions scheduling |
| [docs/quality_guide.md](docs/quality_guide.md) | Linting, formatting, code quality tools |
| [docs/git.md](docs/git.md) | Git workflow and branching |
| [concepts/README.md](concepts/README.md) | 11 Python learning modules |
| [notebooks/README.md](notebooks/README.md) | Jupyter notebook usage |
| [docs/dashboard.md](docs/dashboard.md) | Reports dashboard — current GitHub viewer vs industry-standard BI |

---

## License

MIT — see [LICENSE](LICENSE)
