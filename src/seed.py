import argparse

from .generate_synthetic import gen_claims, gen_members, gen_providers
from .utils import get_engine, logger


def main(rows_members, rows_providers, rows_claims):
    eng = get_engine()
    members = gen_members(rows_members)
    providers = gen_providers(rows_providers)
    claims = gen_claims(rows_claims, rows_members, rows_providers)

    # Generate all data before opening the connection; write atomically
    with eng.begin() as con:
        members.to_sql("member", con, schema="insurance", if_exists="append", index=False)
        providers.to_sql("provider", con, schema="insurance", if_exists="append", index=False)
        claims.to_sql("claim", con, schema="insurance", if_exists="append", index=False)

    logger.info("Seeded data directly into DB.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-members", type=int, default=10_000)
    ap.add_argument("--rows-providers", type=int, default=500)
    ap.add_argument("--rows-claims", type=int, default=50_000)
    args = ap.parse_args()
    main(args.rows_members, args.rows_providers, args.rows_claims)
