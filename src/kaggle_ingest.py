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

import numpy as np
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
    raise EnvironmentError(
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
    """Build a minimal *members* DataFrame from unique ``member_id`` values in claims."""
    member_ids = claims_df["member_id"].dropna().unique()
    n = len(member_ids)
    rng = np.random.default_rng(42)
    dob_year = rng.integers(1955, 2005, size=n)
    dob = pd.to_datetime(dob_year, format="%Y") + pd.to_timedelta(
        rng.integers(0, 365, size=n), unit="D"
    )
    return pd.DataFrame(
        {
            "member_id": member_ids,
            "person_id": member_ids,
            "dob": dob,
            "gender": rng.choice(list("MF"), size=n),
            "region": rng.choice(["East", "West", "North", "South"], size=n),
            "effective_date": pd.Timestamp("2022-01-01"),
            "termination_date": pd.NaT,
        }
    )


def _derive_providers(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Build a minimal *providers* DataFrame from unique ``provider_id`` values in claims."""
    provider_ids = claims_df["provider_id"].dropna().unique()
    n = len(provider_ids)
    rng = np.random.default_rng(43)
    return pd.DataFrame(
        {
            "provider_id": provider_ids,
            "specialty": rng.choice(
                ["PCP", "Cardiology", "Ortho", "Derm", "Oncology"], size=n
            ),
            "in_network": rng.choice([True, False], size=n, p=[0.8, 0.2]),
            "region": rng.choice(["East", "West", "North", "South"], size=n),
        }
    )


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────


def load_kaggle_data(config_path: str = _DEFAULT_CONFIG) -> dict[str, pd.DataFrame]:
    """Download (if needed) and map a Kaggle dataset to the pipeline schema.

    Reads ``config_path`` (default: ``config/kaggle.yaml``) to determine which
    dataset to use, where to cache it, and how to rename / default its columns.

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
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    active = cfg.get("active_dataset")
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

    # Download if the destination directory is missing or any configured file is absent.
    if not os.path.isdir(dest_dir):
        needs_download = True
    elif files:
        # When specific files are configured, require that all of them exist.
        needs_download = any(
            not os.path.isfile(os.path.join(dest_dir, filename))
            for filename in files.values()
        )
    else:
        # Fallback: if no files are configured, look for any CSV as a cache signal.
        needs_download = not any(f.lower().endswith(".csv") for f in os.listdir(dest_dir))
    if needs_download:
        download_dataset(owner, dataset, dest_dir)
    else:
        logger.info("Using cached Kaggle data from %s", dest_dir)

    result: dict[str, pd.DataFrame] = {}
    for role, filename in files.items():
        path = os.path.join(dest_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Expected file '{filename}' not found at '{path}'. "
                "Check the 'files' section in config/kaggle.yaml."
            )
        df = pd.read_csv(path)
        # Merge schema-level defaults with user overrides (user config wins)
        merged_defaults = {**_SCHEMA_DEFAULTS.get(role, {}), **user_defaults.get(role, {})}
        df = _apply_mapping(df, col_maps.get(role, {}), merged_defaults)
        result[role] = df
        logger.info("Loaded %d rows for role '%s' from %s", len(df), role, path)

    if "claims" not in result:
        raise ValueError(
            "Kaggle config must include at least a 'claims' file mapping. "
            "Check the 'files' section in config/kaggle.yaml."
        )

    # Ensure claims carry member_id / provider_id so FK derivation works
    claims_df = result["claims"]
    if "member_id" not in claims_df.columns:
        claims_df = claims_df.assign(member_id=range(1, len(claims_df) + 1))
        logger.info("No member_id in claims — assigned sequential IDs.")
    if "provider_id" not in claims_df.columns:
        claims_df = claims_df.assign(provider_id=1)
        logger.info("No provider_id in claims — assigned provider_id=1 for all rows.")
    result["claims"] = claims_df

    # Auto-derive member / provider tables when not supplied by the dataset
    if "members" not in result:
        logger.info("No members file configured — deriving members from claims data.")
        result["members"] = _derive_members(result["claims"])

    if "providers" not in result:
        logger.info("No providers file configured — deriving providers from claims data.")
        result["providers"] = _derive_providers(result["claims"])

    # Validate FK consistency when members/providers were explicitly configured
    # (derived tables are always consistent by construction)
    claims_df = result["claims"]

    if "members" in files:
        members_df = result["members"]
        if "member_id" not in members_df.columns:
            raise ValueError(
                "Configured 'members' file must include a 'member_id' column matching "
                "'claims.member_id'. Either add this column to the members file or "
                "remove the members file from the Kaggle config to let it be derived "
                "from claims."
            )
        missing_member_ids = set(claims_df["member_id"].dropna()) - set(
            members_df["member_id"].dropna()
        )
        if missing_member_ids:
            sample_str = ", ".join(map(str, sorted(missing_member_ids)[:10]))
            raise ValueError(
                "The 'members' table is missing member_id values that are referenced "
                f"in the 'claims' table. Total missing: {len(missing_member_ids)}. "
                f"Example missing member_id values: {sample_str}"
            )

    if "providers" in files:
        providers_df = result["providers"]
        if "provider_id" not in providers_df.columns:
            raise ValueError(
                "Configured 'providers' file must include a 'provider_id' column matching "
                "'claims.provider_id'. Either add this column to the providers file or "
                "remove the providers file from the Kaggle config to let it be derived "
                "from claims."
            )
        missing_provider_ids = set(claims_df["provider_id"].dropna()) - set(
            providers_df["provider_id"].dropna()
        )
        if missing_provider_ids:
            sample_str = ", ".join(map(str, sorted(missing_provider_ids)[:10]))
            raise ValueError(
                "The 'providers' table is missing provider_id values that are referenced "
                f"in the 'claims' table. Total missing: {len(missing_provider_ids)}. "
                f"Example missing provider_id values: {sample_str}"
            )

    return result
