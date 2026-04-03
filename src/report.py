"""Generate an insurance compliance Excel summary report from the transform and model outputs.

The report conforms to standard insurance analytics reporting requirements and
includes the following worksheets:

* **KPIs** — claim counts, paid totals, and averages segmented by age band,
  member region, and network status.
* **Monthly** — monthly trend summary of claims and paid amounts.
* **LossRatio** — paid, allowed, and billed amounts with derived loss ratio
  percentage and allowed ratio percentage by region and network status.
* **NetworkUtilization** — in-network vs out-of-network claim counts, costs,
  and network penetration percentages.
* **DiagnosisSummary** — claims and costs ranked by ICD diagnosis code.
* **Model_Metrics** — accuracy metrics from the predictive model run.
"""

import argparse
import os

import pandas as pd


def _read_output(filename: str) -> pd.DataFrame | None:
    """Read a CSV from the outputs directory; return None if absent."""
    path = os.path.join("outputs", filename)
    return pd.read_csv(path) if os.path.exists(path) else None


_REQUIRED_KPI_COLUMNS = {
    "age_band",
    "member_region",
    "in_network",
    "claims",
    "paid_total",
    "paid_avg",
}
_REQUIRED_MONTHLY_COLUMNS = {"month", "member_region", "in_network", "claims", "paid_total"}
_REQUIRED_LOSS_RATIO_COLUMNS = {
    "member_region",
    "in_network",
    "claims",
    "billed_total",
    "allowed_total",
    "paid_total",
    "loss_ratio_pct",
    "allowed_ratio_pct",
}
_REQUIRED_NETWORK_COLUMNS = {"in_network", "claims", "paid_total", "paid_avg", "utilization_pct"}
_REQUIRED_DIAGNOSIS_COLUMNS = {"diagnosis_code", "claims", "paid_total", "paid_avg", "billed_total"}


def validate_kpis(df: pd.DataFrame) -> None:
    """Raise ValueError if the KPIs DataFrame is missing required columns."""
    missing = _REQUIRED_KPI_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"KPIs output is missing required columns: {sorted(missing)}")


def validate_monthly(df: pd.DataFrame) -> None:
    """Raise ValueError if the monthly DataFrame is missing required columns."""
    missing = _REQUIRED_MONTHLY_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Monthly output is missing required columns: {sorted(missing)}")


def validate_loss_ratio(df: pd.DataFrame) -> None:
    """Raise ValueError if the loss ratio DataFrame is missing required columns."""
    missing = _REQUIRED_LOSS_RATIO_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Loss ratio output is missing required columns: {sorted(missing)}")


def validate_network_summary(df: pd.DataFrame) -> None:
    """Raise ValueError if the network summary DataFrame is missing required columns."""
    missing = _REQUIRED_NETWORK_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Network utilization output is missing required columns: {sorted(missing)}"
        )


def validate_diagnosis_summary(df: pd.DataFrame) -> None:
    """Raise ValueError if the diagnosis summary DataFrame is missing required columns."""
    missing = _REQUIRED_DIAGNOSIS_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Diagnosis summary output is missing required columns: {sorted(missing)}")


_SHEET_MAP: dict[str, str] = {
    "kpis": "KPIs",
    "monthly": "Monthly",
    "loss_ratio": "LossRatio",
    "network_summary": "NetworkUtilization",
    "diagnosis_summary": "DiagnosisSummary",
}

_VALIDATORS = {
    "kpis": validate_kpis,
    "monthly": validate_monthly,
    "loss_ratio": validate_loss_ratio,
    "network_summary": validate_network_summary,
    "diagnosis_summary": validate_diagnosis_summary,
}


def _load_outputs() -> tuple[dict[str, pd.DataFrame | None], str | None]:
    """Read all pipeline output files; return (dataframes_by_key, metrics_text)."""
    outputs: dict[str, pd.DataFrame | None] = {
        "kpis": _read_output("kpis.csv"),
        "monthly": _read_output("monthly.csv"),
        "loss_ratio": _read_output("loss_ratio.csv"),
        "network_summary": _read_output("network_summary.csv"),
        "diagnosis_summary": _read_output("diagnosis_summary.csv"),
    }
    metrics_text: str | None = None
    if os.path.exists("outputs/model_metrics.txt"):
        with open("outputs/model_metrics.txt", encoding="utf-8") as fh:
            metrics_text = fh.read()
    return outputs, metrics_text


def _validate_outputs(outputs: dict[str, pd.DataFrame | None]) -> None:
    """Run column-level validation for every non-None output DataFrame."""
    for key, validator in _VALIDATORS.items():
        df = outputs.get(key)
        if df is not None:
            validator(df)


def _write_workbook(
    xl: pd.ExcelWriter,
    outputs: dict[str, pd.DataFrame | None],
    metrics_text: str | None,
) -> int:
    """Write all data sheets to *xl*; return the number of sheets written."""
    sheets_written = 0
    for key, sheet_name in _SHEET_MAP.items():
        df = outputs.get(key)
        if df is not None:
            df.to_excel(xl, sheet_name=sheet_name, index=False)
            sheets_written += 1
    if metrics_text:
        pd.DataFrame({"metric": [metrics_text]}).to_excel(
            xl, sheet_name="Model_Metrics", index=False
        )
        sheets_written += 1
    if sheets_written == 0:
        pd.DataFrame({"status": ["No output data available. Run the pipeline first."]}).to_excel(
            xl, sheet_name="Summary", index=False
        )
    return sheets_written


def main(out):
    """Compile insurance compliance KPI outputs into a single Excel workbook."""
    outputs, metrics_text = _load_outputs()
    _validate_outputs(outputs)
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        _write_workbook(xl, outputs, metrics_text)
    print("Wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate an insurance compliance Excel report from transform outputs."
    )
    ap.add_argument("--out", default="outputs/insurance_summary.xlsx")
    args = ap.parse_args()
    os.makedirs("outputs", exist_ok=True)
    main(args.out)
