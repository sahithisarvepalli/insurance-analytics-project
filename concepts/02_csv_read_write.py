#!/usr/bin/env python3
"""
Concept: Reading and Writing CSV Files
Description: Use pandas to read from CSV, manipulate data, and write back.
Example: Reads sample.csv, adds a column, writes to output.csv
"""

import os

import pandas as pd


def main():
    # Create sample data if file doesn't exist
    if not os.path.exists("sample.csv"):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        df.to_csv("sample.csv", index=False)
        print("Created sample.csv")

    # Read CSV
    df = pd.read_csv("sample.csv")
    print("Original data:")
    print(df)

    # Manipulate: add a greeting column
    df["greeting"] = "Hello, " + df["name"] + "!"

    # Write to new CSV
    df.to_csv("output.csv", index=False)
    print("Wrote output.csv with added column")


if __name__ == "__main__":
    main()
