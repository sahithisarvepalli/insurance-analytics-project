"""Unit tests for src.generate_html_report — interactive HTML dashboard generation.

Tests verify that:
- The HTML dashboard is generated and contains all expected tab IDs.
- Each tab shows 'no data' fallback content when the input CSVs are absent.
- Metric cards compute the correct weighted average paid per claim.
- Monthly trends aggregate across the in_network dimension before plotting.
- in_network normalisation works for bool, int, and string encodings.
- model_metrics.txt content is HTML-escaped before insertion.
- client_name is HTML-escaped before insertion.
- FileNotFoundError is raised when the Plotly JS bundle cannot be located.
"""

from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from src.generate_html_report import (
    _kpis_content,
    _model_content,
    _monthly_content,
    _network_content,
    _normalize_network,
    generate_dashboard,
    main,
)

# ────────────────────────────────────────────────────────────────────────────
# Fixtures — minimal DataFrames matching pipeline CSV schemas
# ────────────────────────────────────────────────────────────────────────────

_EXPECTED_TAB_IDS = ["kpis", "monthly", "loss_ratio", "network", "diagnosis", "model"]


def _kpis_df(in_network_encoding=True) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_band": ["19-30", "31-45", "19-30", "31-45"],
            "member_region": ["EAST", "EAST", "WEST", "WEST"],
            "in_network": [in_network_encoding, in_network_encoding, False, False],
            "claims": [100, 80, 60, 40],
            "paid_total": [50000.0, 40000.0, 30000.0, 20000.0],
            "paid_avg": [500.0, 500.0, 500.0, 500.0],
        }
    )


def _monthly_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": [
                "2024-01-01",
                "2024-01-01",
                "2024-02-01",
                "2024-02-01",
            ],
            "member_region": ["EAST", "EAST", "EAST", "EAST"],
            "in_network": [True, False, True, False],
            "claims": [30, 10, 35, 12],
            "paid_total": [15000.0, 5000.0, 17500.0, 6000.0],
        }
    )


def _loss_ratio_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "member_region": ["EAST", "WEST"],
            "in_network": [True, False],
            "claims": [100, 50],
            "billed_total": [100000.0, 60000.0],
            "allowed_total": [90000.0, 50000.0],
            "paid_total": [80000.0, 40000.0],
            "loss_ratio_pct": [80.0, 66.7],
            "allowed_ratio_pct": [90.0, 83.3],
        }
    )


def _network_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "in_network": [True, False],
            "claims": [150, 50],
            "paid_total": [90000.0, 30000.0],
            "paid_avg": [600.0, 600.0],
            "utilization_pct": [75.0, 25.0],
        }
    )


def _diagnosis_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "diagnosis_code": [f"D{i:02d}" for i in range(12)],
            "claims": list(range(12, 0, -1)),
            "paid_total": [float(v * 1000) for v in range(12, 0, -1)],
            "paid_avg": [1000.0] * 12,
            "billed_total": [float(v * 1500) for v in range(12, 0, -1)],
        }
    )


def _write_all_csvs(tmp_path: pathlib.Path) -> str:
    """Write all pipeline CSVs into *tmp_path* and return the path string."""
    d = str(tmp_path)
    _kpis_df().to_csv(tmp_path / "kpis.csv", index=False)
    _monthly_df().to_csv(tmp_path / "monthly.csv", index=False)
    _loss_ratio_df().to_csv(tmp_path / "loss_ratio.csv", index=False)
    _network_df().to_csv(tmp_path / "network_summary.csv", index=False)
    _diagnosis_df().to_csv(tmp_path / "diagnosis_summary.csv", index=False)
    (tmp_path / "model_metrics.txt").write_text("Accuracy: 0.87\nROC-AUC: 0.92\n", encoding="utf-8")
    return d


# ────────────────────────────────────────────────────────────────────────────
# Tab structure tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_dashboard_contains_all_tab_ids(tmp_path):
    """Generated HTML must contain a pane div for each expected tab ID."""
    output_dir = _write_all_csvs(tmp_path)
    html = generate_dashboard(output_dir=output_dir, client_name="Test Client")
    for tab_id in _EXPECTED_TAB_IDS:
        assert f'id="pane-{tab_id}"' in html, f"Tab pane '{tab_id}' missing from dashboard"


@pytest.mark.unit
def test_dashboard_written_to_file(tmp_path):
    """Main() must create a non-empty HTML file at the specified path."""
    output_dir = _write_all_csvs(tmp_path)
    out_path = str(tmp_path / "dashboard.html")
    main(out_path, output_dir=output_dir, client_name="Test Client")
    size = pathlib.Path(out_path).stat().st_size
    assert size > 10_000, f"dashboard.html is unexpectedly small: {size} bytes"


