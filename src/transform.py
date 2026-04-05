"""Transform raw insurance claims data into KPI summaries and monthly aggregations."""

import argparse
import os

import pandas as pd

from .utils import get_engine, logger

_PAID_AMOUNT_COL = "paid_amount"
_BILLED_AMOUNT_COL = "billed_amount"
_ALLOWED_AMOUNT_COL = "allowed_amount"


def run_transform(output_dir: str = "outputs"):
    """Run the full claims transformation pipeline and write CSV outputs.

    Parameters
    ----------
    output_dir:
        Directory where output CSV files are written.  Defaults to ``"outputs"``.
        Pass a client-specific path (e.g. ``"outputs/client_a"``) to isolate
        per-client reports.
    """
    eng = get_engine()

    q = """
    SELECT
        c.claim_id,
        c.member_id,
        c.provider_id,
        c.service_date,
        c.billed_amount,
        c.allowed_amount,
        c.paid_amount,
        c.place_of_service,
        c.diagnosis_code,
        c.procedure_code,
        m.dob,
        m.region AS member_region,
        m.effective_date,
        p.in_network
    FROM insurance.claim c
    JOIN insurance.member m ON c.member_id = m.member_id
    JOIN insurance.provider p ON c.provider_id = p.provider_id
    """

    df = pd.read_sql(q, eng, parse_dates=["service_date", "dob", "effective_date"])
    logger.info("Loaded %d joined rows", len(df))

    # Derivations
    today = pd.Timestamp.now().normalize()
    df["age"] = (today - df["dob"]).dt.days // 365
    df["age_band"] = pd.cut(
        df["age"],
        bins=[0, 18, 30, 45, 60, 200],
        labels=["0-18", "19-30", "31-45", "46-60", "60+"],
    )

    # KPIs — claim counts, paid totals, and averages by age band / region / network
    kpis = (
        df.groupby(["age_band", "member_region", "in_network"], dropna=False, observed=True)
        .agg(
            claims=("claim_id", "count"),
            paid_total=(_PAID_AMOUNT_COL, "sum"),
            paid_avg=(_PAID_AMOUNT_COL, "mean"),
        )
        .reset_index()
    )

    # Monthly summary — claim counts and paid totals by calendar month / region / network
    df["month"] = df["service_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby(["month", "member_region", "in_network"])
        .agg(claims=("claim_id", "count"), paid_total=(_PAID_AMOUNT_COL, "sum"))
        .reset_index()
    )

    # Loss ratio — paid vs billed vs allowed amounts by region / network
    # Loss ratio = paid_amount / billed_amount * 100 (where billed_amount > 0)
    loss_ratio = (
        df.groupby(["member_region", "in_network"], dropna=False)
        .agg(
            claims=("claim_id", "count"),
            billed_total=(_BILLED_AMOUNT_COL, "sum"),
            allowed_total=(_ALLOWED_AMOUNT_COL, "sum"),
            paid_total=(_PAID_AMOUNT_COL, "sum"),
        )
        .reset_index()
    )
    billed_positive = loss_ratio["billed_total"] > 0
    loss_ratio["loss_ratio_pct"] = (
        (loss_ratio["paid_total"] / loss_ratio["billed_total"].where(billed_positive) * 100)
        .where(billed_positive)
        .round(2)
    )
    loss_ratio["allowed_ratio_pct"] = (
        (loss_ratio["allowed_total"] / loss_ratio["billed_total"].where(billed_positive) * 100)
        .where(billed_positive)
        .round(2)
    )

    # Network utilization — in-network vs out-of-network claim and cost summary
    network_summary = (
        df.groupby("in_network", dropna=False)
        .agg(
            claims=("claim_id", "count"),
            paid_total=(_PAID_AMOUNT_COL, "sum"),
            paid_avg=(_PAID_AMOUNT_COL, "mean"),
        )
        .reset_index()
    )
    total_claims = network_summary["claims"].sum()
    network_summary["utilization_pct"] = (network_summary["claims"] / total_claims * 100).round(2)

    # Diagnosis summary — claims and costs by ICD diagnosis code
    diagnosis_summary = (
        df.groupby("diagnosis_code", dropna=False)
        .agg(
            claims=("claim_id", "count"),
            paid_total=(_PAID_AMOUNT_COL, "sum"),
            paid_avg=(_PAID_AMOUNT_COL, "mean"),
            billed_total=(_BILLED_AMOUNT_COL, "sum"),
        )
        .reset_index()
        .sort_values("paid_total", ascending=False)
    )

    # Persist
    os.makedirs(output_dir, exist_ok=True)
    kpis.to_csv(os.path.join(output_dir, "kpis.csv"), index=False)
    monthly.to_csv(os.path.join(output_dir, "monthly.csv"), index=False)
    loss_ratio.to_csv(os.path.join(output_dir, "loss_ratio.csv"), index=False)
    network_summary.to_csv(os.path.join(output_dir, "network_summary.csv"), index=False)
    diagnosis_summary.to_csv(os.path.join(output_dir, "diagnosis_summary.csv"), index=False)
    logger.info(
        "Wrote %s/{kpis,monthly,loss_ratio,network_summary,diagnosis_summary}.csv",
        output_dir,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the insurance claims transformation pipeline.")
    ap.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to write output CSV files (default: outputs).",
    )
    args = ap.parse_args()
    run_transform(output_dir=args.output_dir)
