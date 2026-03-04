
# Insurance Analytics (SAS → Python) – Full Project

Modern, end-to-end **insurance analytics** project that mirrors common SAS workflows using **Python + PostgreSQL**. Includes synthetic data generation, ETL, KPI aggregation, a simple ML model, reporting to Excel, and CI with GitHub Actions.

## ✨ Features
- Synthetic **members/providers/claims** datasets
- PostgreSQL schema + loaders via **pandas/SQLAlchemy**
- Transformations (joins, age bands), KPIs (frequency, severity, loss ratio)
- Basic ML (high-cost claimant classification)
- Excel report with multiple sheets
- **GitHub Actions** CI using a PostgreSQL service

## 🗂 Repository Structure
```
insurance-analytics-python/
  ├─ .github/workflows/ci-postgres.yml
  ├─ config/db.yaml
  ├─ sql/
  │   ├─ ddl_create_tables.sql
  │   └─ kpi_queries.sql
  ├─ src/
  │   ├─ generate_synthetic.py
  │   ├─ load.py
  │   ├─ transform.py
  │   ├─ model.py
  │   ├─ report.py
  │   ├─ seed.py
  │   └─ utils.py
  ├─ tests/test_db.py
  ├─ data/sample_members.csv
  ├─ data/sample_providers.csv
  ├─ data/sample_claims.csv
  ├─ outputs/
  ├─ requirements.txt
  ├─ .env.example
  ├─ .gitignore
  ├─ LICENSE
  └─ README.md
```

## 🚀 Quick Start (Local)
1. **Create env & install deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Start PostgreSQL** (Docker example):
   ```bash
   docker run --name insurdb -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=insurdb -p 5432:5432 -d postgres:15
   ```
3. **Set env** (or copy `.env.example`):
   ```bash
   export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb
   ```
4. **Create schema & tables**
   ```bash
   psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS insurance;" || true
   psql "$DATABASE_URL" -f sql/ddl_create_tables.sql
   ```
5. **Generate and load synthetic data**
   ```bash
   python -m src.generate_synthetic --rows-members 50000 --rows-providers 2000 --rows-claims 300000 --out-dir data/
   python -m src.load --from-csv --members data/sample_members.csv --providers data/sample_providers.csv --claims data/sample_claims.csv
   ```
6. **Transform, KPIs, Model, Report**
   ```bash
   python -m src.transform
   python -m src.model
   python -m src.report --out outputs/insurance_summary.xlsx
   ```

> **Tip:** For a no-DB quick try, set `DATABASE_URL=sqlite:///local.db`. The DDL and loaders will adapt where possible.

## 🧪 CI – GitHub Actions
A ready workflow spins up PostgreSQL, applies DDL, seeds data, and runs tests. See `.github/workflows/ci-postgres.yml`.

## 📊 Data Model
- `insurance.member(member_id, person_id, dob, gender, region, effective_date, termination_date)`
- `insurance.provider(provider_id, specialty, in_network, region)`
- `insurance.claim(claim_id, member_id, provider_id, service_date, diagnosis_code, procedure_code, billed_amount, allowed_amount, paid_amount, place_of_service)`

## 📝 License
MIT
