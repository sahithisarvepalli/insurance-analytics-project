"""Unit tests for src.kaggle_ingest — column mapping, derivation, and ingest logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

from src.kaggle_ingest import (
    _apply_mapping,
    _derive_members,
    _derive_providers,
    _ensure_kaggle_credentials,
    download_dataset,
    load_kaggle_data,
)

# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _sample_claims() -> pd.DataFrame:
    """Return a minimal claims DataFrame for testing."""
    return pd.DataFrame(
        {
            "member_id": [1, 2, 3, 1],
            "provider_id": [10, 10, 20, 20],
            "paid_amount": [100.0, 200.0, 150.0, 50.0],
            "service_date": ["2023-01-01"] * 4,
            "diagnosis_code": ["Z00"] * 4,
            "procedure_code": ["99213"] * 4,
            "billed_amount": [120.0, 220.0, 170.0, 60.0],
            "allowed_amount": [110.0, 210.0, 160.0, 55.0],
            "place_of_service": ["Office"] * 4,
        }
    )


def _sample_claims_with_demographics() -> pd.DataFrame:
    """Return a claims DataFrame that includes Kaggle demographic columns."""
    return pd.DataFrame(
        {
            "member_id": [1, 2, 3, 1],
            "provider_id": [10, 10, 20, 20],
            "paid_amount": [100.0, 200.0, 150.0, 50.0],
            "age": [30, 45, 25, 30],
            "gender": ["M", "F", "M", "M"],
            "region": ["East", "West", "North", "East"],
            "service_date": ["2023-01-01"] * 4,
            "diagnosis_code": ["Z00"] * 4,
            "procedure_code": ["99213"] * 4,
            "billed_amount": [120.0, 220.0, 170.0, 60.0],
            "allowed_amount": [110.0, 210.0, 160.0, 55.0],
            "place_of_service": ["Office"] * 4,
        }
    )


# ────────────────────────────────────────────────────────────────────────────
# _apply_mapping
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_apply_mapping_renames_mapped_columns():
    df = pd.DataFrame({"charges": [100, 200], "sex": ["M", "F"]})
    result = _apply_mapping(df, {"charges": "paid_amount", "sex": "gender"}, {})
    assert "paid_amount" in result.columns
    assert "gender" in result.columns
    assert "charges" not in result.columns
    assert "sex" not in result.columns


@pytest.mark.unit
def test_apply_mapping_ignores_absent_map_keys():
    df = pd.DataFrame({"a": [1]})
    result = _apply_mapping(df, {"nonexistent": "target"}, {})
    assert list(result.columns) == ["a"]


@pytest.mark.unit
def test_apply_mapping_injects_defaults_for_absent_columns():
    df = pd.DataFrame({"paid_amount": [100.0]})
    result = _apply_mapping(df, {}, {"place_of_service": "Office", "diagnosis_code": "Z00"})
    assert result["place_of_service"].iloc[0] == "Office"
    assert result["diagnosis_code"].iloc[0] == "Z00"


@pytest.mark.unit
def test_apply_mapping_does_not_overwrite_existing_columns():
    df = pd.DataFrame({"place_of_service": ["ER"]})
    result = _apply_mapping(df, {}, {"place_of_service": "Office"})
    assert result["place_of_service"].iloc[0] == "ER"


@pytest.mark.unit
def test_apply_mapping_callable_default_is_invoked():
    df = pd.DataFrame({"a": [1, 2]})
    result = _apply_mapping(df, {}, {"b": lambda: [10, 20]})
    assert list(result["b"]) == [10, 20]


@pytest.mark.unit
def test_apply_mapping_callable_default_accepts_length():
    df = pd.DataFrame({"a": [1, 2, 3]})
    result = _apply_mapping(df, {}, {"b": lambda n: [0] * n})
    assert list(result["b"]) == [0, 0, 0]


# ────────────────────────────────────────────────────────────────────────────
# _derive_members
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_derive_members_returns_one_row_per_unique_member():
    claims = _sample_claims()
    members = _derive_members(claims)
    assert len(members) == claims["member_id"].nunique()


@pytest.mark.unit
def test_derive_members_required_columns_present():
    members = _derive_members(_sample_claims())
    for col in ("member_id", "dob", "gender", "region", "effective_date"):
        assert col in members.columns, f"Missing column: {col}"


@pytest.mark.unit
def test_derive_members_ids_match_claims():
    claims = _sample_claims()
    members = _derive_members(claims)
    assert set(members["member_id"]) == set(claims["member_id"].unique())


@pytest.mark.unit
def test_derive_members_uses_age_column_when_present():
    """When claims carry an 'age' column the derived dob must reflect it."""
    claims = _sample_claims_with_demographics()
    members = _derive_members(claims)
    # DOB should not be NaT when age is available
    assert members["dob"].notna().all()


@pytest.mark.unit
def test_derive_members_uses_gender_column_when_present():
    claims = _sample_claims_with_demographics()
    members = _derive_members(claims)
    assert set(members["gender"]).issubset({"M", "F"})


@pytest.mark.unit
def test_derive_members_uses_region_column_when_present():
    claims = _sample_claims_with_demographics()
    members = _derive_members(claims)
    assert set(members["region"]).issubset({"East", "West", "North", "South"})


@pytest.mark.unit
def test_derive_members_falls_back_to_defaults_without_demographic_columns():
    """Without demographic columns, dob is NaT and defaults are applied."""
    claims = _sample_claims()
    members = _derive_members(claims)
    assert (members["gender"] == "U").all()
    assert (members["region"] == "Unknown").all()
    assert members["dob"].isna().all()


@pytest.mark.unit
def test_derive_members_is_deterministic():
    """Derivation must produce identical results on repeated calls (no randomness)."""
    claims = _sample_claims_with_demographics()
    m1 = _derive_members(claims)
    m2 = _derive_members(claims)
    pd.testing.assert_frame_equal(m1, m2)


# ────────────────────────────────────────────────────────────────────────────
# _derive_providers
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_derive_providers_returns_one_row_per_unique_provider():
    claims = _sample_claims()
    providers = _derive_providers(claims)
    assert len(providers) == claims["provider_id"].nunique()


@pytest.mark.unit
def test_derive_providers_required_columns_present():
    providers = _derive_providers(_sample_claims())
    for col in ("provider_id", "specialty", "in_network", "region"):
        assert col in providers.columns, f"Missing column: {col}"


@pytest.mark.unit
def test_derive_providers_ids_match_claims():
    claims = _sample_claims()
    providers = _derive_providers(claims)
    assert set(providers["provider_id"]) == set(claims["provider_id"].unique())


@pytest.mark.unit
def test_derive_providers_uses_schema_defaults():
    """Derived providers must use deterministic schema defaults, not random values."""
    providers = _derive_providers(_sample_claims())
    assert (providers["specialty"] == "Unknown").all()
    assert (providers["in_network"] == True).all()  # noqa: E712
    assert (providers["region"] == "Unknown").all()


@pytest.mark.unit
def test_derive_providers_is_deterministic():
    """Derivation must produce identical results on repeated calls (no randomness)."""
    claims = _sample_claims()
    p1 = _derive_providers(claims)
    p2 = _derive_providers(claims)
    pd.testing.assert_frame_equal(p1, p2)


# ────────────────────────────────────────────────────────────────────────────
# _ensure_kaggle_credentials
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_ensure_kaggle_credentials_passes_with_env_vars(monkeypatch):
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key123")
    _ensure_kaggle_credentials()  # should not raise


@pytest.mark.unit
def test_ensure_kaggle_credentials_raises_when_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    with patch("pathlib.Path.home", return_value=tmp_path):
        with pytest.raises(EnvironmentError, match="Kaggle credentials not found"):
            _ensure_kaggle_credentials()


@pytest.mark.unit
def test_ensure_kaggle_credentials_passes_with_kaggle_json(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    kaggle_dir = tmp_path / ".kaggle"
    kaggle_dir.mkdir()
    (kaggle_dir / "kaggle.json").write_text('{"username":"u","key":"k"}')
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ensure_kaggle_credentials()  # should not raise


# ────────────────────────────────────────────────────────────────────────────
# download_dataset
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_download_dataset_calls_kaggle_api(monkeypatch, tmp_path):
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key")

    mock_api = MagicMock()
    mock_kaggle = MagicMock()
    mock_kaggle.api = mock_api

    with patch.dict("sys.modules", {"kaggle": mock_kaggle}):
        result = download_dataset("owner", "dataset", str(tmp_path))

    mock_api.authenticate.assert_called_once()
    mock_api.dataset_download_files.assert_called_once_with(
        "owner/dataset",
        path=str(tmp_path),
        unzip=True,
        quiet=False,
    )
    assert result == str(tmp_path)


@pytest.mark.unit
def test_download_dataset_raises_without_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    with patch("pathlib.Path.home", return_value=tmp_path):
        with pytest.raises(EnvironmentError):
            download_dataset("owner", "dataset", str(tmp_path))


# ────────────────────────────────────────────────────────────────────────────
# load_kaggle_data
# ────────────────────────────────────────────────────────────────────────────


def _write_config(
    tmp_path, active_dataset="test_ds", extra_files=None, col_map=None, defaults=None
):
    """Write a minimal Kaggle YAML config to a temp file and return its path."""
    files = extra_files or {"claims": "claims.csv"}
    config = {
        "active_dataset": active_dataset,
        "datasets": {
            active_dataset: {
                "owner": "test_owner",
                "dataset": "test_dataset",
                "dest_dir": str(tmp_path / "kaggle"),
                "files": files,
                "column_map": col_map or {},
                "defaults": defaults or {},
            }
        },
    }
    path = tmp_path / "kaggle.yaml"
    path.write_text(yaml.safe_dump(config))
    return str(path)


def _write_claims_csv(dest_dir):
    """Write a minimal claims CSV to dest_dir and return the path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / "claims.csv"
    df = pd.DataFrame(
        {
            "charges": [100.0, 200.0],
            "sex": ["M", "F"],
            "age": [30, 45],
            "region": ["East", "West"],
        }
    )
    df.to_csv(path, index=False)
    return path


