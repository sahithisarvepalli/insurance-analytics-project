---
name: insurance-data-analytics
description: Instructions for processing insurance claims data using Python and Pandas in this project.
---

# Insurance Data Analytics Skill

This skill covers how to work with insurance claims data in this project using Python and the Pandas library. The project follows an ETL (Extract → Transform → Load) pattern feeding into an ELT DW layer built on DuckDB.

## Architecture

```
Kaggle CSV
    │
    ▼
src/load.py  ──►  Postgres ODS (insurance schema)   ← ETL
                        │
                        ▼
src/transform.py  ──►  outputs/*.csv                 ← pandas aggregations
                        │
                        ▼
src/dw_load.py  ──►  outputs/insurance_dw.duckdb     ← ELT / star schema DW
```

- **Postgres** (`insurance` schema) is the operational data store (ODS) — 3 normalised tables.
- **DuckDB** (`outputs/insurance_dw.duckdb`) is the analytical data warehouse — star schema with dimensions, a fact table, and pre-aggregated summary tables.

## Project layout

```
src/
  kaggle_ingest.py  # Downloads Kaggle datasets and maps columns to pipeline schema
  load.py           # Loads mapped DataFrames into PostgreSQL (truncate + insert)
  transform.py      # Joins tables, derives KPIs, and writes outputs/
  dw_load.py        # DuckDB DW loader: dimensions → fact → summaries + QA report
  model.py          # Logistic regression: identifies high-cost members
  report.py         # Assembles outputs into a multi-sheet Excel workbook
  utils.py          # Shared helpers: get_engine(), logger
  sql/
    ddl_create_tables.sql  # Postgres ODS DDL (insurance schema)
    ddl_dw.sql             # DuckDB DW DDL (dim_*, fact_claims)
config/
  kaggle.yaml       # Kaggle dataset selection and column-mapping config
  db.yaml           # Database connection config
outputs/
  kpis.csv                # KPI aggregation by age band / region / network
  monthly.csv             # Monthly claims trend
  loss_ratio.csv          # Paid vs billed vs allowed ratios by region / network
  network_summary.csv     # In-network vs out-of-network utilization
  diagnosis_summary.csv   # Claims ranked by ICD diagnosis code
  model_metrics.txt       # Model accuracy from the logistic regression run
  insurance_summary.xlsx  # Six-sheet Excel report combining all the above
  insurance_dw.duckdb     # DuckDB analytical data warehouse (star schema)
build/reports/
  dw_quality.json   # DW QA report (written by src/dw_load.py on every run)
notebooks/
  dw_sample_queries.ipynb  # Analytic queries against insurance_dw.duckdb
data/
  kaggle/           # Cached Kaggle downloads (not committed)
```

## Key data tables

### Postgres ODS (`insurance` schema)

| Table | Key columns |
|---|---|
| `insurance.member` | `member_id`, `dob`, `gender`, `region`, `effective_date`, `termination_date` |
| `insurance.provider` | `provider_id`, `specialty`, `in_network`, `region` |
| `insurance.claim` | `claim_id`, `member_id`, `provider_id`, `service_date`, `diagnosis_code`, `procedure_code`, `billed_amount`, `allowed_amount`, `paid_amount`, `place_of_service` |

### DuckDB DW (`insurance_dw.duckdb`)

| Table | Type | Source |
|---|---|---|
| `dim_member` | Dimension | Postgres `insurance.member` + `age_band` derived |
| `dim_provider` | Dimension | Postgres `insurance.provider` |
| `dim_date` | Dimension | Generated date spine 2010-01-01 → today+1yr |
| `fact_claims` | Fact | Postgres `insurance.claim` with `date_key` from `service_date` |
| `summary_kpis` | Summary | `outputs/kpis.csv` |
| `summary_monthly` | Summary | `outputs/monthly.csv` |
| `summary_loss_ratio` | Summary | `outputs/loss_ratio.csv` |
| `summary_network` | Summary | `outputs/network_summary.csv` |

## How to load data (Kaggle ingest)

```bash
# Set Kaggle credentials (or place ~/.kaggle/kaggle.json)
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_api_key

# Download the Kaggle dataset and load into PostgreSQL
python -m src.load --kaggle-config config/kaggle.yaml

# Or use the Makefile shortcut
make kaggle-load
```

The active dataset is controlled by `active_dataset` in `config/kaggle.yaml`.
Column mappings and defaults for absent columns are also defined there.

## How to run the transform

```bash
python -m src.transform
```

`transform.py` does the following steps:

1. **Query** – joins `claim`, `member`, and `provider` into one DataFrame using `pd.read_sql`.
2. **Derive age** – calculates each member's age from `dob` and today's date.
3. **Age bands** – uses `pd.cut()` to bucket ages into `0-18`, `19-30`, `31-45`, `46-60`, `60+`.
4. **KPI aggregation** – groups by `age_band`, `member_region`, and `in_network`; computes claim count, total paid, and average paid → `outputs/kpis.csv`.
5. **Monthly summary** – groups by year-month, region, and in-network flag → `outputs/monthly.csv`.
6. **Loss ratio** – computes paid/billed and allowed/billed ratios by region and network status → `outputs/loss_ratio.csv`.
7. **Network utilization** – in-network vs out-of-network claim counts and cost percentages → `outputs/network_summary.csv`.
8. **Diagnosis summary** – claims and costs ranked by ICD diagnosis code → `outputs/diagnosis_summary.csv`.

