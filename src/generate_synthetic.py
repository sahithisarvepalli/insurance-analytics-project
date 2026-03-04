
import argparse, os
import numpy as np, pandas as pd

def gen_members(n=50_000, seed=42):
    rng = np.random.default_rng(seed)
    dob = pd.to_datetime(rng.integers(1955,2005,size=n), format='%Y') + pd.to_timedelta(rng.integers(0,365,size=n), 'D')
    eff = pd.to_datetime('2022-01-01') + pd.to_timedelta(rng.integers(0,365,size=n),'D')
    term = np.where(rng.random(n)<0.1, eff + pd.to_timedelta(rng.integers(30,730,size=n),'D'), pd.NaT)
    return pd.DataFrame({
        'person_id': rng.integers(10_000_000, 99_999_999, size=n),
        'dob': dob,
        'gender': rng.choice(list('MF'), size=n),
        'region': rng.choice(['East','West','North','South'], size=n),
        'effective_date': eff,
        'termination_date': term
    })

def gen_providers(n=2_000, seed=43):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'specialty': rng.choice(['PCP','Cardiology','Ortho','Derm','Oncology'], size=n, p=[0.45,0.15,0.18,0.12,0.10]),
        'in_network': rng.choice([True, False], size=n, p=[0.8,0.2]),
        'region': rng.choice(['East','West','North','South'], size=n)
    })

def gen_claims(n=300_000, members_n=50_000, providers_n=2_000, seed=44):
    rng = np.random.default_rng(seed)
    service_dates = pd.to_datetime('2023-01-01') + pd.to_timedelta(rng.integers(0,365,size=n), 'D')
    paid = np.round(rng.gamma(2.0,150.0,size=n),2)
    allowed = np.round(paid * rng.uniform(1.0,1.3,size=n),2)
    billed = np.round(allowed * rng.uniform(1.0,1.5,size=n),2)
    return pd.DataFrame({
        'member_id': rng.integers(1, members_n+1, size=n),
        'provider_id': rng.integers(1, providers_n+1, size=n),
        'service_date': service_dates,
        'diagnosis_code': rng.choice(['I10','E11','M54','J06','C50','Z00'], size=n, p=[0.25,0.2,0.2,0.2,0.05,0.1]),
        'procedure_code': rng.choice(['99213','99214','93000','71020','80050','J9271'], size=n),
        'billed_amount': billed,
        'allowed_amount': allowed,
        'paid_amount': paid,
        'place_of_service': rng.choice(['Office','Inpatient','Outpatient','ER'], size=n, p=[0.6,0.1,0.25,0.05])
    })

def main(rows_members, rows_providers, rows_claims, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    gen_members(rows_members).to_csv(f'{out_dir}/sample_members.csv', index=False, date_format='%Y-%m-%d')
    gen_providers(rows_providers).to_csv(f'{out_dir}/sample_providers.csv', index=False)
    gen_claims(rows_claims, rows_members, rows_providers).to_csv(f'{out_dir}/sample_claims.csv', index=False, date_format='%Y-%m-%d')
    print('Generated CSVs in', out_dir)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows-members', type=int, default=50_000)
    ap.add_argument('--rows-providers', type=int, default=2_000)
    ap.add_argument('--rows-claims', type=int, default=300_000)
    ap.add_argument('--out-dir', default='data')
    args = ap.parse_args()
    main(args.rows_members, args.rows_providers, args.rows_claims, args.out_dir)
