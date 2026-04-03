"""Initialise the test database for CI integration tests.

Uses the same _apply_ddl() and _table_columns() helpers as src.load so:
- Schema always comes from src/sql/ddl_create_tables.sql (single source of truth).
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
# 20 members spread across regions/genders to give the model enough variation.
_MEMBERS = pd.DataFrame(
    [
        {
            "person_id": i,
            "dob": dob,
            "gender": gender,
            "region": region,
            "effective_date": "2020-01-01",
            "termination_date": None,
        }
        for i, (dob, gender, region) in enumerate(
            [
                ("1980-01-15", "male", "Northeast"),
                ("1975-06-20", "female", "Southeast"),
                ("1990-11-05", "male", "West"),
                ("1985-03-22", "female", "Midwest"),
                ("1978-09-10", "male", "Northeast"),
                ("1992-07-04", "female", "Southeast"),
                ("1968-12-30", "male", "West"),
                ("1983-04-18", "female", "Midwest"),
                ("1995-08-25", "male", "Northeast"),
                ("1970-02-14", "female", "Southeast"),
                ("1988-05-07", "male", "West"),
                ("1976-10-31", "female", "Midwest"),
                ("1993-01-09", "male", "Northeast"),
                ("1965-06-15", "female", "Southeast"),
                ("1987-03-27", "male", "West"),
                ("1972-11-20", "female", "Midwest"),
                ("1996-09-03", "male", "Northeast"),
                ("1982-04-11", "female", "Southeast"),
                # Members 19 & 20 will have very high claims → high_cost = 1
                ("1960-07-22", "male", "West"),
                ("1955-01-05", "female", "Midwest"),
            ],
            start=1,
        )
    ]
)

# 5 providers cycling through the claims below.
_PROVIDERS = pd.DataFrame(
    [
        {"specialty": "General Practice", "in_network": True, "region": "Northeast"},
        {"specialty": "Cardiology", "in_network": False, "region": "Southeast"},
        {"specialty": "Orthopedics", "in_network": True, "region": "West"},
        {"specialty": "Oncology", "in_network": False, "region": "Midwest"},
        {"specialty": "Neurology", "in_network": True, "region": "Northeast"},
    ]
)

# One claim per member.  Members 19 & 20 have large paid_amounts so they land
# above the 90th-percentile threshold → high_cost = 1.  This guarantees
# class_counts.min() >= 2, allowing src.model to use a stratified split.
_LOW_COST = [
    (1, 1, "2023-01-10", "E11.9", "99213", 200, 160, 128, "Office"),
    (2, 2, "2023-02-14", "I10", "93000", 300, 240, 192, "Outpatient"),
    (3, 3, "2023-03-20", "M54.5", "27447", 250, 200, 160, "Office"),
    (4, 4, "2023-04-05", "J45.9", "94010", 180, 144, 115, "Office"),
    (5, 5, "2023-05-12", "K21.0", "43239", 350, 280, 224, "Outpatient"),
    (6, 1, "2023-06-18", "E11.9", "99213", 220, 176, 141, "Office"),
    (7, 2, "2023-07-22", "I10", "93000", 310, 248, 198, "Outpatient"),
    (8, 3, "2023-08-30", "M54.5", "27447", 270, 216, 173, "Office"),
    (9, 4, "2023-09-07", "J45.9", "94010", 190, 152, 122, "Office"),
    (10, 5, "2023-10-15", "K21.0", "43239", 360, 288, 230, "Outpatient"),
    (11, 1, "2023-11-02", "E11.9", "99213", 230, 184, 147, "Office"),
    (12, 2, "2023-12-10", "I10", "93000", 320, 256, 205, "Outpatient"),
    (13, 3, "2023-01-25", "M54.5", "27447", 260, 208, 166, "Office"),
    (14, 4, "2023-02-28", "J45.9", "94010", 195, 156, 125, "Office"),
    (15, 5, "2023-03-15", "K21.0", "43239", 370, 296, 237, "Outpatient"),
    (16, 1, "2023-04-22", "E11.9", "99213", 210, 168, 134, "Office"),
    (17, 2, "2023-05-30", "I10", "93000", 330, 264, 211, "Outpatient"),
    (18, 3, "2023-06-08", "M54.5", "27447", 280, 224, 179, "Office"),
]
_HIGH_COST = [
    (19, 4, "2023-07-14", "C34.1", "32480", 6000, 4800, 3840, "Inpatient"),
    (20, 5, "2023-08-19", "C18.9", "44140", 8000, 6400, 5120, "Inpatient"),
]

_CLAIMS = pd.DataFrame(
    [
        {
            "member_id": r[0],
            "provider_id": r[1],
            "service_date": r[2],
            "diagnosis_code": r[3],
            "procedure_code": r[4],
            "billed_amount": float(r[5]),
            "allowed_amount": float(r[6]),
            "paid_amount": float(r[7]),
            "place_of_service": r[8],
        }
        for r in _LOW_COST + _HIGH_COST
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