@pytest.mark.unit
def test_load_kaggle_data_raises_when_no_active_dataset(tmp_path):
    cfg_path = tmp_path / "kaggle.yaml"
    cfg_path.write_text(yaml.safe_dump({"datasets": {}}))
    with pytest.raises(ValueError, match="active_dataset"):
        load_kaggle_data(str(cfg_path))


@pytest.mark.unit
def test_load_kaggle_data_raises_when_active_dataset_not_in_config(tmp_path):
    cfg_path = tmp_path / "kaggle.yaml"
    cfg_path.write_text(yaml.safe_dump({"active_dataset": "missing", "datasets": {}}))
    with pytest.raises(KeyError, match="missing"):
        load_kaggle_data(str(cfg_path))


@pytest.mark.unit
def test_load_kaggle_data_raises_when_claims_file_not_found(tmp_path, monkeypatch):
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir()
    # download_dataset is a no-op so the configured claims.csv is never created
    monkeypatch.setattr("src.kaggle_ingest.download_dataset", lambda *a, **kw: None)
    cfg_path = _write_config(tmp_path, extra_files={"claims": "claims.csv"})
    with pytest.raises(FileNotFoundError, match="claims.csv"):
        load_kaggle_data(cfg_path)


@pytest.mark.unit
def test_load_kaggle_data_raises_when_no_claims_configured(tmp_path):
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir()
    (dest_dir / "members.csv").write_text("member_id\n1\n")
    cfg_path = _write_config(tmp_path, extra_files={"members": "members.csv"})
    with pytest.raises(ValueError, match="claims"):
        load_kaggle_data(cfg_path)


