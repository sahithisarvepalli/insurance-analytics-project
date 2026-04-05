"""Load insurance data (Kaggle or client CSV) into the PostgreSQL database."""

import argparse
from importlib import resources

import pandas as pd
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

    # Map non-numeric external IDs to surrogate BIGINT keys expected by the
    # canonical DDL. If a client provides string IDs (eg. 'P01') we create a
    # numeric mapping and rewrite both the dimension and claim foreign keys.
    def _map_to_surrogate(dim_df: pd.DataFrame, key: str, fk_df: pd.DataFrame):
        if key not in dim_df.columns or key not in fk_df.columns:
            return dim_df, fk_df
        # If values are already integer-like, leave alone
        if pd.api.types.is_integer_dtype(dim_df[key]) and pd.api.types.is_integer_dtype(fk_df[key]):
            return dim_df, fk_df

        # If all non-null dimension values are purely numeric strings (e.g. "1001"),
        # preserve their original numeric values instead of assigning new surrogates.
        numeric_dim = pd.to_numeric(dim_df[key], errors="coerce")
        if numeric_dim.isna().sum() == dim_df[key].isna().sum():
            dim_df = dim_df.copy()
            dim_df[key] = numeric_dim.astype("Int64")
            fk_df = fk_df.copy()
            fk_df[key] = pd.to_numeric(fk_df[key], errors="coerce").astype("Int64")
            return dim_df, fk_df

        # Create consistent mapping based on the dimension's non-null unique values.
        # Use pandas' nullable string dtype so missing values remain missing instead
        # of becoming the literal strings "nan"/"<NA>".
        orig_vals = dim_df[key].astype("string")
        uniques = pd.Series(orig_vals.dropna().unique())
        mapping = {orig: i + 1 for i, orig in enumerate(uniques)}

        fk_ids = fk_df[key].astype("string")
        missing_mask = fk_ids.notna() & ~fk_ids.isin(mapping)
        if missing_mask.any():
            missing_ids = fk_ids[missing_mask].drop_duplicates().tolist()
            sample = ", ".join(repr(v) for v in missing_ids[:5])
            extra = "" if len(missing_ids) <= 5 else f" (and {len(missing_ids) - 5} more)"
            raise ValueError(
                f"Found unmapped non-null values for foreign key '{key}' while rewriting "
                f"surrogate keys: {sample}{extra}"
            )

        dim_df = dim_df.copy()
        dim_df[key] = orig_vals.map(mapping).astype("Int64")

        fk_df = fk_df.copy()
        fk_df[key] = fk_ids.map(mapping).astype("Int64")
        return dim_df, fk_df

    providers_df, claims_df = _map_to_surrogate(providers_df, "provider_id", claims_df)
    members_df, claims_df = _map_to_surrogate(members_df, "member_id", claims_df)

    # claim_id is BIGSERIAL and not referenced by any FK; drop string values
    # so Postgres auto-generates valid integer PKs.
    claims_df = claims_df.drop(columns=["claim_id"], errors="ignore")

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
