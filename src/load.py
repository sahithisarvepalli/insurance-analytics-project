"""Load insurance data from CSV files or a Kaggle dataset into the PostgreSQL database."""

import argparse

import pandas as pd
from sqlalchemy import text

from .utils import get_engine, logger

_SCHEMA = "insurance"
_IF_EXISTS = "append"
_PARSE_ERRORS = "coerce"


def load_from_csv(members, providers, claims):
    """Load member, provider, and claims data from CSV files into the database."""
    eng = get_engine()

    def read_datesafe(path, date_cols):
        """Read a CSV file and parse specified columns as dates, handling epoch-ns strings."""
        # Load date columns as strings, then normalize
        df = pd.read_csv(path, dtype=dict.fromkeys(date_cols, "string"))
        for col in date_cols:
            s = df[col].fillna("")
            # Detect 15–19 digit epoch ns strings
            mask_ns = s.str.match(r"^\d{15,19}$")
            if mask_ns.any():
                s_ns = pd.to_datetime(s.where(mask_ns, None), errors=_PARSE_ERRORS, unit="ns")
                s_iso = pd.to_datetime(s.where(~mask_ns, None), errors=_PARSE_ERRORS)
                df[col] = s_ns.fillna(s_iso)
            else:
                df[col] = pd.to_datetime(s, errors=_PARSE_ERRORS)
        return df

    # Read all CSVs before opening any DB connection
    members_df = read_datesafe(members, ["dob", "effective_date", "termination_date"])
    providers_df = pd.read_csv(providers)
    claims_df = read_datesafe(claims, ["service_date"])

    # All three writes inside one transaction — partial loads roll back on failure.
    # Uses truncate-then-load to stay idempotent across repeated / scheduled runs.
    with eng.begin() as con:
        con.execute(text("CREATE SCHEMA IF NOT EXISTS insurance;"))
        con.execute(text("TRUNCATE insurance.claim, insurance.provider, insurance.member RESTART IDENTITY CASCADE;"))
        members_df.to_sql("member", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        providers_df.to_sql("provider", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        claims_df.to_sql("claim", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)

    logger.info("Done loading CSVs.")


def load_from_kaggle(config_path: str = "config/kaggle.yaml") -> None:
    """Download (if needed) a Kaggle dataset and load it into the database.

    Reads dataset configuration and column mappings from *config_path*
    (default: ``config/kaggle.yaml``).  The Kaggle credentials must be
    available via the ``KAGGLE_USERNAME`` / ``KAGGLE_KEY`` environment
    variables or ``~/.kaggle/kaggle.json``.

    Parameters
    ----------
    config_path:
        Path to the Kaggle YAML configuration file.
    """
    from .kaggle_ingest import load_kaggle_data  # noqa: PLC0415

    dfs = load_kaggle_data(config_path)
    members_df = dfs["members"]
    providers_df = dfs["providers"]
    claims_df = dfs["claims"]

    eng = get_engine()
    with eng.begin() as con:
        con.execute(text("CREATE SCHEMA IF NOT EXISTS insurance;"))
        con.execute(text("TRUNCATE insurance.claim, insurance.provider, insurance.member RESTART IDENTITY CASCADE;"))
        members_df.to_sql("member", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        providers_df.to_sql("provider", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        claims_df.to_sql("claim", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)

    logger.info("Done loading Kaggle data.")


def main(parsed_args):
    """Entry point: dispatch to the appropriate load function based on CLI flags."""
    if parsed_args.from_kaggle:
        load_from_kaggle(parsed_args.kaggle_config)
    elif parsed_args.from_csv:
        load_from_csv(parsed_args.members, parsed_args.providers, parsed_args.claims)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--from-csv",
        action="store_true",
        help="Load from local CSV files (default source).",
    )
    ap.add_argument(
        "--from-kaggle",
        action="store_true",
        help="Download and load a Kaggle dataset (requires credentials).",
    )
    ap.add_argument("--members", default="data/sample_members.csv")
    ap.add_argument("--providers", default="data/sample_providers.csv")
    ap.add_argument("--claims", default="data/sample_claims.csv")
    ap.add_argument(
        "--kaggle-config",
        default="config/kaggle.yaml",
        help="Path to the Kaggle dataset YAML config (used with --from-kaggle).",
    )
    main(ap.parse_args())
