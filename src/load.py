import argparse

import pandas as pd
from sqlalchemy import text

from .utils import get_engine, logger


def load_from_csv(members, providers, claims):
    eng = get_engine()

    def read_datesafe(path, date_cols):
        # Load date columns as strings, then normalize
        df = pd.read_csv(path, dtype=dict.fromkeys(date_cols, "string"))
        for col in date_cols:
            s = df[col].fillna("")
            # Detect 15–19 digit epoch ns strings
            mask_ns = s.str.match(r"^\d{15,19}$")
            if mask_ns.any():
                s_ns = pd.to_datetime(s.where(mask_ns, None), errors="coerce", unit="ns")
                s_iso = pd.to_datetime(s.where(~mask_ns, None), errors="coerce")
                df[col] = s_ns.fillna(s_iso)
            else:
                df[col] = pd.to_datetime(s, errors="coerce")
        return df

    # Read all CSVs before opening any DB connection
    members_df = read_datesafe(members, ["dob", "effective_date", "termination_date"])
    providers_df = pd.read_csv(providers)
    claims_df = read_datesafe(claims, ["service_date"])

    # All three writes inside one transaction — partial loads roll back on failure.
    # Uses truncate-then-load to stay idempotent across repeated / scheduled runs.
    with eng.begin() as con:
        con.execute(text("CREATE SCHEMA IF NOT EXISTS insurance;"))
        con.execute(text("TRUNCATE insurance.claim, insurance.provider, insurance.member CASCADE;"))
        members_df.to_sql("member", con, schema="insurance", if_exists="append", index=False)
        providers_df.to_sql("provider", con, schema="insurance", if_exists="append", index=False)
        claims_df.to_sql("claim", con, schema="insurance", if_exists="append", index=False)

    logger.info("Done loading CSVs.")


def main(parsed_args):
    if parsed_args.from_csv:
        load_from_csv(parsed_args.members, parsed_args.providers, parsed_args.claims)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-csv", action="store_true")
    ap.add_argument("--members", default="data/sample_members.csv")
    ap.add_argument("--providers", default="data/sample_providers.csv")
    ap.add_argument("--claims", default="data/sample_claims.csv")
    main(ap.parse_args())
