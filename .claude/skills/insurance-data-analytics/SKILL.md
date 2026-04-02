---
name: insurance-data-analytics
description: Instructions for processing insurance claims data using Python and Pandas in this project.
---

# Insurance Data Analytics Skill

This skill covers how to work with insurance claims data in this project using Python and the Pandas library. The project follows an ETL (Extract → Transform → Load) pattern with three core stages: synthetic data generation, database loading, and transformation into KPI outputs.

## Project layout

```
src/
  generate_synthetic.py   # Creates fake member, provider, and claims CSV files
  load.py                 # Reads CSVs and writes them to PostgreSQL
  transform.py            # Joins tables, derives KPIs, and writes outputs/
  model.py                # (Optional) machine-learning utilities
  report.py               # Report generation helpers
  seed.py                 # Database seeding helpers
  utils.py                # Shared helpers: get_engine(), logger
outputs/
  kpis.csv                # Aggregated KPIs produced by transform.py
  monthly.csv             # Monthly rollup produced by transform.py
data/                     # Generated CSV files (not committed)
```

## Key data tables

| Table | Key columns |
|---|---|
| `insurance.member` | `member_id`, `dob`, `gender`, `region`, `effective_date`, `termination_date` |
| `insurance.provider` | `provider_id`, `specialty`, `in_network`, `region` |
| `insurance.claim` | `claim_id`, `member_id`, `provider_id`, `service_date`, `diagnosis_code`, `procedure_code`, `billed_amount`, `allowed_amount`, `paid_amount`, `place_of_service` |

## How to generate and load data

```bash
# 1. Generate synthetic CSV files into data/
python -m src.generate_synthetic \
    --rows-members 2000 \
    --rows-providers 300 \
    --rows-claims 5000 \
    --out-dir data/

# 2. Load the CSVs into PostgreSQL
python -m src.load --from-csv \
    --members  data/sample_members.csv \
    --providers data/sample_providers.csv \
    --claims   data/sample_claims.csv

# Or use the Makefile shortcut
make data-gen
make load-data
```

## How to run the transform

```bash
python -m src.transform
```

`transform.py` does the following steps (good to understand as a learner):

1. **Query** – joins `claim`, `member`, and `provider` into one DataFrame using `pd.read_sql`.
2. **Derive age** – calculates each member's age from `dob` and today's date.
3. **Age bands** – uses `pd.cut()` to bucket ages into `0-18`, `19-30`, `31-45`, `46-60`, `60+`.
4. **KPI aggregation** – groups by `age_band`, `member_region`, and `in_network`; computes claim count, total paid, and average paid.
5. **Monthly summary** – groups by year-month, region, and in-network flag.
6. **Write outputs** – saves `outputs/kpis.csv` and `outputs/monthly.csv`.

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
```
