"""Kaggle dataset ingestion — download and map external datasets to the pipeline schema.

Usage
-----
1. Set credentials::

    export KAGGLE_USERNAME=your_username
    export KAGGLE_KEY=your_api_key

   Or place ``~/.kaggle/kaggle.json`` (downloaded from kaggle.com → Account → API).

2. Configure the dataset in ``config/kaggle.yaml`` (select ``active_dataset`` and fill
   the matching ``column_map`` / ``defaults`` entries).

3. Run the loader::

    python -m src.load --from-kaggle
    # or with a custom config path:
    python -m src.load --from-kaggle --kaggle-config path/to/kaggle.yaml
"""

from __future__ import annotations

import logging
import os
import pathlib

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = "config/kaggle.yaml"

# ────────────────────────────────────────────────────────────────────────────
# Schema-level defaults injected when a required column is absent in the source
# ────────────────────────────────────────────────────────────────────────────
_SCHEMA_DEFAULTS: dict[str, dict] = {
    "members": {
        "person_id": None,
        "gender": "U",
        "region": "Unknown",
        "effective_date": "2023-01-01",
        "termination_date": None,
    },
    "providers": {
        "specialty": "Unknown",
        "in_network": True,
        "region": "Unknown",
    },
    "claims": {
        "billed_amount": 0.0,
        "allowed_amount": 0.0,
        "place_of_service": "Office",
        "procedure_code": "99213",
        "service_date": "2023-01-01",
        "diagnosis_code": "Z00",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# Credential helpers
# ────────────────────────────────────────────────────────────────────────────


def _ensure_kaggle_credentials() -> None:
    """Verify Kaggle credentials are available; raise ``EnvironmentError`` if missing."""
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return
    if (pathlib.Path.home() / ".kaggle" / "kaggle.json").exists():
        return
    raise OSError(
        "Kaggle credentials not found. "
        "Set the KAGGLE_USERNAME and KAGGLE_KEY environment variables, "
        "or place your API token at ~/.kaggle/kaggle.json. "
        "See https://www.kaggle.com/docs/api for instructions."
    )


# ────────────────────────────────────────────────────────────────────────────
# Download
# ────────────────────────────────────────────────────────────────────────────


def download_dataset(owner: str, dataset: str, dest_dir: str = "data/kaggle") -> str:
    """Download a Kaggle dataset, unzip it, and return the destination directory.

    Parameters
    ----------
    owner:
        Kaggle username or organisation that owns the dataset.
    dataset:
        Dataset slug as it appears in the Kaggle URL.
    dest_dir:
        Local directory to store the extracted files.

    Returns
    -------
    str
        Absolute path to *dest_dir* after the download.
    """
    _ensure_kaggle_credentials()
    import kaggle  # noqa: PLC0415  (lazy import keeps kaggle optional at module load time)

    os.makedirs(dest_dir, exist_ok=True)
    logger.info("Downloading Kaggle dataset %s/%s …", owner, dataset)
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        f"{owner}/{dataset}",
        path=dest_dir,
        unzip=True,
        quiet=False,
    )
    logger.info("Download complete → %s", dest_dir)
    return dest_dir


# ────────────────────────────────────────────────────────────────────────────
# Mapping helpers
# ────────────────────────────────────────────────────────────────────────────


def _apply_mapping(df: pd.DataFrame, col_map: dict, defaults: dict) -> pd.DataFrame:
    """Rename columns per *col_map* and inject *defaults* for absent columns.

    Parameters
    ----------
    df:
        Source DataFrame loaded from the Kaggle file.
    col_map:
        ``{source_column: target_column}`` rename pairs.  Only columns that
        are present in *df* are renamed; extra entries are silently ignored.
    defaults:
        ``{column_name: value}`` pairs added when the column is absent.
        Values may be scalars or callables that accept the DataFrame length.

    Returns
    -------
    pd.DataFrame
        Transformed copy of *df*.
    """
    rename = {src: tgt for src, tgt in col_map.items() if src in df.columns}
    df = df.rename(columns=rename)
    for col, val in defaults.items():
        if col not in df.columns:
            if callable(val):
                try:
                    df[col] = val(len(df))
                except TypeError:
                    # Fall back to zero-argument callables for backward compatibility.
                    df[col] = val()
            else:
                df[col] = val
    return df


# ────────────────────────────────────────────────────────────────────────────
# Derivation helpers (used when members / providers are not in the dataset)
# ────────────────────────────────────────────────────────────────────────────


def _derive_members(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Build a *members* DataFrame from unique ``member_id`` values in claims.

    When the claims data contains demographic columns produced by Kaggle column
    mapping (``age``, ``gender``, ``region``) those values are used directly.
    Otherwise, schema-level defaults are applied.  No random data is generated.
    """
    unique_claims = claims_df.drop_duplicates(subset=["member_id"]).reset_index(drop=True)
    member_ids = unique_claims["member_id"].values

    # Derive DOB from age when available, otherwise use a fixed reference date
    # Use 365.25 days/year to account for leap years in the conversion.
    if "age" in unique_claims.columns:
        today = pd.Timestamp.now().normalize()
        dob: pd.Series = today - pd.to_timedelta(
            pd.to_numeric(unique_claims["age"], errors="coerce").fillna(0) * 365.25,
            unit="D",
        )
    else:
        dob = pd.Series([pd.NaT] * len(unique_claims))

    gender = unique_claims["gender"].values if "gender" in unique_claims.columns else "U"
    region = unique_claims["region"].values if "region" in unique_claims.columns else "Unknown"

    return pd.DataFrame(
        {
            "member_id": member_ids,
            "person_id": member_ids,
            "dob": dob.values,
            "gender": gender,
            "region": region,
            "effective_date": pd.Timestamp("2023-01-01"),
            "termination_date": pd.NaT,
        }
    )


def _derive_providers(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Build a *providers* DataFrame from unique ``provider_id`` values in claims.

    Typical Kaggle insurance datasets do not contain provider-level attributes; schema defaults are
    applied.  No random data is generated.
    """
    provider_ids = claims_df["provider_id"].dropna().unique()
    return pd.DataFrame(
        {
            "provider_id": provider_ids,
            "specialty": "Unknown",
            "in_network": True,
            "region": "Unknown",
        }
    )


# ────────────────────────────────────────────────────────────────────────────
# Public API helpers
# ────────────────────────────────────────────────────────────────────────────


def _parse_dataset_config(
    config_path: str,
    active_dataset: str | None = None,
) -> tuple[str, str, str, dict, dict, dict]:
    """Read *config_path* and return ``(owner, dataset, dest_dir, files, col_maps, user_defaults)``.

    Parameters
    ----------
    active_dataset:
        Override the ``active_dataset`` key from the YAML file.  Useful for
        selecting a non-default dataset at runtime without editing the config.

    Raises
    ------
    ValueError
        If ``active_dataset`` is missing.
    KeyError
        If the named ``active_dataset`` is not defined under ``datasets``.
    """
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    active = active_dataset or cfg.get("active_dataset")
    if not active:
        raise ValueError("'active_dataset' is not set in the Kaggle config.")

    datasets = cfg.get("datasets", {})
    if active not in datasets:
        raise KeyError(
            f"Dataset '{active}' not found in config. "
            f"Available datasets: {list(datasets.keys())}"
        )

    dataset_cfg = datasets[active]
    owner: str = dataset_cfg["owner"]
    dataset: str = dataset_cfg["dataset"]
    dest_dir: str = dataset_cfg.get("dest_dir", f"data/kaggle/{active}")
    files: dict = dataset_cfg.get("files", {})
    col_maps: dict = dataset_cfg.get("column_map", {})
    user_defaults: dict = dataset_cfg.get("defaults", {})
    return owner, dataset, dest_dir, files, col_maps, user_defaults


def _needs_download(dest_dir: str, files: dict) -> bool:
    """Return ``True`` when the dataset must be (re-)downloaded."""
    if not os.path.isdir(dest_dir):
        return True
    if files:
        return any(
            not os.path.isfile(os.path.join(dest_dir, filename)) for filename in files.values()
        )
    return not any(f.lower().endswith(".csv") for f in os.listdir(dest_dir))


def _load_role_files(
    dest_dir: str,
    files: dict,
    col_maps: dict,
    user_defaults: dict,
) -> dict[str, pd.DataFrame]:
    """Read each configured file into a DataFrame and apply column mapping."""
    result: dict[str, pd.DataFrame] = {}
    for role, filename in files.items():
        path = os.path.join(dest_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Expected file '{filename}' not found at '{path}'. "
                "Check the 'files' section in config/kaggle.yaml."
            )
        df = pd.read_csv(path)
        merged_defaults = {**_SCHEMA_DEFAULTS.get(role, {}), **user_defaults.get(role, {})}
        df = _apply_mapping(df, col_maps.get(role, {}), merged_defaults)
        result[role] = df
        logger.info("Loaded %d rows for role '%s' from %s", len(df), role, path)
    return result


def _ensure_claims_keys(result: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Ensure claims has member_id / provider_id; derive missing member/provider tables."""
    claims_df = result["claims"]
    if "member_id" not in claims_df.columns:
        claims_df = claims_df.assign(member_id=range(1, len(claims_df) + 1))
        logger.info("No member_id in claims — assigned sequential IDs.")
    if "provider_id" not in claims_df.columns:
        claims_df = claims_df.assign(provider_id=1)
        logger.info("No provider_id in claims — assigned provider_id=1 for all rows.")
    result["claims"] = claims_df

    if "members" not in result:
        logger.info("No members file configured — deriving members from claims data.")
        result["members"] = _derive_members(result["claims"])
    if "providers" not in result:
        logger.info("No providers file configured — deriving providers from claims data.")
        result["providers"] = _derive_providers(result["claims"])
    return result


def _validate_member_fk(result: dict[str, pd.DataFrame]) -> None:
    """Raise ``ValueError`` if claims references member_id values missing from members."""
    members_df = result["members"]
    if "member_id" not in members_df.columns:
        raise ValueError(
            "Configured 'members' file must include a 'member_id' column matching "
            "'claims.member_id'. Either add this column to the members file or "
            "remove the members file from the Kaggle config to let it be derived "
            "from claims."
        )
    missing_ids = set(result["claims"]["member_id"].dropna()) - set(
        members_df["member_id"].dropna()
    )
    if missing_ids:
        sample_str = ", ".join(map(str, sorted(missing_ids)[:10]))
        raise ValueError(
            "The 'members' table is missing member_id values that are referenced "
            f"in the 'claims' table. Total missing: {len(missing_ids)}. "
            f"Example missing member_id values: {sample_str}"
        )


def _validate_provider_fk(result: dict[str, pd.DataFrame]) -> None:
    """Raise ``ValueError`` if claims references provider_id values missing from providers."""
    providers_df = result["providers"]
    if "provider_id" not in providers_df.columns:
        raise ValueError(
            "Configured 'providers' file must include a 'provider_id' column matching "
            "'claims.provider_id'. Either add this column to the providers file or "
            "remove the providers file from the Kaggle config to let it be derived "
            "from claims."
        )
    missing_ids = set(result["claims"]["provider_id"].dropna()) - set(
        providers_df["provider_id"].dropna()
    )
    if missing_ids:
        sample_str = ", ".join(map(str, sorted(missing_ids)[:10]))
        raise ValueError(
            "The 'providers' table is missing provider_id values that are referenced "
            f"in the 'claims' table. Total missing: {len(missing_ids)}. "
            f"Example missing provider_id values: {sample_str}"
        )


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────


def load_kaggle_data(
    config_path: str = _DEFAULT_CONFIG,
    active_dataset: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Download (if needed) and map a Kaggle dataset to the pipeline schema.

    Reads ``config_path`` (default: ``config/kaggle.yaml``) to determine which
    dataset to use, where to cache it, and how to rename / default its columns.

    Parameters
    ----------
    active_dataset:
        Override the ``active_dataset`` key from the YAML.  Useful for
        selecting ``insurance_claims`` instead of the default
        ``insurance_charges`` without editing the config file.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are ``"members"``, ``"providers"``, and ``"claims"``.  If the
        dataset config does not supply separate members or providers files they
        are derived automatically from the claims data.

    Raises
    ------
    ValueError
        If ``active_dataset`` is missing from the config or the config contains
        no ``claims`` file mapping.
    KeyError
        If the named ``active_dataset`` is not defined under ``datasets``.
    FileNotFoundError
        If a configured file is absent after the download step.
    EnvironmentError
        If Kaggle credentials cannot be located.
    """
    owner, dataset, dest_dir, files, col_maps, user_defaults = _parse_dataset_config(
        config_path, active_dataset
    )

    if _needs_download(dest_dir, files):
        download_dataset(owner, dataset, dest_dir)
    else:
        logger.info("Using cached Kaggle data from %s", dest_dir)

    result = _load_role_files(dest_dir, files, col_maps, user_defaults)

    if "claims" not in result:
        raise ValueError(
            "Kaggle config must include at least a 'claims' file mapping. "
            "Check the 'files' section in config/kaggle.yaml."
        )

    result = _ensure_claims_keys(result)

    if "members" in files:
        _validate_member_fk(result)
    if "providers" in files:
        _validate_provider_fk(result)

    return result
