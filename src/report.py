"""Generate an Excel summary report from the transform and model outputs."""

import argparse
import os

import pandas as pd


def main(out):
    """Compile KPI, monthly, and model metrics outputs into a single Excel workbook."""
    kpis = pd.read_csv("outputs/kpis.csv") if os.path.exists("outputs/kpis.csv") else None
    monthly = pd.read_csv("outputs/monthly.csv") if os.path.exists("outputs/monthly.csv") else None
    metrics_text = None
    if os.path.exists("outputs/model_metrics.txt"):
        with open("outputs/model_metrics.txt", encoding="utf-8") as fh:
            metrics_text = fh.read()
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        if kpis is not None:
            kpis.to_excel(xl, sheet_name="KPIs", index=False)
        if monthly is not None:
            monthly.to_excel(xl, sheet_name="Monthly", index=False)
        if metrics_text:
            pd.DataFrame({"metric": [metrics_text]}).to_excel(
                xl, sheet_name="Model_Metrics", index=False
            )
    print("Wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/insurance_summary.xlsx")
    args = ap.parse_args()
    os.makedirs("outputs", exist_ok=True)
    main(args.out)
