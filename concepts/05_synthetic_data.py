#!/usr/bin/env python3
"""
Concept: Generating Synthetic Data
Description: Use numpy to generate random data with distributions.
"""

import numpy as np
import pandas as pd

def main():
    rng = np.random.default_rng(42)  # Reproducible random

    # Generate ages: normal distribution
    ages = rng.normal(30, 10, 100).astype(int)
    ages = np.clip(ages, 18, 80)  # Clip to reasonable range

    # Generate scores: uniform
    scores = rng.integers(50, 100, 100)

    # Generate names: random choice
    names = rng.choice(["Alice", "Bob", "Charlie", "Diana"], 100)

    df = pd.DataFrame({"name": names, "age": ages, "score": scores})
    print("Synthetic data sample:")
    print(df.head(10))

    df.to_csv("synthetic_data.csv", index=False)
    print("Saved to synthetic_data.csv")

if __name__ == "__main__":
    main()