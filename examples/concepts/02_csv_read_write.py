#!/usr/bin/env python3
"""
Concept: Reading and Writing CSV Files
Description: Use pandas to read from CSV, manipulate data, and write back.
Example: Reads sample.csv, adds a column, writes to output.csv
"""

import os

import pandas as pd


def main():
    os.makedirs("build/scratch", exist_ok=True)
    sample_path = "build/scratch/sample.csv"
    output_path = "build/scratch/output.csv"

    # Create sample data if file doesn't exist
    if not os.path.exists(sample_path):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        df.to_csv(sample_path, index=False)
        print("Created build/scratch/sample.csv")

    # Read CSV
    df = pd.read_csv(sample_path)
    print("Original data:")
    print(df)

    # Manipulate: add a greeting column
    df["greeting"] = "Hello, " + df["name"] + "!"

    # Write to new CSV
    df.to_csv(output_path, index=False)
    print("Wrote build/scratch/output.csv with added column")


if __name__ == "__main__":
    main()
