import argparse

from .generate_synthetic import gen_claims, gen_members, gen_providers
from .utils import get_engine, logger


def main(rows_members, rows_providers, rows_claims):
    eng = get_engine()
    gen_members(rows_members).to_sql(
        "member", eng, schema="insurance", if_exists="append", index=False
    )
    gen_providers(rows_providers).to_sql(
        "provider", eng, schema="insurance", if_exists="append", index=False
    )
    gen_claims(rows_claims, rows_members, rows_providers).to_sql(
        "claim", eng, schema="insurance", if_exists="append", index=False
    )
    logger.info("Seeded data directly into DB.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-members", type=int, default=10_000)
    ap.add_argument("--rows-providers", type=int, default=500)
    ap.add_argument("--rows-claims", type=int, default=50_000)
    args = ap.parse_args()
    main(args.rows_members, args.rows_providers, args.rows_claims)
