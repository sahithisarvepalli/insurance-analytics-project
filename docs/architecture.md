# 🏗️ Architecture

> **Concept:** This project is an end-to-end **data pipeline** — raw insurance data flows through four stages and comes out the other end as business reports and ML predictions.

---

## 🔄 The Big Picture

Think of the pipeline like an assembly line. Each stage does one job and passes its output to the next.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  📥 INGEST  │───▶│  🔧 TRANSFORM│───▶│  🤖 MODEL   │───▶│  📊 REPORT  │
│             │    │             │    │             │    │             │
│ Download &  │    │ Compute     │    │ Predict     │    │ Excel       │
│ load data   │    │ KPIs & stats│    │ high-cost   │    │ workbook    │
│ into DB     │    │ to CSVs     │    │ members     │    │ output      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     ▲                   ▲                  ▲
     │                   │                  │
  Kaggle API          PostgreSQL          CSV files
```

---

## 📦 What Each Stage Does

| Stage | File | What it does | Output |
|-------|------|-------------|--------|
| 📥 **Ingest** | `kaggle_ingest.py` + `load.py` | Downloads dataset from Kaggle, maps columns, loads into DB | 3 DB tables |
| 🔧 **Transform** | `transform.py` | Joins tables, computes KPIs, trends, loss ratios | 5 CSV files |
| 🤖 **Model** | `model.py` | Trains logistic regression to flag high-cost members | `model_metrics.txt` |
| 📊 **Report** | `report.py` | Reads all outputs, assembles 6-sheet Excel workbook | `insurance_summary.xlsx` |

> 💡 **SAS users:** Ingest = `PROC IMPORT`, Transform = `PROC MEANS/SQL`, Model = `PROC LOGISTIC`, Report = `ODS Excel`

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

## 🧩 Design Principles (Why it's built this way)

| Principle | What it means in practice |
|-----------|--------------------------|
| **One job per stage** | Each stage is independently runnable and testable — fix one without touching others |
| **Idempotent ingest** | Re-running ingest always produces the same result — no duplicate data |
| **Config-driven schema mapping** | `config/kaggle.yaml` maps Kaggle column names → pipeline schema, so swapping datasets only requires a config change |
| **Atomic DB writes** | All 3 tables are written in one transaction — if anything fails, nothing is saved (no partial data) |
| **Safe credentials** | Passwords and API keys are never written to logs |
| **Rich outputs** | 5 separate CSVs so any downstream tool can consume just what it needs |