@pytest.mark.unit
def test_load_kaggle_data_returns_all_three_roles(tmp_path):
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(
        tmp_path,
        col_map={"claims": {"charges": "paid_amount", "sex": "gender"}},
        defaults={
            "claims": {
                "billed_amount": 0.0,
                "allowed_amount": 0.0,
                "place_of_service": "Office",
                "procedure_code": "99213",
                "service_date": "2023-01-01",
                "diagnosis_code": "Z00",
            }
        },
    )
    result = load_kaggle_data(cfg_path)
    assert set(result.keys()) == {"members", "providers", "claims"}


@pytest.mark.unit
def test_load_kaggle_data_column_mapping_applied(tmp_path):
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(
        tmp_path,
        col_map={"claims": {"charges": "paid_amount", "sex": "gender"}},
    )
    result = load_kaggle_data(cfg_path)
    assert "paid_amount" in result["claims"].columns
    assert "gender" in result["claims"].columns
    assert "charges" not in result["claims"].columns


@pytest.mark.unit
def test_load_kaggle_data_defaults_injected(tmp_path):
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(
        tmp_path,
        defaults={"claims": {"place_of_service": "Inpatient"}},
    )
    result = load_kaggle_data(cfg_path)
    assert (result["claims"]["place_of_service"] == "Inpatient").all()


