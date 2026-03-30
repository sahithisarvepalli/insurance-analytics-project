"""Transform raw insurance claims data into KPI summaries and monthly aggregations."""

import os

import pandas as pd

from .utils import get_engine, logger

_PAID_AMOUNT_COL = "paid_amount"


def run_transform():
    """Run the full claims transformation pipeline and write CSV outputs."""
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

    # KPIs
    kpis = (
        df.groupby(["age_band", "member_region", "in_network"], dropna=False, observed=True)
        .agg(
            claims=("claim_id", "count"),
            paid_total=(_PAID_AMOUNT_COL, "sum"),
            paid_avg=(_PAID_AMOUNT_COL, "mean"),
        )
        .reset_index()
    )

    # Monthly summary
    df["month"] = df["service_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby(["month", "member_region", "in_network"])
        .agg(claims=("claim_id", "count"), paid_total=(_PAID_AMOUNT_COL, "sum"))
        .reset_index()
    )

    # Persist
    os.makedirs("outputs", exist_ok=True)
    kpis.to_csv("outputs/kpis.csv", index=False)
    monthly.to_csv("outputs/monthly.csv", index=False)
    logger.info("Wrote outputs/kpis.csv and outputs/monthly.csv")


if __name__ == "__main__":
    run_transform()
