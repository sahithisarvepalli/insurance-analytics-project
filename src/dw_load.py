"""Load the insurance analytics data warehouse into a DuckDB columnar database.

The DW file (outputs/insurance_dw.duckdb) is rebuilt on every pipeline run:
  1. Dimensions  – dim_member, dim_provider, dim_date
  2. Fact table  – fact_claims
  3. Summaries   – summary_kpis, summary_monthly, summary_loss_ratio, summary_network

Summary tables are created dynamically from the CSV outputs produced by src.transform,
so they always reflect the latest aggregation logic without a rigid schema constraint.
"""

import json
import os
from datetime import date, datetime, timedelta
from importlib import resources

import duckdb
import pandas as pd
from sqlalchemy.engine import Engine

from .utils import get_engine, logger

_DEFAULT_DW_PATH = "outputs/insurance_dw.duckdb"


def _read_ddl() -> str:
    """Return the DW DDL SQL bundled with the package."""
    ref = resources.files("src.sql").joinpath("ddl_dw.sql")
    return ref.read_text(encoding="utf-8")


def get_dw_conn(path: str = _DEFAULT_DW_PATH) -> duckdb.DuckDBPyConnection:
    """Open (or create) a DuckDB file at *path* and apply the DW schema DDL."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = duckdb.connect(path)
    ddl = _read_ddl()
    for stmt in ddl.split(";"):
        # Skip fragments that contain no real SQL (blank lines or comments only)
        meaningful = "\n".join(
            line for line in stmt.splitlines() if line.strip() and not line.strip().startswith("--")
        ).strip()
        if meaningful:
            conn.execute(meaningful)
    return conn


def load_dim_member(dw: duckdb.DuckDBPyConnection, engine: Engine) -> None:
    """Load dim_member from Postgres insurance.member, deriving age_band."""
    df = pd.read_sql(
        "SELECT member_id, dob, gender, region FROM insurance.member",
        engine,
        parse_dates=["dob"],
    )
    today = pd.Timestamp.now().normalize()
    df["age"] = (today - df["dob"]).dt.days // 365
    df["age_band"] = pd.cut(
        df["age"],
        bins=[0, 18, 30, 45, 60, 200],
        labels=["0-18", "19-30", "31-45", "46-60", "60+"],
    ).astype(object)
    df = df.drop(columns=["age"])
    dw.execute("DELETE FROM dim_member")  # noqa: S608
    dw.register("_dim_member", df)
    dw.execute(
        "INSERT INTO dim_member " "SELECT member_id, dob, gender, region, age_band FROM _dim_member"
    )
    dw.unregister("_dim_member")
    logger.info("dim_member: loaded %d rows", len(df))


def load_dim_provider(dw: duckdb.DuckDBPyConnection, engine: Engine) -> None:
    """Load dim_provider from Postgres insurance.provider."""
    df = pd.read_sql(
        "SELECT provider_id, specialty, in_network, region FROM insurance.provider",
        engine,
    )
    dw.execute("DELETE FROM dim_provider")  # noqa: S608
    dw.register("_dim_provider", df)
    dw.execute(
        "INSERT INTO dim_provider "
        "SELECT provider_id, specialty, in_network, region FROM _dim_provider"
    )
    dw.unregister("_dim_provider")
    logger.info("dim_provider: loaded %d rows", len(df))


def load_dim_date(dw: duckdb.DuckDBPyConnection) -> None:
    """Generate and load a date dimension spanning 2010-01-01 to one year from today."""
    start = date(2010, 1, 1)
    end = date.today().replace(year=date.today().year + 1)
    days = (end - start).days + 1
    date_list = [start + timedelta(days=i) for i in range(days)]
    df = pd.DataFrame({"date_key": pd.to_datetime(date_list)})
    df["year"] = df["date_key"].dt.year
    df["month_num"] = df["date_key"].dt.month
    df["month_name"] = df["date_key"].dt.strftime("%B")
    df["quarter"] = df["date_key"].dt.quarter
    df["day_of_week"] = df["date_key"].dt.strftime("%A")
    dw.execute("DELETE FROM dim_date")  # noqa: S608
    dw.register("_dim_date", df)
    dw.execute(
        "INSERT INTO dim_date "
        "SELECT date_key, year, month_num, month_name, quarter, day_of_week FROM _dim_date"
    )
    dw.unregister("_dim_date")
    logger.info("dim_date: loaded %d rows", len(df))


def load_fact_claims(dw: duckdb.DuckDBPyConnection, engine: Engine) -> None:
    """Load fact_claims from Postgres insurance.claim, mapping service_date to date_key."""
    df = pd.read_sql(
        """
        SELECT claim_id, member_id, provider_id, service_date,
               billed_amount, allowed_amount, paid_amount,
               diagnosis_code, procedure_code, place_of_service
        FROM insurance.claim
        """,
        engine,
        parse_dates=["service_date"],
    )
    df = df.rename(columns={"service_date": "date_key"})
    dw.execute("DELETE FROM fact_claims")  # noqa: S608
    dw.register("_fact_claims", df)
    dw.execute(
        "INSERT INTO fact_claims "
        "SELECT claim_id, member_id, provider_id, date_key, "
        "billed_amount, allowed_amount, paid_amount, "
        "diagnosis_code, procedure_code, place_of_service "
        "FROM _fact_claims"
    )
    dw.unregister("_fact_claims")
    logger.info("fact_claims: loaded %d rows", len(df))


def _load_summary_csv(dw: duckdb.DuckDBPyConnection, table: str, path: str) -> None:
    """Drop and recreate *table* from *path*, letting DuckDB infer the schema."""
    df = pd.read_csv(path)
    dw.register(f"_{table}", df)
    dw.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _{table}")  # noqa: S608  # nosec
    dw.unregister(f"_{table}")
    count_row = dw.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608  # nosec
    count = int(count_row[0]) if count_row else 0
    logger.info("%s: loaded %d rows from %s", table, count, path)


def run_quality_checks(dw: duckdb.DuckDBPyConnection) -> dict:
    """Run basic DW quality checks and return a result dictionary.

    Checks performed:
    - non-empty dimensional tables
    - uniqueness of `fact_claims.claim_id`
    - referential integrity between `fact_claims` and dimensions
    - no NULLs in primary key columns
    Raises RuntimeError on failure.
    """
    results = {}

    def _count(q):
        return int(dw.execute(q).fetchone()[0])

    # Basic counts
    results["dim_member_count"] = _count("SELECT COUNT(*) FROM dim_member")
    results["dim_provider_count"] = _count("SELECT COUNT(*) FROM dim_provider")
    results["fact_claims_count"] = _count("SELECT COUNT(*) FROM fact_claims")

    # PK uniqueness
    dup_claims = _count("SELECT COUNT(*) - COUNT(DISTINCT claim_id) FROM fact_claims")
    results["fact_claims_dup_claim_id"] = dup_claims

    # FK referential integrity
    missing_members = _count(
        "SELECT COUNT(*) FROM fact_claims f LEFT JOIN dim_member m ON f.member_id = m.member_id WHERE m.member_id IS NULL"
    )
    missing_providers = _count(
        "SELECT COUNT(*) FROM fact_claims f LEFT JOIN dim_provider p ON f.provider_id = p.provider_id WHERE p.provider_id IS NULL"
    )
    results["missing_member_refs"] = missing_members
    results["missing_provider_refs"] = missing_providers

    # Null PKs
    null_member_pk = _count("SELECT COUNT(*) FROM dim_member WHERE member_id IS NULL")
    null_provider_pk = _count("SELECT COUNT(*) FROM dim_provider WHERE provider_id IS NULL")
    results["null_member_pk"] = null_member_pk
    results["null_provider_pk"] = null_provider_pk

    # Evaluate
    failures = []
    if results["dim_member_count"] == 0:
        failures.append("dim_member is empty")
    if results["fact_claims_count"] == 0:
        failures.append("fact_claims is empty")
    if results["fact_claims_dup_claim_id"] > 0:
        failures.append("duplicate claim_id in fact_claims")
    if results["missing_member_refs"] > 0:
        failures.append("fact_claims contains member_id values not present in dim_member")
    if results["missing_provider_refs"] > 0:
        failures.append("fact_claims contains provider_id values not present in dim_provider")
    if results["null_member_pk"] > 0 or results["null_provider_pk"] > 0:
        failures.append("NULL primary keys found in dimensions")

    if failures:
        raise RuntimeError("DW quality checks failed: " + "; ".join(failures))

    results["status"] = "ok"
    return results


def load_summaries(dw: duckdb.DuckDBPyConnection) -> None:
    """Create or replace the four summary tables from existing CSV transform outputs."""
    _load_summary_csv(dw, "summary_kpis", "outputs/kpis.csv")
    _load_summary_csv(dw, "summary_monthly", "outputs/monthly.csv")
    _load_summary_csv(dw, "summary_loss_ratio", "outputs/loss_ratio.csv")
    _load_summary_csv(dw, "summary_network", "outputs/network_summary.csv")


def run_dw_load(path: str = _DEFAULT_DW_PATH) -> None:
    """Orchestrate the full DW load: dimensions → fact table → summary tables."""
    engine = get_engine()
    dw = get_dw_conn(path)
    try:
        load_dim_member(dw, engine)
        load_dim_provider(dw, engine)
        load_dim_date(dw)
        load_fact_claims(dw, engine)
        load_summaries(dw)
        # Run lightweight DW quality checks (row counts, PK uniqueness, referential integrity)
        try:
            results = run_quality_checks(dw)
        except Exception:
            logger.exception("DW quality checks failed")
            raise
        _write_qa_report(results)
        logger.info("DW load complete → %s", path)
        logger.info("DW quality checks: %s", results)
    finally:
        dw.close()


def _write_qa_report(results: dict, report_dir: str = "build/reports") -> None:
    """Persist quality-check results as a timestamped JSON file in *report_dir*."""
    os.makedirs(report_dir, exist_ok=True)
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "checks": results,
    }
    dest = os.path.join(report_dir, "dw_quality.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    logger.info("DW QA report written → %s", dest)


if __name__ == "__main__":
    dw_path = os.getenv("DW_PATH", _DEFAULT_DW_PATH)
    run_dw_load(dw_path)