## How to build the DuckDB data warehouse

```bash
# Run after kaggle-load and transform
make dw-load
# or directly:
python -m src.dw_load
```

`dw_load.py` orchestrates:

1. `get_dw_conn(path)` — opens/creates `outputs/insurance_dw.duckdb`, applies `src/sql/ddl_dw.sql`.
2. `load_dim_member()` — reads Postgres `insurance.member`, derives `age_band` via `pd.cut`, loads to `dim_member`.
3. `load_dim_provider()` — reads Postgres `insurance.provider` → `dim_provider`.
4. `load_dim_date()` — generates date spine 2010-01-01 → today+1yr → `dim_date`.
5. `load_fact_claims()` — reads `insurance.claim`, renames `service_date` → `date_key` → `fact_claims`.
6. `load_summaries()` — reads `outputs/*.csv` into 4 `summary_*` tables (schema inferred).
7. `run_quality_checks()` — validates row counts, PK uniqueness, FK refs, null PKs; raises `RuntimeError` on failure.
8. `_write_qa_report()` — writes `build/reports/dw_quality.json`.

### Loading strategy

Every run does a **full refresh** (idempotent):
- Dimension tables: `DELETE FROM + INSERT` (preserves schema, replaces all rows).
- Summary tables: `CREATE OR REPLACE TABLE` (schema may change as transform evolves).

### Querying the DW in Python / Jupyter

```python
import duckdb
conn = duckdb.connect('outputs/insurance_dw.duckdb', read_only=True)

# Star schema join: paid claims by age band, region, quarter
df = conn.execute("""
    SELECT m.age_band, m.region, d.quarter,
           COUNT(f.claim_id) AS claims, SUM(f.paid_amount) AS total_paid
    FROM fact_claims f
    JOIN dim_member  m ON f.member_id  = m.member_id
    JOIN dim_date    d ON f.date_key   = d.date_key
    GROUP BY m.age_band, m.region, d.quarter
    ORDER BY total_paid DESC
""").df()
conn.close()
```

Open the pre-built notebook for more examples:
```bash
make run-jupyterlab   # then open notebooks/dw_sample_queries.ipynb
```

### DW QA report

After every `make dw-load`, a JSON report is written to `build/reports/dw_quality.json`:

```json
{
  "generated_at": "2026-04-03T15:00:00Z",
  "checks": {
    "dim_member_count": 1338,
    "fact_claims_count": 1338,
    "fact_claims_dup_claim_id": 0,
    "missing_member_refs": 0,
    "missing_provider_refs": 0,
    "null_member_pk": 0,
    "null_provider_pk": 0,
    "status": "ok"
  }
}
```

## Pandas patterns used in this project

```python
import pandas as pd

# Read a SQL query into a DataFrame (used in transform.py)
df = pd.read_sql(query, engine, parse_dates=["service_date", "dob"])

# Derive a calculated column
df["age"] = (pd.Timestamp.now().normalize() - df["dob"]).dt.days // 365

# Bin a numeric column into labelled categories
df["age_band"] = pd.cut(df["age"], bins=[0, 18, 30, 45, 60, 200],
                         labels=["0-18", "19-30", "31-45", "46-60", "60+"])

# Group and aggregate
kpis = (
    df.groupby(["age_band", "member_region", "in_network"], observed=True)
    .agg(
        claims=("claim_id", "count"),
        paid_total=("paid_amount", "sum"),
        paid_avg=("paid_amount", "mean"),
    )
    .reset_index()
)

# Write to CSV
kpis.to_csv("outputs/kpis.csv", index=False)
```

## Common beginner mistakes to avoid

- **Date parsing**: Always pass `parse_dates=` to `pd.read_sql` or `pd.read_csv` so date columns become `datetime64`, not plain strings.
- **groupby observed**: Pass `observed=True` when grouping by a `pd.Categorical` column (like `age_band`) to avoid empty groups appearing in the output.
- **index=False**: Pass `index=False` to `DataFrame.to_csv()` so the row index is not written as an extra column.
- **reset_index()**: Call `.reset_index()` after a groupby so the group keys become regular columns instead of a MultiIndex.
- **pandas + SQLAlchemy**: `DataFrame.to_sql()` in pandas 2.x requires a SQLAlchemy `Engine` object, not a `Connection`. Always pass `engine`, not `con` from `engine.begin()`.
- **DuckDB read_only**: Open the DW file with `read_only=True` in notebooks/scripts that only query — prevents lock conflicts with the pipeline writer.

## Connecting to PostgreSQL

The database URL is read from the `DATABASE_URL` environment variable (set in `.env`):

```python
# utils.py provides this helper — always use it instead of creating your own engine
from src.utils import get_engine
engine = get_engine()
```

Set `DATABASE_URL` in your shell or copy `.env.example` to `.env`:

```bash
cp .env.example .env
# edit .env and set DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/insurdb
```

## Running in Jupyter

```bash
make run-jupyterlab   # opens http://localhost:8888
# or
make run-jupyter      # opens http://localhost:8889
```

Notebooks live in the `notebooks/` directory. Import project modules with:

```python
import sys
sys.path.insert(0, "..")   # if running from inside notebooks/
from src.transform import run_transform
from src.dw_load import run_dw_load
```
