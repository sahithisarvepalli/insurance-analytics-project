"""Airflow DAG — Insurance Analytics end-to-end pipeline.

Schedule : daily at 06:00 UTC (configurable via AIRFLOW_PIPELINE_SCHEDULE env var)

Data source: Kaggle (requires KAGGLE_USERNAME and KAGGLE_KEY env vars or
~/.kaggle/kaggle.json).  Configure the active dataset in config/kaggle.yaml.

Pipeline: kaggle_ingest → [transform, model] → dw_load → report

Pattern: This pipeline follows a hybrid EtLT approach:
  - kaggle_ingest performs light column-mapping before loading to PostgreSQL (ETL)
  - transform and model query PostgreSQL and produce outputs (ELT)
  - dw_load builds a DuckDB columnar star-schema warehouse from PostgreSQL + CSV outputs (ELT)
  - report assembles all outputs into an Excel workbook

The DAG is idempotent — load.py truncates before inserting.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

# ---------------------------------------------------------------------------
# Configuration — override via Airflow Variables or environment
# ---------------------------------------------------------------------------
SCHEDULE = os.getenv("AIRFLOW_PIPELINE_SCHEDULE", "0 6 * * *")  # daily 06:00
PROJECT_DIR = os.getenv("AIRFLOW_PROJECT_DIR", "/workspaces/insurance-analytics-project")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/insurdb")

# Path to the Kaggle dataset config file.
KAGGLE_CONFIG = os.getenv("KAGGLE_CONFIG", f"{PROJECT_DIR}/config/kaggle.yaml")

DEFAULT_ARGS = {
    "owner": "analytics-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "email_on_failure": False,  # set True + smtp once mail is configured
    "email_on_retry": False,
}

# Common env passed to every BashOperator so the Python modules can
# find the database and import the src package.
TASK_ENV = {
    "DATABASE_URL": DATABASE_URL,
    "PYTHONPATH": PROJECT_DIR,
}

# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="insurance_analytics_pipeline",
    default_args=DEFAULT_ARGS,
    description="Kaggle Ingest → Transform + Model → DW Load → Report",
    schedule=SCHEDULE,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["insurance", "elt", "ml"],
) as dag:
    kaggle_ingest = BashOperator(
        task_id="kaggle_ingest",
        bash_command=(
            f"cd {PROJECT_DIR} && " "python -m src.load " f"--kaggle-config {KAGGLE_CONFIG}"
        ),
        env={
            **TASK_ENV,
            "KAGGLE_USERNAME": os.getenv("KAGGLE_USERNAME", ""),
            "KAGGLE_KEY": os.getenv("KAGGLE_KEY", ""),
        },
    )

    transform = BashOperator(
        task_id="run_transform_kpis",
        bash_command=f"cd {PROJECT_DIR} && python -m src.transform",
        env=TASK_ENV,
    )

    model = BashOperator(
        task_id="run_ml_model",
        bash_command=f"cd {PROJECT_DIR} && python -m src.model",
        env=TASK_ENV,
    )

    dw_load = BashOperator(
        task_id="load_duckdb_warehouse",
        bash_command=f"cd {PROJECT_DIR} && python -m src.dw_load",
        env=TASK_ENV,
    )

    report = BashOperator(
        task_id="generate_excel_report",
        bash_command=(
            f"cd {PROJECT_DIR} && " "python -m src.report --out outputs/insurance_summary.xlsx"
        ),
        env=TASK_ENV,
    )

    # kaggle_ingest feeds both transform and model (both read from PostgreSQL).
    # dw_load runs after transform (needs the CSV summary outputs) and after model
    # (model_metrics.txt is not used by dw_load, but ensures all outputs are
    # stable before the warehouse is refreshed).
    # report runs last, after all outputs (CSVs + model_metrics.txt) are available.
    kaggle_ingest >> [transform, model]  # pylint: disable=pointless-statement
    [transform, model] >> dw_load  # pylint: disable=pointless-statement
    dw_load >> report  # pylint: disable=pointless-statement
