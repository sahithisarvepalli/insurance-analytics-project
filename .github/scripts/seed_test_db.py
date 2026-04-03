"""Initialise the test database for CI integration tests.

Uses the same _apply_ddl() and _table_columns() helpers as src.load so:
- Schema always comes from sql/ddl_create_tables.sql (single source of truth).
- Seed DataFrames are trimmed to live-reflected columns — adding or removing a
  column in the DDL never requires touching this file.
"""

import sys

sys.path.insert(0, ".")

import pandas as pd  # noqa: E402

from src.load import _apply_ddl, _table_columns  # noqa: E402
from src.utils import get_engine  # noqa: E402

_SCHEMA = "insurance"

# ---------------------------------------------------------------------------
# Seed fixtures — define all candidate fields; extra columns are trimmed
# automatically against the live schema so this dict never needs to change
# when the DDL evolves (as long as the data stays valid for existing columns).
# ---------------------------------------------------------------------------
_MEMBERS = pd.DataFrame(
    [
        {
            "person_id": 1,
            "dob": "1980-01-15",
            "gender": "male",
            "region": "Northeast",
            "effective_date": "2020-01-01",
            "termination_date": None,
        },
        {
            "person_id": 2,
            "dob": "1975-06-20",
            "gender": "female",
            "region": "Southeast",
            "effective_date": "2019-03-01",
            "termination_date": None,
        },
        {
            "person_id": 3,
            "dob": "1990-11-05",
            "gender": "male",
            "region": "West",
            "effective_date": "2021-07-01",
            "termination_date": None,
        },
    ]
)

_PROVIDERS = pd.DataFrame(
    [
        {"specialty": "General Practice", "in_network": True, "region": "Northeast"},
        {"specialty": "Cardiology", "in_network": False, "region": "Southeast"},
        {"specialty": "Orthopedics", "in_network": True, "region": "West"},
    ]
)

_CLAIMS = pd.DataFrame(
    [
        {
            "member_id": 1,
            "provider_id": 1,
            "service_date": "2023-03-10",
            "diagnosis_code": "E11.9",
            "procedure_code": "99213",
            "billed_amount": 200.00,
            "allowed_amount": 160.00,
            "paid_amount": 128.00,
            "place_of_service": "Office",
        },
        {
            "member_id": 2,
            "provider_id": 2,
            "service_date": "2023-05-22",
            "diagnosis_code": "I10",
            "procedure_code": "93000",
            "billed_amount": 500.00,
            "allowed_amount": 350.00,
            "paid_amount": 280.00,
            "place_of_service": "Outpatient",
        },
        {
            "member_id": 3,
            "provider_id": 3,
            "service_date": "2023-08-14",
            "diagnosis_code": "M54.5",
            "procedure_code": "27447",
            "billed_amount": 800.00,
            "allowed_amount": 600.00,
            "paid_amount": 480.00,
            "place_of_service": "Office",
        },
    ]
)


def main() -> None:
    eng = get_engine()
    with eng.begin() as con:
        _apply_ddl(con)

    for df, table in [(_MEMBERS, "member"), (_PROVIDERS, "provider"), (_CLAIMS, "claim")]:
        cols = _table_columns(eng, table)
        df[[c for c in cols if c in df.columns]].to_sql(
            table, eng, schema=_SCHEMA, if_exists="append", index=False
        )

    print("Test database initialised and seeded successfully.")


if __name__ == "__main__":
    main()
