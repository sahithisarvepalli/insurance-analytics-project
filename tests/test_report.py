"""Unit tests for src.report — insurance compliance Excel report generation.

Tests verify that:
- All required insurance compliance worksheet names are present in the workbook.
- Each sheet contains the expected column headers.
- Column validators in report.py raise errors on incomplete data.
- The report functions correctly when optional outputs are absent.
"""

from __future__ import annotations

import os

import pandas as pd
import pytest

from src.report import (
    main,
    validate_diagnosis_summary,
    validate_kpis,
    validate_loss_ratio,
    validate_monthly,
    validate_network_summary,
)

# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────


def _make_kpis() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_band": ["0-18", "19-30", "31-45"],
            "member_region": ["East", "West", "North"],
            "in_network": [True, True, False],
            "claims": [10, 20, 15],
            "paid_total": [1000.0, 2000.0, 1500.0],
            "paid_avg": [100.0, 100.0, 100.0],
        }
    )


def _make_monthly() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": ["2023-01-01", "2023-02-01"],
            "member_region": ["East", "West"],
            "in_network": [True, False],
            "claims": [50, 30],
            "paid_total": [5000.0, 3000.0],
        }
    )


def _make_loss_ratio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "member_region": ["East", "West"],
            "in_network": [True, False],
            "claims": [50, 30],
            "billed_total": [6000.0, 4000.0],
            "allowed_total": [5500.0, 3500.0],
            "paid_total": [5000.0, 3000.0],
            "loss_ratio_pct": [83.33, 75.0],
            "allowed_ratio_pct": [91.67, 87.5],
        }
    )


def _make_network_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "in_network": [True, False],
            "claims": [80, 20],
            "paid_total": [8000.0, 2000.0],
            "paid_avg": [100.0, 100.0],
            "utilization_pct": [80.0, 20.0],
        }
    )


def _make_diagnosis_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "diagnosis_code": ["I10", "E11", "M54"],
            "claims": [40, 35, 25],
            "paid_total": [4000.0, 3500.0, 2500.0],
            "paid_avg": [100.0, 100.0, 100.0],
            "billed_total": [5000.0, 4200.0, 3000.0],
        }
    )


def _write_outputs(tmp_path, **frames) -> None:
    """Write DataFrames as CSVs into tmp_path/outputs/."""
    out_dir = tmp_path / "outputs"
    out_dir.mkdir(exist_ok=True)
    for name, df in frames.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)


# ────────────────────────────────────────────────────────────────────────────
# Validator tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_validate_kpis_passes_with_required_columns():
    validate_kpis(_make_kpis())  # should not raise


@pytest.mark.unit
def test_validate_kpis_raises_on_missing_column():
    df = _make_kpis().drop(columns=["paid_avg"])
    with pytest.raises(ValueError, match="paid_avg"):
        validate_kpis(df)


@pytest.mark.unit
def test_validate_monthly_passes_with_required_columns():
    validate_monthly(_make_monthly())  # should not raise


@pytest.mark.unit
def test_validate_monthly_raises_on_missing_column():
    df = _make_monthly().drop(columns=["paid_total"])
    with pytest.raises(ValueError, match="paid_total"):
        validate_monthly(df)


@pytest.mark.unit
def test_validate_loss_ratio_passes_with_required_columns():
    validate_loss_ratio(_make_loss_ratio())  # should not raise


@pytest.mark.unit
def test_validate_loss_ratio_raises_on_missing_column():
    df = _make_loss_ratio().drop(columns=["loss_ratio_pct"])
    with pytest.raises(ValueError, match="loss_ratio_pct"):
        validate_loss_ratio(df)


@pytest.mark.unit
def test_validate_network_summary_passes_with_required_columns():
    validate_network_summary(_make_network_summary())  # should not raise


@pytest.mark.unit
def test_validate_network_summary_raises_on_missing_column():
    df = _make_network_summary().drop(columns=["utilization_pct"])
    with pytest.raises(ValueError, match="utilization_pct"):
        validate_network_summary(df)


@pytest.mark.unit
def test_validate_diagnosis_summary_passes_with_required_columns():
    validate_diagnosis_summary(_make_diagnosis_summary())  # should not raise


@pytest.mark.unit
def test_validate_diagnosis_summary_raises_on_missing_column():
    df = _make_diagnosis_summary().drop(columns=["billed_total"])
    with pytest.raises(ValueError, match="billed_total"):
        validate_diagnosis_summary(df)


# ────────────────────────────────────────────────────────────────────────────
# Full report generation tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_report_generates_all_compliance_sheets(tmp_path, monkeypatch):
    """The Excel workbook must contain all required insurance compliance sheets."""
    _write_outputs(
        tmp_path,
        kpis=_make_kpis(),
        monthly=_make_monthly(),
        loss_ratio=_make_loss_ratio(),
        network_summary=_make_network_summary(),
        diagnosis_summary=_make_diagnosis_summary(),
    )
    out_file = str(tmp_path / "report.xlsx")

    monkeypatch.chdir(tmp_path)
    main(out_file)

    xl = pd.ExcelFile(out_file)
    required_sheets = {"KPIs", "Monthly", "LossRatio", "NetworkUtilization", "DiagnosisSummary"}
    missing = required_sheets - set(xl.sheet_names)
    assert not missing, f"Report is missing required sheets: {sorted(missing)}"


