#!/usr/bin/env python3
"""
Concept: Date Handling
Description: Work with dates using pandas and datetime.
"""

import pandas as pd


def main():
    # Current date
    today = pd.Timestamp.today()
    print(f"Today: {today}")

    # Parse dates
    dates = pd.to_datetime(["2023-01-01", "2023-06-15", "2023-12-31"])
    print("Parsed dates:")
    print(dates)

    # Date arithmetic
    future = today + pd.Timedelta(days=30)
    print(f"30 days from now: {future}")

    # Age calculation
    birthdates = pd.to_datetime(["1990-05-10", "1985-03-20"])
    ages = (today - birthdates).days // 365
    print(f"Ages: {ages.tolist()}")

    # Format dates
    formatted = dates.strftime("%B %d, %Y")
    print("Formatted dates:")
    print(formatted)


if __name__ == "__main__":
    main()