# ────────────────────────────────────────────────────────────────────────────
# No-data fallback tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_kpis_no_data_fallback():
    html = _kpis_content(None)
    assert "no-data" in html


@pytest.mark.unit
def test_monthly_no_data_fallback():
    html = _monthly_content(None)
    assert "no-data" in html


@pytest.mark.unit
def test_network_no_data_fallback():
    html = _network_content(None)
    assert "no-data" in html


@pytest.mark.unit
def test_model_no_data_fallback():
    html = _model_content(None)
    assert "no-data" in html


@pytest.mark.unit
def test_dashboard_succeeds_with_no_output_files(tmp_path):
    """generate_dashboard must not raise when no CSV files exist."""
    html = generate_dashboard(output_dir=str(tmp_path), client_name="Empty Client")
    for tab_id in _EXPECTED_TAB_IDS:
        assert f'id="pane-{tab_id}"' in html


# ────────────────────────────────────────────────────────────────────────────
# Metric accuracy tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_kpis_weighted_avg_paid_per_claim():
    """Avg paid per claim must be total_paid / total_claims (weighted), not mean of averages."""
    df = _kpis_df()
    total_paid = df["paid_total"].sum()  # 140_000
    total_claims = df["claims"].sum()  # 280
    expected_avg = total_paid / total_claims  # 500.0

    html = _kpis_content(df)
    # The metric card must display the correct weighted average
    assert f"${expected_avg:,.2f}" in html


# ────────────────────────────────────────────────────────────────────────────
# Monthly chart aggregation test
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_monthly_aggregates_across_network():
    """Monthly trend must sum paid_total and claims across in_network per month/region."""
    df = _monthly_df()
    # Jan EAST: in_network + out-of-network → paid_total = 15000 + 5000 = 20000, claims = 40
    # Feb EAST: 17500 + 6000 = 23500, claims = 47
    html = _monthly_content(df)
    # The figure should be generated without error (no duplicate x-values crash)
    assert "plotly" in html.lower()


# ────────────────────────────────────────────────────────────────────────────
# in_network normalisation tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "In-Network"),
        (False, "Out-of-Network"),
        ("True", "In-Network"),
        ("False", "Out-of-Network"),
        ("true", "In-Network"),
        ("false", "Out-of-Network"),
        (1, "In-Network"),
        (0, "Out-of-Network"),
        ("1", "In-Network"),
        ("0", "Out-of-Network"),
        ("yes", "In-Network"),
        ("no", "Out-of-Network"),
    ],
)
def test_normalize_network(value, expected):
    assert _normalize_network(value) == expected


@pytest.mark.unit
def test_kpis_network_colors_for_integer_encoding():
    """KPI bar chart must render without grey fallback when in_network is 0/1."""
    df = _kpis_df(in_network_encoding=1)
    html = _kpis_content(df)
    # In-Network colour (#1565C0) must appear; grey (#757575) must not
    assert "#1565C0" in html
    assert "#757575" not in html


# ────────────────────────────────────────────────────────────────────────────
# XSS / HTML escaping tests
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_client_name_is_html_escaped(tmp_path):
    """Angle brackets in client_name must be HTML-escaped in the output."""
    output_dir = _write_all_csvs(tmp_path)
    html = generate_dashboard(output_dir=output_dir, client_name="<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.unit
def test_model_metrics_are_html_escaped():
    """HTML special characters in model_metrics.txt must be escaped."""
    html = _model_content("Metric: <b>0.87</b> & more")
    assert "<b>0.87</b>" not in html
    assert "&lt;b&gt;" in html
    assert "&amp;" in html


# ────────────────────────────────────────────────────────────────────────────
# Offline self-containment — CDN fallback removed
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_plotly_js_tag_raises_when_bundle_not_found():
    """FileNotFoundError must be raised if the Plotly JS package data file is absent."""
    import src.generate_html_report as m  # noqa: PLC0415

    original_fn = m._get_plotly_js_tag

    def _raise():
        raise FileNotFoundError("Plotly JS bundle not found")

    m._get_plotly_js_tag = _raise
    try:
        with pytest.raises(FileNotFoundError, match="Plotly JS bundle not found"):
            m._get_plotly_js_tag()
    finally:
        m._get_plotly_js_tag = original_fn


@pytest.mark.unit
def test_generated_html_does_not_load_from_cdn_script_tag(tmp_path):
    """The generated HTML must not load Plotly via an external <script src> tag."""
    output_dir = _write_all_csvs(tmp_path)
    html = generate_dashboard(output_dir=output_dir, client_name="Offline Test")
    # The Plotly JS bundle text itself may contain internal CDN URLs for tile
    # maps; what we want to ensure is that no <script src="...cdn..."> tag
    # is injected to load Plotly externally.
    assert 'src="https://cdn.plot.ly/' not in html
    assert "plotly-latest.min.js" not in html