@pytest.mark.unit
def test_load_kaggle_data_members_derived_when_absent(tmp_path):
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    # Claims CSV has no member_id; provide it via defaults
    cfg_path = _write_config(
        tmp_path,
        col_map={"claims": {"charges": "paid_amount"}},
        defaults={"claims": {"member_id": 1, "provider_id": 1}},
    )
    result = load_kaggle_data(cfg_path)
    assert "members" in result
    assert not result["members"].empty


@pytest.mark.unit
def test_load_kaggle_data_providers_derived_when_absent(tmp_path):
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(
        tmp_path,
        defaults={"claims": {"member_id": 1, "provider_id": 1}},
    )
    result = load_kaggle_data(cfg_path)
    assert "providers" in result
    assert not result["providers"].empty


@pytest.mark.unit
def test_load_kaggle_data_uses_cached_data_without_downloading(tmp_path, monkeypatch):
    """load_kaggle_data must not call download when CSV files are already present."""
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(tmp_path)

    download_called = []

    def fake_download(owner, dataset, dest_dir):
        download_called.append(True)
        return dest_dir

    monkeypatch.setattr("src.kaggle_ingest.download_dataset", fake_download)
    load_kaggle_data(cfg_path)
    assert not download_called, "download_dataset should not be called when cache exists"


@pytest.mark.unit
def test_load_kaggle_data_triggers_download_when_configured_file_absent(tmp_path, monkeypatch):
    """A stale cache dir with a different CSV must still trigger a download."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    # Put an unrelated CSV in the cache dir — the configured claims.csv is missing
    (dest_dir / "unrelated.csv").write_text("x\n1\n")
    cfg_path = _write_config(tmp_path)

    download_called = []

    def fake_download(owner, dataset, dest):
        download_called.append(True)
        # Write the expected file so the subsequent read succeeds
        _write_claims_csv(dest_dir)
        return dest

    monkeypatch.setattr("src.kaggle_ingest.download_dataset", fake_download)
    load_kaggle_data(cfg_path)
    assert download_called, "download_dataset should be called when configured file is absent"


@pytest.mark.unit
def test_load_kaggle_data_derived_members_use_kaggle_demographics(tmp_path):
    """Members derived from Kaggle claims must reflect age, gender, and region columns."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    claims_path = dest_dir / "claims.csv"
    pd.DataFrame(
        {
            "member_id": [1, 2],
            "provider_id": [10, 10],
            "paid_amount": [100.0, 200.0],
            "age": [30, 45],
            "gender": ["M", "F"],
            "region": ["East", "West"],
        }
    ).to_csv(claims_path, index=False)
    cfg_path = _write_config(tmp_path)
    result = load_kaggle_data(cfg_path)
    members = result["members"]
    assert members["dob"].notna().all(), "dob must be derived from age"
    assert set(members["gender"]).issubset({"M", "F"})
    assert set(members["region"]).issubset({"East", "West"})


