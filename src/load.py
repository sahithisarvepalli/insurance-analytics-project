"""Load a Kaggle insurance dataset into the PostgreSQL database."""

import argparse

from sqlalchemy import text

from .utils import get_engine, logger

_SCHEMA = "insurance"
_IF_EXISTS = "append"


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
        con.execute(
            text(
                "TRUNCATE insurance.claim, insurance.provider, insurance.member "
                "RESTART IDENTITY CASCADE;"
            )
        )
        members_df.to_sql("member", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        providers_df.to_sql("provider", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
        claims_df.to_sql("claim", con, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)

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
