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


def _read_output(filename: str, output_dir: str = "outputs") -> pd.DataFrame | None:
    """Read a CSV from *output_dir*; return None if absent."""
    path = os.path.join(output_dir, filename)
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


def _load_outputs(
    output_dir: str = "outputs",
) -> tuple[dict[str, pd.DataFrame | None], str | None]:
    """Read all pipeline output files from *output_dir*; return (dataframes_by_key, metrics_text)."""
    outputs: dict[str, pd.DataFrame | None] = {
        "kpis": _read_output("kpis.csv", output_dir),
        "monthly": _read_output("monthly.csv", output_dir),
        "loss_ratio": _read_output("loss_ratio.csv", output_dir),
        "network_summary": _read_output("network_summary.csv", output_dir),
        "diagnosis_summary": _read_output("diagnosis_summary.csv", output_dir),
    }
    metrics_text: str | None = None
    metrics_path = os.path.join(output_dir, "model_metrics.txt")
    if os.path.exists(metrics_path):
        with open(metrics_path, encoding="utf-8") as fh:
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
        sheets_written += 1
    return sheets_written


def main(out, output_dir: str = "outputs", client_name: str = "Insurance Analytics"):
    """Compile insurance compliance KPI outputs into a single Excel workbook.

    Parameters
    ----------
    out:
        Destination path for the Excel workbook.
    output_dir:
        Directory containing the pipeline CSV outputs to read.
    client_name:
        Client name included in the workbook filename and used for logging.
    """
    outputs, metrics_text = _load_outputs(output_dir)
    _validate_outputs(outputs)
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        _write_workbook(xl, outputs, metrics_text)
    print(f"[{client_name}] Wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate an insurance compliance Excel report from transform outputs."
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output Excel file path (default: <output-dir>/insurance_summary.xlsx).",
    )
    ap.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory containing pipeline CSV outputs (default: outputs).",
    )
    ap.add_argument(
        "--client-name",
        default="Insurance Analytics",
        help="Client name for the report (default: Insurance Analytics).",
    )
    args = ap.parse_args()
    out_path = args.out or os.path.join(args.output_dir, "insurance_summary.xlsx")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    main(out_path, output_dir=args.output_dir, client_name=args.client_name)
