"""Generate realistic sample CSV files for local pipeline runs.

Produces three files in ``data/`` with the same schema and FK relationships
that the CI seed (``seed_test_db.py``) uses, just at a much larger scale:

    data/sample_members.csv    — N_MEMBERS rows
    data/sample_providers.csv  — N_PROVIDERS rows
    data/sample_claims.csv     — N_CLAIMS rows

Column names match the pipeline schema exactly so ``config/clients/sample.yaml``
needs no column_map and ``src/model.py`` needs no demographic fallback.

Usage
-----
    python scripts/generate_sample_data.py                 # default scale
    python scripts/generate_sample_data.py --claims 1000000  # 1 M claims
    python scripts/generate_sample_data.py --claims 20        # CI-scale smoke test
"""

# The heavy numeric/data-science dependencies used here (numpy, pandas)
# are optional for CI-run tests. Skip pylint checks for environments where
# those packages are not installed.
# pylint: skip-file

from __future__ import annotations

import argparse
import pathlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

_SEED = 42
_REGIONS = ["Northeast", "Southeast", "West", "Midwest", "Southwest"]
_GENDERS = ["male", "female"]
_SPECIALTIES = [
    "General Practice",
    "Cardiology",
    "Orthopedics",
    "Oncology",
    "Neurology",
    "Dermatology",
    "Pediatrics",
    "Psychiatry",
    "Radiology",
    "Emergency Medicine",
]
_DIAGNOSIS_CODES = [
    "E11.9",  # Type 2 diabetes
    "I10",  # Essential hypertension
    "J06.9",  # Acute upper respiratory infection
    "M54.5",  # Low back pain
    "Z00.00",  # General exam
    "F32.9",  # Major depressive disorder
    "J45.20",  # Mild intermittent asthma
    "K21.0",  # GERD
    "N39.0",  # UTI
    "S93.40",  # Ankle sprain
    "I25.10",  # Coronary artery disease
    "C34.10",  # Lung cancer
    "G43.909",  # Migraine
    "L40.0",  # Psoriasis
    "H52.4",  # Presbyopia
]
_PROCEDURE_CODES = [
    "99213",  # Office visit established
    "99214",  # Office visit moderate complexity
    "93000",  # ECG
    "71046",  # Chest X-ray
    "80053",  # Comprehensive metabolic panel
    "99283",  # ED visit moderate severity
    "27447",  # Total knee arthroplasty
    "43239",  # EGD with biopsy
    "45378",  # Colonoscopy
    "70553",  # MRI brain with contrast
]
_PLACES = ["Office", "Hospital", "Outpatient", "Urgent Care", "Emergency"]


def _random_date(rng: np.random.Generator, start: date, end: date) -> np.ndarray:
    delta = (end - start).days
    offsets = rng.integers(0, delta, size=1)[0]
    return start + timedelta(days=int(offsets))


def generate_members(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Return a members DataFrame with proper schema matching the pipeline DDL."""
    member_ids = np.arange(1, n + 1)
    # DOB: ages roughly 18–80
    today = date.today()
    min_dob = today.replace(year=today.year - 80)
    max_dob = today.replace(year=today.year - 18)
    dob_offsets = rng.integers(0, (max_dob - min_dob).days, size=n)
    dobs = [min_dob + timedelta(days=int(d)) for d in dob_offsets]

    eff_start = date(2015, 1, 1)
    eff_end = date(2023, 12, 31)
    eff_offsets = rng.integers(0, (eff_end - eff_start).days, size=n)
    effective_dates = [eff_start + timedelta(days=int(d)) for d in eff_offsets]

    return pd.DataFrame(
        {
            "member_id": member_ids,
            "person_id": member_ids,  # surrogate == person in this synthetic dataset
            "dob": [d.isoformat() for d in dobs],
            "gender": rng.choice(_GENDERS, size=n),
            "region": rng.choice(_REGIONS, size=n),
            "effective_date": [d.isoformat() for d in effective_dates],
            "termination_date": "",  # all active
        }
    )


def generate_providers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Return a providers DataFrame with proper schema matching the pipeline DDL."""
    provider_ids = np.arange(1, n + 1)
    # 70 % in-network
    in_network = rng.random(size=n) < 0.70
    return pd.DataFrame(
        {
            "provider_id": provider_ids,
            "specialty": rng.choice(_SPECIALTIES, size=n),
            "in_network": in_network,
            "region": rng.choice(_REGIONS, size=n),
        }
    )


def generate_claims(
    n: int, n_members: int, n_providers: int, rng: np.random.Generator
) -> pd.DataFrame:
    """Return a claims DataFrame referencing valid member_id and provider_id values."""
    svc_start = date(2020, 1, 1)
    svc_end = date(2024, 12, 31)
    svc_offsets = rng.integers(0, (svc_end - svc_start).days, size=n)
    service_dates = [svc_start + timedelta(days=int(d)) for d in svc_offsets]

    # Amounts: billed > allowed >= paid; use log-normal for realistic skew
    billed = np.round(rng.lognormal(mean=5.5, sigma=1.2, size=n), 2)
    allowed_ratio = rng.uniform(0.60, 0.95, size=n)
    allowed = np.round(billed * allowed_ratio, 2)
    paid_ratio = rng.uniform(0.80, 1.0, size=n)
    paid = np.round(allowed * paid_ratio, 2)

    return pd.DataFrame(
        {
            "member_id": rng.integers(1, n_members + 1, size=n),
            "provider_id": rng.integers(1, n_providers + 1, size=n),
            "service_date": [d.isoformat() for d in service_dates],
            "diagnosis_code": rng.choice(_DIAGNOSIS_CODES, size=n),
            "procedure_code": rng.choice(_PROCEDURE_CODES, size=n),
            "billed_amount": billed,
            "allowed_amount": allowed,
            "paid_amount": paid,
            "place_of_service": rng.choice(_PLACES, size=n),
        }
    )


def generate(
    n_claims: int = 300_000,
    n_members: int = 50_000,
    n_providers: int = 2_000,
    out_dir: str = "data",
) -> None:
    """Generate and write all three sample CSV files to *out_dir*."""
    rng = np.random.default_rng(_SEED)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Generating {n_members:,} members ...")
    members = generate_members(n_members, rng)
    members.to_csv(out / "sample_members.csv", index=False)

    print(f"Generating {n_providers:,} providers ...")
    providers = generate_providers(n_providers, rng)
    providers.to_csv(out / "sample_providers.csv", index=False)

    print(f"Generating {n_claims:,} claims ...")
    claims = generate_claims(n_claims, n_members, n_providers, rng)
    claims.to_csv(out / "sample_claims.csv", index=False)

    print(
        f"Done — written to {out}/\n"
        f"  sample_members.csv   {n_members:>10,} rows\n"
        f"  sample_providers.csv {n_providers:>10,} rows\n"
        f"  sample_claims.csv    {n_claims:>10,} rows"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate sample CSV data for local pipeline runs.")
    ap.add_argument("--claims", type=int, default=300_000, help="Number of claims rows.")
    ap.add_argument("--members", type=int, default=50_000, help="Number of member rows.")
    ap.add_argument("--providers", type=int, default=2_000, help="Number of provider rows.")
    ap.add_argument("--out-dir", default="data", help="Output directory.")
    args = ap.parse_args()
    generate(
        n_claims=args.claims,
        n_members=args.members,
        n_providers=args.providers,
        out_dir=args.out_dir,
    )
