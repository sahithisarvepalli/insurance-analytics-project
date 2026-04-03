#!/usr/bin/env python3
"""
Concept: Machine Learning Basics
Description: Binary classification with logistic regression using scikit-learn.

This mirrors the approach used in src/model.py — identifying high-cost members
using logistic regression with preprocessing and class-weight balancing.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def main():
    # Generate sample insurance-like data
    rng = np.random.default_rng(42)
    n = 500

    ages = rng.integers(18, 80, n)
    regions = rng.choice(["Northeast", "Southeast", "West", "Midwest"], n)
    in_network = rng.choice([True, False], n)
    paid_total = rng.exponential(scale=3000, size=n)

    df = pd.DataFrame(
        {"age": ages, "region": regions, "in_network": in_network, "paid_total": paid_total}
    )

    # Label: top 10th percentile of paid_total = high-cost (mirrors src/model.py)
    threshold = np.quantile(df["paid_total"], 0.9)
    df["high_cost"] = (df["paid_total"] > threshold).astype(int)
    print(f"High-cost members: {df['high_cost'].sum()} / {len(df)} ({df['high_cost'].mean():.1%})")

    X = df[["age", "region", "in_network"]]
    y = df["high_cost"]

    # Preprocessing: scale numeric, one-hot encode categoricals
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), ["age"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["region", "in_network"]),
        ]
    )

    model = Pipeline(
        [("pre", pre), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))]
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f"Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()
