# 🏗️ Architecture

> **Concept:** This project is an end-to-end **data pipeline** — raw insurance data flows through five stages and comes out the other end as a columnar data warehouse, business reports, and ML predictions.

---

## 🔄 ETL or ELT? — It's a Hybrid: **EtLT**

The project follows a **hybrid EtLT** pattern (a common real-world approach):

| Step | Pattern | Why |
|------|---------|-----|
| `kaggle_ingest.py` | **ETL** (light-T before load) | Column renaming, schema defaults, and FK validation are applied *before* the data reaches PostgreSQL so only clean, conforming rows land in the DB |
| `transform.py` + `model.py` | **ELT** (load first, transform in-DB) | Raw relational data already lives in PostgreSQL — transformations are expressed as SQL JOINs and Pandas aggregations *after* the load |
| `dw_load.py` | **ELT** (build DW from loaded data) | Reads from the already-loaded PostgreSQL tables and transform CSV outputs to populate a DuckDB columnar star-schema warehouse |

> **Summary:** The ingest phase does a small amount of column-mapping ETL to enforce the pipeline schema. Everything after that — KPI aggregation, ML modelling, and DW loading — is pure **ELT**: load raw data first, transform inside the system.

---

## 🔄 The Big Picture

Think of the pipeline like an assembly line. Each stage does one job and passes its output to the next.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  📥 INGEST  │───▶│  🔧 TRANSFORM│──┐ │  📊 REPORT  │
│             │    │             │  │ │             │
│ Download &  │    │ Compute     │  ├▶│  🏛️ DW LOAD ├──▶│ Excel │
│ load data   │    │ KPIs & stats│  │ │             │    │workbook│
│ into DB     │    │ to CSVs     │  │ │ DuckDB      │    └────────┘
└──────┬──────┘    └─────────────┘  │ │ star-schema │
       │                            │ └──────▲──────┘
       │           ┌─────────────┐  │        │
       └──────────▶│  🤖 MODEL   │──┘        │
                   │             │           │
                   │ Predict     ├───────────┘
                   │ high-cost   │
                   │ members     │
                   └─────────────┘
```

*Transform and Model run in parallel (both read from PostgreSQL). DW Load waits for both before building the warehouse. Report is generated last.*

---

## 📦 What Each Stage Does

| Stage | File | What it does | Output |
|-------|------|-------------|--------|
| 📥 **Ingest** | `kaggle_ingest.py` + `load.py` | Downloads dataset from Kaggle, maps columns, loads into DB | 3 DB tables |
| 🔧 **Transform** | `transform.py` | Joins tables, computes KPIs, trends, loss ratios | 5 CSV files |
| 🤖 **Model** | `model.py` | Trains logistic regression to flag high-cost members | `model_metrics.txt` |
| 🏛️ **DW Load** | `dw_load.py` | Builds a DuckDB columnar star-schema warehouse (dims + fact + summaries) | `insurance_dw.duckdb` |
| 📊 **Report** | `report.py` | Reads all outputs, assembles 6-sheet Excel workbook | `insurance_summary.xlsx` |

> 💡 **SAS users:** Ingest = `PROC IMPORT`, Transform = `PROC MEANS/SQL`, Model = `PROC LOGISTIC`, DW Load = `PROC DATASETS` + summary tables, Report = `ODS Excel`

---

## 🗄️ Database Schema

Data lives in a PostgreSQL schema called `insurance`. Think of it as a **star schema** — claims are at the centre, and member/provider tables describe who submitted them.

```
                    ┌──────────────┐
                    │   👤 member  │
                    │  (who)       │
                    └──────┬───────┘
                           │
    ┌──────────────┐        │        ┌──────────────────────────┐
    │  🏥 provider │────────┼───────▶│       💊 claim           │
    │  (where)     │        │        │  (what was billed/paid)  │
    └──────────────┘        │        └──────────────────────────┘
```

| Table | What it holds |
|-------|--------------|
| `member` | Who — patient age, gender, region, coverage dates |
| `provider` | Where — doctor/hospital specialty, network status |
| `claim` | What — billed amount, paid amount, diagnosis code, service date |

**Pipeline outputs** (CSVs written by `transform.py`):

| File | Answers the question… |
|------|----------------------|
| `kpis.csv` | What are the key claim metrics by age/region/network? |
| `monthly.csv` | How do claim counts and costs change month by month? |
| `loss_ratio.csv` | What % of billed amounts are actually being paid? |
| `network_summary.csv` | Are members using in-network or out-of-network providers? |
| `diagnosis_summary.csv` | Which diagnosis codes drive the most cost? |

Full DDL: [`src/sql/ddl_create_tables.sql`](../src/sql/ddl_create_tables.sql)

---

## 🏛️ DuckDB Data Warehouse (Star Schema)

`dw_load.py` builds a columnar **star-schema warehouse** in `outputs/insurance_dw.duckdb`:

| Table | Type | Source |
|-------|------|--------|
| `dim_member` | Dimension | PostgreSQL `insurance.member` (+ derived `age_band`) |
| `dim_provider` | Dimension | PostgreSQL `insurance.provider` |
| `dim_date` | Dimension | Generated calendar spine (2010 → next year) |
| `fact_claims` | Fact | PostgreSQL `insurance.claim` |
| `summary_kpis` | Summary | `outputs/kpis.csv` |
| `summary_monthly` | Summary | `outputs/monthly.csv` |
| `summary_loss_ratio` | Summary | `outputs/loss_ratio.csv` |
| `summary_network` | Summary | `outputs/network_summary.csv` |

Full DW DDL: [`src/sql/ddl_dw.sql`](../src/sql/ddl_dw.sql)

---

## 🧩 Design Principles (Why it's built this way)

| Principle | What it means in practice |
|-----------|--------------------------|
| **One job per stage** | Each stage is independently runnable and testable — fix one without touching others |
| **Idempotent ingest** | Re-running ingest always produces the same result — no duplicate data |
| **Config-driven schema mapping** | `config/kaggle.yaml` maps Kaggle column names → pipeline schema, so swapping datasets only requires a config change |
| **Atomic DB writes** | All 3 tables are written in one transaction — if anything fails, nothing is saved (no partial data) |
| **Safe credentials** | Passwords and API keys are never written to logs |
| **Rich outputs** | 5 separate CSVs so any downstream tool can consume just what it needs |
| **Columnar DW** | DuckDB warehouse enables fast analytical queries on the full dataset without a heavy OLAP stack |
