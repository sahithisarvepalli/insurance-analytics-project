"""Load a Kaggle insurance dataset into the PostgreSQL database."""

import argparse
import pathlib

from sqlalchemy import inspect, text

from .utils import get_engine, logger

_SCHEMA = "insurance"
_IF_EXISTS = "append"

# Single source of truth for the schema — Python never re-declares column names.
_DDL_PATH = pathlib.Path(__file__).parent.parent / "sql" / "ddl_create_tables.sql"


def _apply_ddl(con) -> None:
    """Drop and recreate the insurance schema using the canonical DDL file."""
    con.execute(text("DROP SCHEMA IF EXISTS insurance CASCADE;"))
    ddl = _DDL_PATH.read_text(encoding="utf-8")
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(text(stmt))


def _table_columns(eng, table: str) -> list:
    """Return column names for *table* by reflecting the live DB schema."""
    return [col["name"] for col in inspect(eng).get_columns(table, schema=_SCHEMA)]


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
        _apply_ddl(con)

    # Reflect column names from the live schema — trims any source columns not in the table.
    members_df = members_df[[c for c in _table_columns(eng, "member") if c in members_df.columns]]
    providers_df = providers_df[
        [c for c in _table_columns(eng, "provider") if c in providers_df.columns]
    ]
    claims_df = claims_df[[c for c in _table_columns(eng, "claim") if c in claims_df.columns]]

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
