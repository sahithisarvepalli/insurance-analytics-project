#!/usr/bin/env python3
"""
Concept: Excel Report Generation
Description: Write data to Excel with multiple sheets using pandas.

This mirrors the approach used in src/report.py, which produces a six-sheet
workbook: KPIs, Monthly, LossRatio, NetworkUtilization, DiagnosisSummary, Model_Metrics.
"""

import os

import pandas as pd


def main():
    # Sample KPI data
    kpis = pd.DataFrame(
        {
            "age_band": ["19-30", "31-45", "46-60"],
            "member_region": ["Northeast", "West", "Southeast"],
            "in_network": [True, True, False],
            "claims": [120, 95, 80],
            "paid_total": [48000.0, 52000.0, 61000.0],
            "paid_avg": [400.0, 547.4, 762.5],
        }
    )

    # Sample monthly trend
    monthly = pd.DataFrame(
        {
            "month": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "member_region": ["Northeast", "Northeast", "Northeast"],
            "in_network": [True, True, True],
            "claims": [40, 45, 35],
            "paid_total": [16000.0, 18000.0, 14000.0],
        }
    )

    # Sample model metrics
    model_metrics = pd.DataFrame({"metric": ["LogisticRegression accuracy: 0.8200"]})

    os.makedirs("outputs", exist_ok=True)
    with pd.ExcelWriter("outputs/report.xlsx", engine="openpyxl") as writer:
        kpis.to_excel(writer, sheet_name="KPIs", index=False)
        monthly.to_excel(writer, sheet_name="Monthly", index=False)
        model_metrics.to_excel(writer, sheet_name="Model_Metrics", index=False)

    print("Created outputs/report.xlsx with sheets: KPIs, Monthly, Model_Metrics")


if __name__ == "__main__":
    main()
