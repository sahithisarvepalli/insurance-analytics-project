
import numpy as np, pandas as pd, os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from .utils import get_engine, logger

def run_model():
    eng = get_engine()
    q = (
        "SELECT c.member_id, m.dob, m.region AS member_region, p.in_network, "
        "SUM(c.paid_amount) AS paid_total FROM insurance.claim c "
        "JOIN insurance.member m ON c.member_id = m.member_id "
        "JOIN insurance.provider p ON c.provider_id = p.provider_id "
        "GROUP BY c.member_id, m.dob, m.region, p.in_network"
    )
    df = pd.read_sql(q, eng, parse_dates=['dob'])
    today = pd.Timestamp('2024-12-31')
    df['age'] = (today - df['dob']).dt.days // 365

    thresh = np.quantile(df['paid_total'], 0.9)
    df['high_cost'] = (df['paid_total'] > thresh).astype(int)

    X = df[['age','member_region','in_network']]
    y = df['high_cost']

    pre = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['member_region','in_network'])
    ], remainder='passthrough')

    model = Pipeline([('pre', pre), ('clf', LogisticRegression(max_iter=1000))])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model.fit(Xtr, ytr)
    score = model.score(Xte, yte)
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/model_metrics.txt','w') as fh:
        fh.write(f'LogisticRegression accuracy: {score:.4f}\n')
    logger.info(f'Model accuracy: {score:.4f}')

if __name__ == '__main__':
    run_model()