@pytest.mark.unit
def test_report_kpis_sheet_columns(tmp_path, monkeypatch):
    """KPIs sheet must contain all required insurance KPI columns."""
    _write_outputs(tmp_path, kpis=_make_kpis())
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    main(out_file)

    kpis_df = pd.read_excel(out_file, sheet_name="KPIs")
    for col in ("age_band", "member_region", "in_network", "claims", "paid_total", "paid_avg"):
        assert col in kpis_df.columns, f"KPIs sheet missing column: {col}"


@pytest.mark.unit
def test_report_loss_ratio_sheet_columns(tmp_path, monkeypatch):
    """LossRatio sheet must contain all required loss ratio compliance columns."""
    _write_outputs(tmp_path, loss_ratio=_make_loss_ratio())
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    main(out_file)

    lr_df = pd.read_excel(out_file, sheet_name="LossRatio")
    for col in ("member_region", "in_network", "billed_total", "paid_total", "loss_ratio_pct"):
        assert col in lr_df.columns, f"LossRatio sheet missing column: {col}"


@pytest.mark.unit
def test_report_network_utilization_sheet_columns(tmp_path, monkeypatch):
    """NetworkUtilization sheet must contain utilization percentage column."""
    _write_outputs(tmp_path, network_summary=_make_network_summary())
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    main(out_file)

    ns_df = pd.read_excel(out_file, sheet_name="NetworkUtilization")
    assert "utilization_pct" in ns_df.columns


@pytest.mark.unit
def test_report_diagnosis_summary_sheet_columns(tmp_path, monkeypatch):
    """DiagnosisSummary sheet must contain ICD diagnosis_code and cost columns."""
    _write_outputs(tmp_path, diagnosis_summary=_make_diagnosis_summary())
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    main(out_file)

    ds_df = pd.read_excel(out_file, sheet_name="DiagnosisSummary")
    for col in ("diagnosis_code", "claims", "paid_total", "billed_total"):
        assert col in ds_df.columns, f"DiagnosisSummary sheet missing column: {col}"


@pytest.mark.unit
def test_report_model_metrics_sheet_present_when_file_exists(tmp_path, monkeypatch):
    """Model_Metrics sheet must appear when outputs/model_metrics.txt exists."""
    out_dir = tmp_path / "outputs"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "model_metrics.txt").write_text(
        "LogisticRegression accuracy: 0.8542\n", encoding="utf-8"
    )
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    main(out_file)

    xl = pd.ExcelFile(out_file)
    assert "Model_Metrics" in xl.sheet_names


@pytest.mark.unit
def test_report_succeeds_with_no_output_files(tmp_path, monkeypatch):
    """Report must still generate a valid (empty) workbook when no output CSVs exist."""
    monkeypatch.chdir(tmp_path)
    out_file = str(tmp_path / "report.xlsx")
    main(out_file)
    assert os.path.exists(out_file), "Workbook must be created even without input files"


@pytest.mark.unit
def test_report_raises_on_invalid_kpis_columns(tmp_path, monkeypatch):
    """Main() must raise ValueError if kpis.csv has missing required columns."""
    bad_kpis = pd.DataFrame({"age_band": ["0-18"], "claims": [5]})  # missing paid_total etc.
    _write_outputs(tmp_path, kpis=bad_kpis)
    out_file = str(tmp_path / "report.xlsx")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="KPIs output is missing required columns"):
        main(out_file)


@pytest.mark.unit
def test_report_uses_custom_output_dir(tmp_path):
    """Main() must read CSVs from output_dir without requiring chdir()."""
    custom_dir = tmp_path / "client_x" / "outputs"
    custom_dir.mkdir(parents=True)
    _make_kpis().to_csv(custom_dir / "kpis.csv", index=False)
    _make_monthly().to_csv(custom_dir / "monthly.csv", index=False)
    _make_loss_ratio().to_csv(custom_dir / "loss_ratio.csv", index=False)
    _make_network_summary().to_csv(custom_dir / "network_summary.csv", index=False)
    _make_diagnosis_summary().to_csv(custom_dir / "diagnosis_summary.csv", index=False)

    out_file = str(tmp_path / "client_report.xlsx")
    # No chdir() — pass output_dir explicitly
    main(out_file, output_dir=str(custom_dir))

    xl = pd.ExcelFile(out_file)
    required_sheets = {"KPIs", "Monthly", "LossRatio", "NetworkUtilization", "DiagnosisSummary"}
    assert not required_sheets - set(xl.sheet_names)
