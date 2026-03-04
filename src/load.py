
import argparse
import pandas as pd
from sqlalchemy import text
from .utils import get_engine, logger


def load_from_csv(members, providers, claims):
    eng = get_engine()
    with eng.begin() as con:
        # ensure schema exists
        con.execute(text('CREATE SCHEMA IF NOT EXISTS insurance;'))
    logger.info('Loading members...')
    pd.read_csv(members, parse_dates=['dob','effective_date','termination_date']).to_sql('member', eng, schema='insurance', if_exists='append', index=False)
    logger.info('Loading providers...')
    pd.read_csv(providers).to_sql('provider', eng, schema='insurance', if_exists='append', index=False)
    logger.info('Loading claims...')
    pd.read_csv(claims, parse_dates=['service_date']).to_sql('claim', eng, schema='insurance', if_exists='append', index=False)
    logger.info('Done loading CSVs.')


def main(args):
    if args.from_csv:
        load_from_csv(args.members, args.providers, args.claims)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--from-csv', action='store_true')
    ap.add_argument('--members', default='data/sample_members.csv')
    ap.add_argument('--providers', default='data/sample_providers.csv')
    ap.add_argument('--claims', default='data/sample_claims.csv')
    args = ap.parse_args()
    main(args)
