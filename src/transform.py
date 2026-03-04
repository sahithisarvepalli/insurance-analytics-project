
import os
import pandas as pd
from .utils import get_engine, logger


def run_transform():
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
    logger.info(f"Loaded {len(df):,} joined rows")

    today = pd.Timestamp("2024-12-31")
    df["age"] = (today - df["dob"]).dt.days // 365
    df["age_band"] = pd.cut(
        df["age"], bins=[0,18,30,45,60,200], labels=["0-18","19-30","31-45","46-60","60+"]
    )

    kpis = (
        df.groupby(["age_band","member_region","in_network"], dropna=False)
        .agg(claims=("claim_id","count"), paid_total=("paid_amount","sum"), paid_avg=("paid_amount","mean"))
        .reset_index()
    )

    df["month"] = df["service_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby(["month","member_region","in_network"]) 
        .agg(claims=("claim_id","count"), paid_total=("paid_amount","sum"))
        .reset_index()
    )

    os.makedirs('outputs', exist_ok=True)
    kpis.to_csv('outputs/kpis.csv', index=False)
    monthly.to_csv('outputs/monthly.csv', index=False)
    logger.info('Wrote outputs/kpis.csv and outputs/monthly.csv')


if __name__ == '__main__':
    run_transform()
