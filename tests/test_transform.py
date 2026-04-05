"""Unit tests for src.transform — insurance KPI computation logic.

Tests are fully in-memory: no database connection is required.  All helpers
that call ``get_engine`` / ``pd.read_sql`` are patched out so the pure
transformation logic is exercised in isolation.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.transform import run_transform

# ────────────────────────────────────────────────────────────────────────────
# Fixture: minimal joined DataFrame matching the SQL query output
# ────────────────────────────────────────────────────────────────────────────


def _make_joined_df() -> pd.DataFrame:
    """Return a small DataFrame with all columns produced by the SQL join."""
    return pd.DataFrame(
        {
            "claim_id": [1, 2, 3, 4, 5, 6],
            "member_id": [1, 1, 2, 2, 3, 3],
            "provider_id": [10, 10, 20, 20, 10, 20],
            "service_date": pd.to_datetime(
                ["2023-01-15", "2023-02-20", "2023-01-10", "2023-03-05", "2023-02-14", "2023-03-22"]
            ),
            "billed_amount": [150.0, 250.0, 300.0, 400.0, 120.0, 180.0],
            "allowed_amount": [130.0, 220.0, 270.0, 360.0, 100.0, 160.0],
            "paid_amount": [100.0, 200.0, 250.0, 300.0, 80.0, 140.0],
            "place_of_service": ["Office", "Office", "Inpatient", "ER", "Office", "Outpatient"],
            "diagnosis_code": ["I10", "E11", "I10", "M54", "E11", "I10"],
            "procedure_code": ["99213", "99214", "93000", "71020", "99213", "80050"],
            "dob": pd.to_datetime(
                ["1980-06-15", "1980-06-15", "1960-03-22", "1960-03-22", "1990-09-01", "1990-09-01"]
            ),
            "member_region": ["East", "East", "West", "West", "North", "North"],
            "effective_date": pd.to_datetime(["2023-01-01"] * 6),
            "in_network": [True, True, False, False, True, False],
        }
    )


def _run_transform_with_df(df: pd.DataFrame, tmp_path) -> None:
    """Patch engine and read_sql, then call run_transform writing to tmp_path."""
    mock_engine = MagicMock()
    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch("pandas.DataFrame.to_csv") as mock_to_csv,
    ):
        # Redirect output writes to tmp_path so we can inspect CSVs
        written: dict[str, pd.DataFrame] = {}

        def capture_to_csv(path, index=False):
            written[path] = None  # record that write was attempted

        mock_to_csv.side_effect = capture_to_csv
        run_transform()
    return written


# ────────────────────────────────────────────────────────────────────────────
# KPI output tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_kpis_required_columns(tmp_path):
    """KPI output must contain the mandatory insurance reporting columns."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured_kpis: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "kpis" in path:
            captured_kpis.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    assert captured_kpis, "kpis.csv must be written"
    kpis = captured_kpis[0]
    for col in ("age_band", "member_region", "in_network", "claims", "paid_total", "paid_avg"):
        assert col in kpis.columns, f"KPIs missing required column: {col}"


@pytest.mark.unit
def test_run_transform_kpis_no_negative_claim_counts(tmp_path):
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "kpis" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    kpis = captured[0]
    assert (kpis["claims"] >= 0).all(), "Claim counts must be non-negative"


@pytest.mark.unit
def test_run_transform_kpis_paid_avg_consistent_with_total():
    """paid_avg must equal paid_total / claims for every KPI row."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "kpis" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    kpis = captured[0]
    expected_avg = kpis["paid_total"] / kpis["claims"]
    pd.testing.assert_series_equal(
        kpis["paid_avg"].round(6),
        expected_avg.round(6),
        check_names=False,
    )


# ────────────────────────────────────────────────────────────────────────────
# Monthly output tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_monthly_required_columns():
    """Monthly output must contain the mandatory trend-reporting columns."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "monthly" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    assert captured, "monthly.csv must be written"
    monthly = captured[0]
    for col in ("month", "member_region", "in_network", "claims", "paid_total"):
        assert col in monthly.columns, f"Monthly missing required column: {col}"


