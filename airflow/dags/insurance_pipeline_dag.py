"""Airflow DAG — Insurance Analytics end-to-end pipeline.

Schedule : daily at 06:00 UTC (configurable via AIRFLOW_PIPELINE_SCHEDULE env var)
Graph    : generate → load → [transform, model] → report

Each task shells out to the existing CLI entry-points so no production code
needs to change.  The DAG is idempotent — load.py truncates before inserting.
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
    description="Generate → Load → Transform + Model → Report",
    schedule=SCHEDULE,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["insurance", "etl", "ml"],
) as dag:
    generate = BashOperator(
        task_id="generate_synthetic_data",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.generate_synthetic "
            "--rows-members 2000 --rows-providers 300 --rows-claims 5000 "
            "--out-dir data/"
        ),
        env=TASK_ENV,
    )

    load = BashOperator(
        task_id="load_csv_to_postgres",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.load --from-csv "
            "--members data/sample_members.csv "
            "--providers data/sample_providers.csv "
            "--claims data/sample_claims.csv"
        ),
        env=TASK_ENV,
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

    report = BashOperator(
        task_id="generate_excel_report",
        bash_command=(
            f"cd {PROJECT_DIR} && " "python -m src.report --out outputs/insurance_summary.xlsx"
        ),
        env=TASK_ENV,
    )

    # ----- dependency graph -----
    # generate → load → transform ──┐
    #                    model    ───┤→ report
    generate >> load >> [transform, model] >> report  # pylint: disable=pointless-statement
