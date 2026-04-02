---
name: automation-ci-helper
description: Instructions for managing CI pipelines, GitHub Actions workflows, Airflow DAGs, and automation scripts in the insurance analytics project.
---

# Automation & CI Helper Skill

This skill covers all automation in the insurance analytics project: GitHub Actions CI workflows, the Apache Airflow data pipeline, the Makefile task runner, pre-commit hooks, and quality-gate tooling.

## Automation components at a glance

| Component | Location | Purpose |
|---|---|---|
| GitHub Actions – CI | `.github/workflows/ci-postgres.yml` | Lint → test → SonarCloud on every push/PR |
| GitHub Actions – Release | `.github/workflows/release.yml` | Publishes a release artifact |
| GitHub Actions – Scheduled | `.github/workflows/scheduled-pipeline.yml` | Runs the pipeline on a schedule |
| Airflow DAG | `airflow/dags/insurance_pipeline_dag.py` | Orchestrates the ETL end-to-end |
| Makefile | `Makefile` | Developer task runner (local shortcuts) |
| Pre-commit hooks | `.pre-commit-config.yaml` | Auto-formats and lints on every `git commit` |

## GitHub Actions: CI workflow (`ci-postgres.yml`)

The CI workflow has **three sequential jobs**:

```
lint  →  test  →  sonarcloud
```

### Job 1 – `lint` (static analysis)

Runs on every push/PR to `main`/`master` that touches `src/`, `tests/`, `sql/`, or config files.

Steps:
1. `black --check` + `isort --check` – formatting
2. `flake8` + `pylint` – style and errors
3. `mypy src` – static type checking
4. `bandit -r src` – security scan
5. `radon cc` + `radon mi` – cyclomatic complexity and maintainability index

### Job 2 – `test` (integration tests with PostgreSQL)

Spins up a **PostgreSQL 15 service container** (`POSTGRES_USER=postgres`, `POSTGRES_DB=insurdb`), then:

1. Applies the DDL (`sql/ddl_create_tables.sql`)
2. Generates synthetic data (`src.generate_synthetic`)
3. Loads data (`src.load`)
4. Runs the transform (`src.transform`)
5. Runs pytest with `--cov` and uploads coverage to Codecov

Key environment variable set by the workflow:

```yaml
DATABASE_URL: postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb
```

### Job 3 – `sonarcloud`

Downloads the test artifacts (coverage + JUnit XML) and runs SonarCloud analysis. Requires two repository secrets:

- `SONAR_TOKEN` – from SonarCloud
- `CODECOV_TOKEN` – from Codecov

### Triggering CI manually

Push any change to a file under `src/`, `tests/`, `sql/`, `requirements.txt`, or `pyproject.toml` on a branch targeting `main`/`master`. A pull request against those branches also triggers CI.

## Makefile: local task runner

Run `make help` to see all targets. Most-used ones:

```bash
make install        # pip install all dependencies
make test           # pytest with coverage
make lint           # flake8 + ruff + pylint
make format         # black + isort + ruff format + docformatter
make check-types    # mypy --strict
make quality        # bandit + radon + xenon + cohesion + vulture
make check          # lint + check-types + test + quality (full gate)

make db-init        # apply sql/ddl_create_tables.sql
make db-reset       # DROP SCHEMA + re-apply DDL
make data-gen       # generate synthetic CSVs into data/
make load-data      # load CSVs into PostgreSQL
make setup          # install + db-init + data-gen + load-data (full first-time setup)

make airflow-up     # start Airflow via Docker Compose (port 8080)
make airflow-down   # stop Airflow
make airflow-logs   # tail scheduler logs
```

## Airflow DAG

The DAG is defined in `airflow/dags/insurance_pipeline_dag.py` and orchestrates:

```
ingest  →  load  →  transform  →  report
```

The `DATA_SOURCE` environment variable controls the ingest step:
- `DATA_SOURCE=kaggle` → uses `src/kaggle_ingest.py` (downloads from Kaggle API)
- Any other value → uses the default synthetic-data path

Kaggle credentials are read from:
- Environment variables `KAGGLE_USERNAME` and `KAGGLE_KEY`, **or**
- `~/.kaggle/kaggle.json`

Kaggle configuration (dataset name, output path) lives in `config/kaggle.yaml`.

### Starting Airflow locally

```bash
make airflow-up
# Airflow UI → http://localhost:8080   login: admin / admin
make airflow-down   # stop when done
```

Airflow runs via Docker Compose (`airflow/docker-compose-airflow.yml`) on a dedicated `insurance-network` Docker network.

## Pre-commit hooks (`.pre-commit-config.yaml`)

Pre-commit runs automatically on `git commit`. To run it manually against all files:

```bash
make pre-commit
# or directly:
pre-commit run --all-files
```

Typical hooks in this project: `black`, `isort`, `flake8`, trailing-whitespace / end-of-file fixers.

First-time setup:

```bash
pip install pre-commit
pre-commit install   # installs the git hook
```

## Quality gate script (`check-quality.sh`)

A shell script that aggregates multiple quality checks in one pass:

```bash
make quality-check
# or directly:
./check-quality.sh
```

Run this locally before opening a pull request to catch issues that CI will also catch.

## Adding a new CI step

1. Open `.github/workflows/ci-postgres.yml`.
2. Add a new `- name: …` step inside the appropriate job (`lint` for static checks, `test` for runtime checks).
3. Any new Python tool must also be added to `requirements.txt` and optionally `pyproject.toml` so it installs in CI.
4. Test the workflow by pushing to a feature branch and opening a pull request.

## Common CI failures and fixes

| Failure | Likely cause | Fix |
|---|---|---|
| `black --check` fails | Code not formatted | Run `make format` locally, then commit |
| `mypy` errors | Missing type annotations or wrong types | Add/fix type hints in `src/` |
| `bandit` security warning | Use of a flagged function (e.g. `subprocess`, `pickle`) | Refactor or add `# nosec` with justification |
| Postgres connection refused | Service container not ready | The workflow uses health-checks; check `options:` in the YAML |
| `pytest` collection error | Import error in `src/` | Run `pytest -q` locally with the same `DATABASE_URL` to reproduce |
| SonarCloud gate fails | Coverage below threshold or new bugs found | Fix the issues reported in the SonarCloud PR comment |

## Secrets required in GitHub repository settings

| Secret name | Used by |
|---|---|
| `SONAR_TOKEN` | SonarCloud scan (job 3) |
| `CODECOV_TOKEN` | Codecov upload (job 2) |
| `KAGGLE_USERNAME` | Kaggle ingest (Airflow / scheduled pipeline) |
| `KAGGLE_KEY` | Kaggle ingest (Airflow / scheduled pipeline) |