@pytest.mark.unit
def test_run_transform_monthly_total_claims_matches_input():
    """Sum of monthly claim counts must equal the total number of input rows."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "monthly" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    monthly = captured[0]
    assert monthly["claims"].sum() == len(df)


# ────────────────────────────────────────────────────────────────────────────
# Loss ratio output tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_loss_ratio_required_columns():
    """Loss ratio output must contain all insurance compliance reporting columns."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "loss_ratio" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    assert captured, "loss_ratio.csv must be written"
    lr = captured[0]
    for col in (
        "member_region",
        "in_network",
        "claims",
        "billed_total",
        "allowed_total",
        "paid_total",
        "loss_ratio_pct",
        "allowed_ratio_pct",
    ):
        assert col in lr.columns, f"Loss ratio missing required column: {col}"


@pytest.mark.unit
def test_run_transform_loss_ratio_values_in_range():
    """loss_ratio_pct must be between 0 and 100 when billed_amount > 0."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "loss_ratio" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    lr = captured[0]
    non_null = lr["loss_ratio_pct"].dropna()
    assert (non_null >= 0).all(), "loss_ratio_pct must be >= 0"
    assert (non_null <= 100).all(), "loss_ratio_pct must be <= 100"


@pytest.mark.unit
def test_run_transform_loss_ratio_paid_leq_billed():
    """Paid total must not exceed billed total for any region/network group."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "loss_ratio" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    lr = captured[0]
    assert (lr["paid_total"] <= lr["billed_total"]).all(), "paid_total must not exceed billed_total"


# ────────────────────────────────────────────────────────────────────────────
# Network utilization output tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_network_summary_required_columns():
    """Network utilization output must contain all required reporting columns."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "network_summary" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    assert captured, "network_summary.csv must be written"
    ns = captured[0]
    for col in ("in_network", "claims", "paid_total", "paid_avg", "utilization_pct"):
        assert col in ns.columns, f"Network summary missing required column: {col}"


@pytest.mark.unit
def test_run_transform_network_utilization_pct_sums_to_100():
    """Network utilization percentages must sum to 100 across all groups."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "network_summary" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    ns = captured[0]
    total_pct = ns["utilization_pct"].sum()
    assert abs(total_pct - 100.0) < 0.1, f"utilization_pct must sum to ~100, got {total_pct}"


# ────────────────────────────────────────────────────────────────────────────
# Diagnosis summary output tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_diagnosis_summary_required_columns():
    """Diagnosis summary output must contain all required ICD reporting columns."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "diagnosis_summary" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    assert captured, "diagnosis_summary.csv must be written"
    ds = captured[0]
    for col in ("diagnosis_code", "claims", "paid_total", "paid_avg", "billed_total"):
        assert col in ds.columns, f"Diagnosis summary missing required column: {col}"


@pytest.mark.unit
def test_run_transform_diagnosis_summary_covers_all_codes():
    """Every distinct diagnosis_code in the input must appear in the summary."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "diagnosis_summary" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    ds = captured[0]
    expected_codes = set(df["diagnosis_code"].unique())
    actual_codes = set(ds["diagnosis_code"].unique())
    assert (
        expected_codes == actual_codes
    ), f"Diagnosis codes mismatch — expected {expected_codes}, got {actual_codes}"


@pytest.mark.unit
def test_run_transform_diagnosis_summary_total_claims_matches_input():
    """Sum of claims across all diagnosis groups must equal the total input rows."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    captured: list[pd.DataFrame] = []

    def fake_to_csv(self, path, index=False):
        if "diagnosis_summary" in path:
            captured.append(self)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch("src.transform.os.makedirs"),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform()

    ds = captured[0]
    assert ds["claims"].sum() == len(df)


# ────────────────────────────────────────────────────────────────────────────
# output_dir parameter tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_run_transform_uses_custom_output_dir(tmp_path):
    """run_transform(output_dir=...) must write all CSV files into that directory."""
    df = _make_joined_df()
    mock_engine = MagicMock()
    custom_dir = str(tmp_path / "client_x")
    captured_paths: list[str] = []

    def fake_to_csv(self, path, index=False):
        captured_paths.append(path)

    with (
        patch("src.transform.get_engine", return_value=mock_engine),
        patch("src.transform.pd.read_sql", return_value=df),
        patch.object(pd.DataFrame, "to_csv", fake_to_csv),
    ):
        run_transform(output_dir=custom_dir)

    assert captured_paths, "run_transform must write at least one CSV file"
    for path in captured_paths:
        assert path.startswith(
            custom_dir
        ), f"Expected every CSV to be written under '{custom_dir}', got '{path}'"
    written_names = {os.path.basename(p) for p in captured_paths}
    assert "kpis.csv" in written_names
    assert "monthly.csv" in written_names
    assert "loss_ratio.csv" in written_names
    assert "network_summary.csv" in written_names
