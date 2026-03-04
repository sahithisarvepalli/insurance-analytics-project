
import argparse
import pandas as pd
from sqlalchemy import text
from .utils import get_engine, logger


def load_from_csv(members, providers, claims):
    eng = get_engine()
    with eng.begin() as con:
        con.execute(text('CREATE SCHEMA IF NOT EXISTS insurance;'))

    def read_datesafe(path, date_cols):
        df = pd.read_csv(path, dtype={col: 'string' for col in date_cols})
        for col in date_cols:
            s = df[col].fillna('')
            mask_ns = s.str.match(r'^\d{15,19}$')
            if mask_ns.any():
                s_ns = pd.to_datetime(s.where(mask_ns, None), errors='coerce', unit='ns')
                s_iso = pd.to_datetime(s.where(~mask_ns, None), errors='coerce')
                df[col] = s_ns.fillna(s_iso)
            else:
                df[col] = pd.to_datetime(s, errors='coerce')
        return df

    members_df = read_datesafe(members, ['dob','effective_date','termination_date'])
    members_df.to_sql('member', eng, schema='insurance', if_exists='append', index=False)

    pd.read_csv(providers).to_sql('provider', eng, schema='insurance', if_exists='append', index=False)

    claims_df = read_datesafe(claims, ['service_date'])
    claims_df.to_sql('claim', eng, schema='insurance', if_exists='append', index=False)
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