@pytest.mark.unit
def test_load_kaggle_data_derived_providers_use_schema_defaults(tmp_path):
    """Derived providers must use deterministic schema defaults, not random values."""
    dest_dir = tmp_path / "kaggle"
    _write_claims_csv(dest_dir)
    cfg_path = _write_config(
        tmp_path,
        defaults={"claims": {"member_id": 1, "provider_id": 1}},
    )
    result = load_kaggle_data(cfg_path)
    providers = result["providers"]
    assert (providers["specialty"] == "Unknown").all()
    assert (providers["in_network"] == True).all()  # noqa: E712
    assert (providers["region"] == "Unknown").all()


@pytest.mark.unit
def test_load_kaggle_data_fk_validation_raises_when_members_missing_member_id_column(tmp_path):
    """Explicit members file without member_id column must raise ValueError."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    _write_claims_csv(dest_dir)
    # members file that lacks member_id
    members_path = dest_dir / "members.csv"
    pd.DataFrame({"name": ["Alice"]}).to_csv(members_path, index=False)

    cfg_path = _write_config(
        tmp_path,
        extra_files={"claims": "claims.csv", "members": "members.csv"},
        defaults={"claims": {"member_id": 1, "provider_id": 1}},
    )
    with pytest.raises(ValueError, match="member_id"):
        load_kaggle_data(cfg_path)


@pytest.mark.unit
def test_load_kaggle_data_fk_validation_raises_when_members_have_missing_ids(tmp_path):
    """Claims referencing member_ids absent from the members table must raise ValueError."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    # Claims reference member_ids 1 and 2
    claims_path = dest_dir / "claims.csv"
    pd.DataFrame(
        {
            "member_id": [1, 2],
            "provider_id": [10, 10],
            "paid_amount": [100.0, 200.0],
        }
    ).to_csv(claims_path, index=False)
    # Members table only covers member_id=1
    members_path = dest_dir / "members.csv"
    pd.DataFrame({"member_id": [1]}).to_csv(members_path, index=False)

    cfg_path = _write_config(
        tmp_path,
        extra_files={"claims": "claims.csv", "members": "members.csv"},
    )
    with pytest.raises(ValueError, match="missing member_id"):
        load_kaggle_data(cfg_path)


@pytest.mark.unit
def test_load_kaggle_data_fk_validation_raises_when_providers_missing_provider_id_column(
    tmp_path,
):
    """Explicit providers file without provider_id column must raise ValueError."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    _write_claims_csv(dest_dir)
    providers_path = dest_dir / "providers.csv"
    pd.DataFrame({"specialty": ["PCP"]}).to_csv(providers_path, index=False)

    cfg_path = _write_config(
        tmp_path,
        extra_files={"claims": "claims.csv", "providers": "providers.csv"},
        defaults={"claims": {"member_id": 1, "provider_id": 1}},
    )
    with pytest.raises(ValueError, match="provider_id"):
        load_kaggle_data(cfg_path)


@pytest.mark.unit
def test_load_kaggle_data_fk_validation_raises_when_providers_have_missing_ids(tmp_path):
    """Claims referencing provider_ids absent from providers table must raise ValueError."""
    dest_dir = tmp_path / "kaggle"
    dest_dir.mkdir(parents=True)
    claims_path = dest_dir / "claims.csv"
    pd.DataFrame(
        {
            "member_id": [1, 1],
            "provider_id": [10, 20],
            "paid_amount": [100.0, 200.0],
        }
    ).to_csv(claims_path, index=False)
    # Providers table only covers provider_id=10
    providers_path = dest_dir / "providers.csv"
    pd.DataFrame({"provider_id": [10]}).to_csv(providers_path, index=False)

    cfg_path = _write_config(
        tmp_path,
        extra_files={"claims": "claims.csv", "providers": "providers.csv"},
    )
    with pytest.raises(ValueError, match="missing provider_id"):
        load_kaggle_data(cfg_path)
