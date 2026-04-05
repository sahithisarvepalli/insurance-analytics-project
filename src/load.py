"""Load insurance data (Kaggle or client CSV) into the PostgreSQL database."""

import argparse
from importlib import resources

from sqlalchemy import inspect, text

from .utils import get_engine, logger

_SCHEMA = "insurance"
_IF_EXISTS = "append"


def _read_ddl() -> str:
    """Return the canonical DDL SQL bundled with the package."""
    ref = resources.files("src.sql").joinpath("ddl_create_tables.sql")
    return ref.read_text(encoding="utf-8")


def _apply_ddl(con) -> None:
    """Drop and recreate the insurance schema using the canonical DDL file."""
    con.execute(text(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE;"))
    ddl = _read_ddl()
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(text(stmt))


def _table_columns(con, table: str) -> list:
    """Return column names for *table* by reflecting the live DB schema."""
    return [col["name"] for col in inspect(con).get_columns(table, schema=_SCHEMA)]


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
    _insert_dataframes(dfs["members"], dfs["providers"], dfs["claims"])
    logger.info("Done loading Kaggle data.")


def _insert_dataframes(
    members_df,
    providers_df,
    claims_df,
) -> None:
    """Apply DDL, trim columns to schema, and insert all three DataFrames."""
    eng = get_engine()

    with eng.begin() as con:
        _apply_ddl(con)
        member_cols = _table_columns(con, "member")
        provider_cols = _table_columns(con, "provider")
        claim_cols = _table_columns(con, "claim")

    members_df = members_df[[c for c in member_cols if c in members_df.columns]]
    providers_df = providers_df[[c for c in provider_cols if c in providers_df.columns]]
    claims_df = claims_df[[c for c in claim_cols if c in claims_df.columns]]

    members_df.to_sql("member", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
    providers_df.to_sql("provider", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)
    claims_df.to_sql("claim", eng, schema=_SCHEMA, if_exists=_IF_EXISTS, index=False)


def load_from_client_csv(config_path: str) -> None:
    """Load a client's CSV dataset into the database using a client config file.

    Reads file paths and column mappings from *config_path* (e.g.
    ``config/clients/client_a.yaml``).  No external credentials are required —
    the CSV files must already exist locally at the paths declared in the config.

    Parameters
    ----------
    config_path:
        Path to a client YAML config file under ``config/clients/``.
    """
    from .client_ingest import load_client_data  # noqa: PLC0415

    dfs = load_client_data(config_path)
    _insert_dataframes(dfs["members"], dfs["providers"], dfs["claims"])
    logger.info("Done loading client CSV data from '%s'.", config_path)


def main(parsed_args):
    """Entry point: load data (Kaggle or client CSV) into the database."""
    if parsed_args.client_config:
        load_from_client_csv(parsed_args.client_config)
    else:
        load_from_kaggle(parsed_args.kaggle_config)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Load insurance data (Kaggle or client CSV) into PostgreSQL."
    )
    ap.add_argument(
        "--kaggle-config",
        default="config/kaggle.yaml",
        help="Path to the Kaggle dataset YAML config.",
    )
    ap.add_argument(
        "--client-config",
        default=None,
        help="Path to a client CSV YAML config (e.g. config/clients/client_a.yaml). "
        "When provided, client CSV data is loaded instead of Kaggle.",
    )
    main(ap.parse_args())
