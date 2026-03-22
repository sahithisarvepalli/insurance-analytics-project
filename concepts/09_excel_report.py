#!/usr/bin/env python3
"""
Concept: Excel Report Generation
Description: Write data to Excel with multiple sheets using pandas.
"""

import os

import pandas as pd


def main():
    # Sample data
    df1 = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [85, 90]})
    df2 = pd.DataFrame({"Month": ["Jan", "Feb"], "Sales": [1000, 1200]})

    os.makedirs("outputs", exist_ok=True)
    with pd.ExcelWriter("outputs/report.xlsx", engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Scores", index=False)
        df2.to_excel(writer, sheet_name="Sales", index=False)

    print("Created outputs/report.xlsx with two sheets")


if __name__ == "__main__":
    main()
