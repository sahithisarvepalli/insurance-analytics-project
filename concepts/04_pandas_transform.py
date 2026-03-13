#!/usr/bin/env python3
"""
Concept: Data Transformation with Pandas
Description: Load data, perform aggregations, filtering, and transformations.
"""

import pandas as pd
import numpy as np

def main():
    # Create sample data
    data = {
        "name": ["Alice", "Bob", "Charlie", "Alice"],
        "age": [25, 30, 35, 25],
        "score": [85, 90, 78, 92]
    }
    df = pd.DataFrame(data)
    print("Original data:")
    print(df)

    # Filter: ages > 25
    filtered = df[df["age"] > 25]
    print("\nFiltered (age > 25):")
    print(filtered)

    # Group by name and average score
    grouped = df.groupby("name")["score"].mean().reset_index()
    print("\nAverage score by name:")
    print(grouped)

    # Add a new column: age category
    df["age_category"] = pd.cut(df["age"], bins=[0, 30, 40, 100], labels=["Young", "Middle", "Old"])
    print("\nWith age category:")
    print(df)

if __name__ == "__main__":
    main()