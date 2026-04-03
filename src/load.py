"""Load a Kaggle insurance dataset into the PostgreSQL database."""

import argparse

from sqlalchemy import text

from .utils import get_engine, logger

_SCHEMA = "insurance"
_IF_EXISTS = "append"

# Canonical columns for each table — extras from the source are dropped before insert.
_MEMBER_COLS = [
    "member_id",
    "person_id",
    "dob",
    "gender",
    "region",
    "effective_date",
    "termination_date",
]
_PROVIDER_COLS = ["provider_id", "specialty", "in_network", "region"]
_CLAIM_COLS = [
    "member_id",
    "provider_id",
    "service_date",
    "diagnosis_code",
    "procedure_code",
    "billed_amount",
    "allowed_amount",
    "paid_amount",
    "place_of_service",
]


def load_from_kaggle(config_path: str = "config/kaggle.yaml") -> None:
    """Download (if needed) a Kaggle dataset and load it into the database.

    Reads dataset configuration and column mappings from *config_path*
    (default: ``config/kaggle.yaml``).  Kaggle credentials must be available
    via the ``KAGGLE_USERNAME`` / ``KAGGLE_KEY`` environment variables or
    ``~/.kaggle/kaggle.json``.

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
        con.execute(text("DROP TABLE IF EXISTS insurance.claim CASCADE;"))
        con.execute(text("DROP TABLE IF EXISTS insurance.provider CASCADE;"))
        con.execute(text("DROP TABLE IF EXISTS insurance.member CASCADE;"))
        con.execute(
            text(
                """
            CREATE TABLE insurance.member (
              member_id BIGSERIAL PRIMARY KEY,
              person_id BIGINT,
              dob DATE,
              gender VARCHAR(10),
              region VARCHAR(50),
              effective_date DATE,
              termination_date DATE
            );
        """
            )
        )
        con.execute(
            text(
                """
            CREATE TABLE insurance.provider (
              provider_id BIGSERIAL PRIMARY KEY,
              specialty VARCHAR(80),
              in_network BOOLEAN,
              region VARCHAR(50)
            );
        """
            )
        )
        con.execute(
            text(
                """
            CREATE TABLE insurance.claim (
              claim_id BIGSERIAL PRIMARY KEY,
              member_id BIGINT REFERENCES insurance.member(member_id),
              provider_id BIGINT REFERENCES insurance.provider(provider_id),
              service_date DATE,
              diagnosis_code VARCHAR(8),
              procedure_code VARCHAR(8),
              billed_amount NUMERIC(12,2),
              allowed_amount NUMERIC(12,2),
              paid_amount NUMERIC(12,2),
              place_of_service VARCHAR(20)
            );
        """
            )
        )
    members_df = members_df[[c for c in _MEMBER_COLS if c in members_df.columns]]
    providers_df = providers_df[[c for c in _PROVIDER_COLS if c in providers_df.columns]]
    claims_df = claims_df[[c for c in _CLAIM_COLS if c in claims_df.columns]]

    members_df.to_sql("member", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
    providers_df.to_sql("provider", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
    claims_df.to_sql("claim", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)

    logger.info("Done loading Kaggle data.")


def main(parsed_args):
    """Entry point: load a Kaggle dataset into the database."""
    load_from_kaggle(parsed_args.kaggle_config)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load a Kaggle insurance dataset into PostgreSQL.")
    ap.add_argument(
        "--kaggle-config",
        default="config/kaggle.yaml",
        help="Path to the Kaggle dataset YAML config.",
    )
    main(ap.parse_args())
