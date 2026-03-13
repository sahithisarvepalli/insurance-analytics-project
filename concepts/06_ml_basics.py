#!/usr/bin/env python3
"""
Concept: Machine Learning Basics
Description: Simple linear regression using scikit-learn.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

def main():
    # Generate sample data: predict score from age
    np.random.seed(42)
    ages = np.random.randint(18, 80, 200)
    scores = 100 - (ages - 18) * 0.5 + np.random.normal(0, 5, 200)  # Linear with noise
    scores = np.clip(scores, 0, 100)

    df = pd.DataFrame({"age": ages, "score": scores})

    # Split data
    X = df[["age"]]
    y = df["score"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error: {mse:.2f}")
    print(f"Coefficient: {model.coef_[0]:.2f}, Intercept: {model.intercept_:.2f}")

if __name__ == "__main__":
    main()