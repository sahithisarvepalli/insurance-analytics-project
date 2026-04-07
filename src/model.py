"""Logistic regression model for identifying high-cost insurance claimants."""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .utils import get_engine, logger


def run_model(output_dir: str = "outputs"):
    """Train a logistic regression model to predict high-cost members and write metrics.

    Parameters
    ----------
    output_dir:
        Directory where ``model_metrics.txt`` is written.  Defaults to ``"outputs"``.
        Pass a client-specific path (e.g. ``"outputs/client_a"``) to isolate
        per-client results.
    """
    eng = get_engine()
    q = """
        SELECT c.member_id, m.dob, m.region AS member_region, p.in_network,
               SUM(c.paid_amount) AS paid_total
        FROM insurance.claim c
        JOIN insurance.member m ON c.member_id = m.member_id
        JOIN insurance.provider p ON c.provider_id = p.provider_id
        GROUP BY c.member_id, m.dob, m.region, p.in_network
    """
    df = pd.read_sql(q, eng, parse_dates=["dob"])
    today = pd.Timestamp.now().normalize()
    df["age"] = (today - df["dob"]).dt.days // 365

    thresh = np.quantile(df["paid_total"], 0.9)
    df["high_cost"] = (df["paid_total"] > thresh).astype(int)

    X = df[["age", "member_region", "in_network"]]
    y = df["high_cost"]

    # Scale numeric features; encode categoricals; use class_weight for 90th-pctile imbalance
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), ["age"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["member_region", "in_network"]),
        ]
    )

    model = Pipeline(
        [("pre", pre), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))]
    )

    class_counts = y.value_counts()
    can_stratify = y.nunique() > 1 and not class_counts.empty and class_counts.min() >= 2

    if can_stratify:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
        model.fit(Xtr, ytr)
        score = model.score(Xte, yte)
        metric_label = "LogisticRegression accuracy"
    else:
        # Small seeded datasets in CI may not support stratified splitting.
        if y.nunique() < 2:
            score = 1.0
            metric_label = "LogisticRegression skipped (single target class), baseline accuracy"
        else:
            model.fit(X, y)
            score = model.score(X, y)
            metric_label = "LogisticRegression train accuracy (fallback, no stratified split)"

        logger.warning(
            "Fallback model path used due to insufficient class counts for stratified split: %s",
            class_counts.to_dict(),
        )
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "model_metrics.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"{metric_label}: {score:.4f}\n")
    logger.info("Model accuracy: %.4f", score)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the high-cost member prediction model.")
    ap.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to write model_metrics.txt (default: outputs).",
    )
    args = ap.parse_args()
    run_model(output_dir=args.output_dir)
