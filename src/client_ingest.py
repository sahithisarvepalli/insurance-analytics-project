"""Client CSV ingestion — load and map client-supplied CSV files to the pipeline schema.

Usage
-----
1. Create a client config YAML under ``config/clients/<client_id>.yaml`` that
   specifies the CSV file path and column mappings::

       client_id: acme
       client_name: "Acme Health Plans"
       files:
         claims: data/clients/acme/claims.csv
       column_map:
         claims:
           charge_amt: paid_amount
           patient_id: member_id
       defaults:
         claims:
           billed_amount: 0.0

2. Run the loader::

       python -m src.load --client-config config/clients/acme.yaml
"""

from __future__ import annotations

import logging
import os

import pandas as pd
import yaml

from .kaggle_ingest import (
    _SCHEMA_DEFAULTS,
    _apply_mapping,
    _ensure_claims_keys,
    _validate_member_fk,
    _validate_provider_fk,
)

logger = logging.getLogger(__name__)


def _parse_client_config(
    config_path: str,
) -> tuple[str, str, dict, dict, dict]:
    """Read *config_path* and return ``(client_id, client_name, files, col_maps, user_defaults)``.

    Raises
    ------
    ValueError
        If ``client_id`` or ``files`` is missing from the config.
    """
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    if not isinstance(cfg, dict):
        raise ValueError(
            f"Client config '{config_path}' is not a valid YAML mapping "
            f"(got {type(cfg).__name__ if cfg is not None else 'empty file'})."
        )

    client_id: str = cfg.get("client_id") or ""
    if not client_id:
        raise ValueError(f"Client config '{config_path}' is missing required field 'client_id'.")
    client_name: str = cfg.get("client_name", client_id)
    files: dict = cfg.get("files", {})
    col_maps: dict = cfg.get("column_map", {})
    user_defaults: dict = cfg.get("defaults", {})

    if not files:
        raise ValueError(
            f"Client config '{config_path}' has no 'files' section. "
            "At minimum, a 'claims' file must be configured."
        )

    return client_id, client_name, files, col_maps, user_defaults


def _load_client_role_files(
    files: dict,
    col_maps: dict,
    user_defaults: dict,
) -> dict[str, pd.DataFrame]:
    """Read each configured CSV file into a DataFrame and apply column mapping.

    Parameters
    ----------
    files:
        ``{role: filepath}`` pairs, e.g. ``{"claims": "data/clients/acme/claims.csv"}``.
    col_maps:
        Per-role column rename maps ``{role: {src_col: tgt_col}}``.
    user_defaults:
        Per-role default column values ``{role: {col: value}}``.

    Returns
    -------
    dict[str, pd.DataFrame]
        DataFrames keyed by role after column mapping and defaults are applied.
    """
    result: dict[str, pd.DataFrame] = {}
    for role, filepath in files.items():
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Expected client file '{filepath}' not found. "
                "Check the 'files' section in the client config."
            )
        df = pd.read_csv(filepath)
        merged_defaults = {**_SCHEMA_DEFAULTS.get(role, {}), **user_defaults.get(role, {})}
        df = _apply_mapping(df, col_maps.get(role, {}), merged_defaults)
        result[role] = df
        logger.info("Loaded %d rows for role '%s' from %s", len(df), role, filepath)
    return result


def load_client_data(config_path: str) -> dict[str, pd.DataFrame]:
    """Load and map a client's CSV files to the pipeline schema.

    Reads *config_path* to determine file paths and column mappings.  Members
    and providers are derived automatically from claims data when separate files
    are not configured.

    Parameters
    ----------
    config_path:
        Path to a client YAML config file (e.g. ``config/clients/client_a.yaml``).

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are ``"members"``, ``"providers"``, and ``"claims"``.

    Raises
    ------
    ValueError
        If ``files`` is missing or no ``claims`` file is configured.
    FileNotFoundError
        If a configured CSV file does not exist on disk.
    """
    client_id, client_name, files, col_maps, user_defaults = _parse_client_config(config_path)
    logger.info("Loading data for client '%s' (%s)", client_name, client_id)

    result = _load_client_role_files(files, col_maps, user_defaults)

    if "claims" not in result:
        raise ValueError(
            "Client config must include at least a 'claims' file mapping. "
            "Check the 'files' section in the client config."
        )

    result = _ensure_claims_keys(result)

    if "members" in files:
        _validate_member_fk(result)
    if "providers" in files:
        _validate_provider_fk(result)

    return result
