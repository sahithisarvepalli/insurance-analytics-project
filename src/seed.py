
import argparse
from .generate_synthetic import gen_members, gen_providers, gen_claims
from .utils import get_engine, logger


def main(rows_members, rows_providers, rows_claims):
    eng = get_engine()
    m = gen_members(rows_members)
    p = gen_providers(rows_providers)
    c = gen_claims(rows_claims, rows_members, rows_providers)

    m.to_sql('member', eng, schema='insurance', if_exists='append', index=False)
    p.to_sql('provider', eng, schema='insurance', if_exists='append', index=False)
    c.to_sql('claim', eng, schema='insurance', if_exists='append', index=False)
    logger.info('Seeded data directly into DB.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows-members', type=int, default=10_000)
    ap.add_argument('--rows-providers', type=int, default=500)
    ap.add_argument('--rows-claims', type=int, default=50_000)
    args = ap.parse_args()
    main(args.rows_members, args.rows_providers, args.rows_claims)
