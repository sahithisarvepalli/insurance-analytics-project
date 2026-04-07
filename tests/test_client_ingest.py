"""Unit tests for src.client_ingest — client CSV loading and column mapping."""

from __future__ import annotations

import os

import pandas as pd
import pytest
import yaml

from src.client_ingest import (
    _load_client_role_files,
    _parse_client_config,
    load_client_data,
)

# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _write_config(tmp_path, cfg: dict) -> str:
    """Write a YAML config dict to a temp file and return its path."""
    p = tmp_path / "client_test.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return str(p)


def _write_csv(tmp_path, name: str, df: pd.DataFrame) -> str:
    """Write a DataFrame to a temp CSV and return its path."""
    p = tmp_path / name
    df.to_csv(str(p), index=False)
    return str(p)


def _minimal_claims_df() -> pd.DataFrame:
    """Return a minimal claims DataFrame that satisfies pipeline requirements after mapping."""
    return pd.DataFrame(
        {
            "charge_amt": [1200.0, 2500.0, 980.0],
            "patient_id": [101, 102, 103],
            "physician_id": ["P01", "P02", "P01"],
            "service_dt": ["2023-01-10", "2023-01-15", "2023-02-01"],
            "icd_code": ["E11.9", "I10", "M54.5"],
            "cpt_code": ["99213", "93000", "27447"],
            "sex": ["M", "F", "M"],
            "age": [45, 52, 38],
            "patient_state": ["Northeast", "Southeast", "West"],
        }
    )


# ────────────────────────────────────────────────────────────────────────────
# _parse_client_config
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_parse_client_config_returns_all_fields(tmp_path):
    cfg = {
        "client_id": "acme",
        "client_name": "Acme Health",
        "files": {"claims": "some/path.csv"},
        "column_map": {"claims": {"charge_amt": "paid_amount"}},
        "defaults": {"claims": {"billed_amount": 0.0}},
    }
    path = _write_config(tmp_path, cfg)
    client_id, client_name, files, col_maps, user_defaults = _parse_client_config(path)
    assert client_id == "acme"
    assert client_name == "Acme Health"
    assert files == {"claims": "some/path.csv"}
    assert col_maps["claims"]["charge_amt"] == "paid_amount"
    assert user_defaults["claims"]["billed_amount"] == 0.0


@pytest.mark.unit
def test_parse_client_config_defaults_client_name_to_id(tmp_path):
    cfg = {"client_id": "acme", "files": {"claims": "some/path.csv"}}
    path = _write_config(tmp_path, cfg)
    client_id, client_name, *_ = _parse_client_config(path)
    assert client_name == "acme"


@pytest.mark.unit
def test_parse_client_config_raises_on_missing_files(tmp_path):
    cfg = {"client_id": "acme", "client_name": "Acme Health"}
    path = _write_config(tmp_path, cfg)
    with pytest.raises(ValueError, match="no 'files' section"):
        _parse_client_config(path)


@pytest.mark.unit
def test_parse_client_config_raises_on_missing_client_id(tmp_path):
    """A config without 'client_id' must raise ValueError."""
    cfg = {"client_name": "Acme Health", "files": {"claims": "some/path.csv"}}
    path = _write_config(tmp_path, cfg)
    with pytest.raises(ValueError, match="client_id"):
        _parse_client_config(path)


@pytest.mark.unit
def test_parse_client_config_raises_on_empty_yaml(tmp_path):
    """An empty (or non-mapping) YAML file must raise ValueError."""
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="valid YAML mapping"):
        _parse_client_config(str(p))


# ────────────────────────────────────────────────────────────────────────────
# _load_client_role_files
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_load_client_role_files_applies_column_map(tmp_path):
    df = pd.DataFrame({"charge_amt": [100.0, 200.0], "icd_code": ["E11.9", "I10"]})
    csv_path = _write_csv(tmp_path, "claims.csv", df)
    result = _load_client_role_files(
        files={"claims": csv_path},
        col_maps={"claims": {"charge_amt": "paid_amount", "icd_code": "diagnosis_code"}},
        user_defaults={},
    )
    assert "paid_amount" in result["claims"].columns
    assert "diagnosis_code" in result["claims"].columns
    assert "charge_amt" not in result["claims"].columns


@pytest.mark.unit
def test_load_client_role_files_injects_defaults(tmp_path):
    df = pd.DataFrame({"paid_amount": [100.0]})
    csv_path = _write_csv(tmp_path, "claims.csv", df)
    result = _load_client_role_files(
        files={"claims": csv_path},
        col_maps={},
        user_defaults={"claims": {"billed_amount": 0.0, "place_of_service": "Office"}},
    )
    assert result["claims"]["billed_amount"].iloc[0] == 0.0
    assert result["claims"]["place_of_service"].iloc[0] == "Office"


@pytest.mark.unit
def test_load_client_role_files_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        _load_client_role_files(
            files={"claims": str(tmp_path / "nonexistent.csv")},
            col_maps={},
            user_defaults={},
        )


# ────────────────────────────────────────────────────────────────────────────
# load_client_data
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_load_client_data_derives_members_and_providers(tmp_path):
    """When no members/providers files are configured they should be derived from claims."""
    raw_df = _minimal_claims_df()
    csv_path = _write_csv(tmp_path, "claims.csv", raw_df)
    cfg = {
        "client_id": "acme",
        "client_name": "Acme Health",
        "files": {"claims": csv_path},
        "column_map": {
            "claims": {
                "charge_amt": "paid_amount",
                "patient_id": "member_id",
                "physician_id": "provider_id",
                "service_dt": "service_date",
                "icd_code": "diagnosis_code",
                "cpt_code": "procedure_code",
                "sex": "gender",
                "patient_state": "region",
            }
        },
        "defaults": {
            "claims": {
                "billed_amount": 0.0,
                "allowed_amount": 0.0,
                "place_of_service": "Office",
            }
        },
    }
    config_path = _write_config(tmp_path, cfg)
    result = load_client_data(config_path)

    assert set(result.keys()) == {"claims", "members", "providers"}
    assert len(result["claims"]) == 3
    assert "member_id" in result["members"].columns
    assert "provider_id" in result["providers"].columns


@pytest.mark.unit
def test_load_client_data_raises_on_missing_claims(tmp_path):
    """Config without a 'claims' file should raise ValueError."""
    df = pd.DataFrame({"member_id": [1, 2]})
    csv_path = _write_csv(tmp_path, "members.csv", df)
    cfg = {
        "client_id": "acme",
        "files": {"members": csv_path},
    }
    config_path = _write_config(tmp_path, cfg)
    with pytest.raises(ValueError, match="claims"):
        load_client_data(config_path)


@pytest.mark.unit
def test_load_client_data_real_client_a_config():
    """Smoke test: load the bundled Client A config and sample CSV."""
    config_path = os.path.join("config", "clients", "client_a.yaml")
    if not os.path.exists(config_path):
        pytest.skip("Client A config not present — skipping smoke test.")
    result = load_client_data(config_path)
    assert len(result["claims"]) > 0
    assert "paid_amount" in result["claims"].columns
    assert "member_id" in result["claims"].columns


@pytest.mark.unit
def test_load_client_data_real_client_b_config():
    """Smoke test: load the bundled Client B config and sample CSV."""
    config_path = os.path.join("config", "clients", "client_b.yaml")
    if not os.path.exists(config_path):
        pytest.skip("Client B config not present — skipping smoke test.")
    result = load_client_data(config_path)
    assert len(result["claims"]) > 0
    assert "paid_amount" in result["claims"].columns
    assert "member_id" in result["claims"].columns
