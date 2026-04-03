# Architecture

## Pipeline

The pipeline is a linear, stage-gated ETL + ML workflow. Each stage has a single responsibility and hands off its output (files or database tables) to the next stage. Stages can be run independently or sequentially end-to-end.

```
  ┌──────────────────────┐
  │  Kaggle Ingest       │  Downloads a public insurance dataset from
  │  (kaggle_ingest.py   │  Kaggle, maps columns to the pipeline schema,
  │   + load.py)         │  and persists all entities atomically into the DB
  └──────────┬───────────┘
             │ relational tables
             ▼
  ┌──────────────────────┐
  │  Transform / KPIs    │  Joins entities, derives business metrics
  │                      │  (age bands, network status, loss ratios),
  │                      │  and writes aggregated summaries
  └──────────┬───────────┘
             │ aggregated outputs (5 CSVs)
             ▼
  ┌──────────────────────┐
  │  ML Modelling        │  Builds a binary classification model to
  │                      │  identify high-cost members; persists metrics
  └──────────┬───────────┘
             │ model metrics
             ▼
  ┌──────────────────────┐
  │  Reporting           │  Consolidates KPIs, trends, loss ratios,
  │                      │  network utilization, diagnosis summary,
  │                      │  and model results into a multi-sheet workbook
  └──────────────────────┘
```

---

## SAS Equivalents

This project intentionally mirrors SAS workflows in Python. The table below maps each pipeline stage to its SAS counterpart for practitioners transitioning from a SAS/DB2 background.

| Pipeline Stage | SAS Equivalent |
|----------------|---------------|
| Kaggle data ingest | `PROC IMPORT`, `LIBNAME` engine |
| KPI aggregation | `PROC MEANS`, `PROC SQL GROUP BY` |
| ML classification model | `PROC LOGISTIC` |
| Excel report | `ODS Excel` |

---

## Database Schema

The relational model uses a single schema (`insurance`) with a classic star-like structure — claims at the centre, members and providers as dimension-style tables.

```
  member ──────┐
               ├──── claim ──── claims_enhanced (derived)
  provider ────┘         │
                         └──── kpi_summary (aggregated)
                               model_predictions (scored)
```

| Table | Role | Key Business Attributes |
|-------|------|------------------------|
| **Member** | Enrollee / patient demographics | Date of birth, gender, region, coverage effective and termination dates |
| **Provider** | Healthcare provider registry | Specialty, network participation flag, region |
| **Claim** | Raw submitted claims | Service date, billed / allowed / paid amounts, diagnosis code, procedure code, place of service |
| **KPI Summary** (`outputs/kpis.csv`) | Aggregated business metrics | Claim frequency, paid totals, averages — grouped by age band, region, network status |
| **Monthly** (`outputs/monthly.csv`) | Monthly trend summary | Claim counts and paid totals by calendar month, region, and network status |
| **Loss Ratio** (`outputs/loss_ratio.csv`) | Financial ratios | Paid vs billed vs allowed amounts with loss ratio and allowed ratio percentages |
| **Network Utilization** (`outputs/network_summary.csv`) | In/out-of-network breakdown | Claim counts, costs, and utilization percentages by network status |
| **Diagnosis Summary** (`outputs/diagnosis_summary.csv`) | Diagnosis code analysis | Claims and costs ranked by ICD diagnosis code |
| **Model Predictions** (`outputs/model_metrics.txt`) | Scored output | Accuracy metric from the high-cost logistic regression model |

Full DDL: [`src/sql/ddl_create_tables.sql`](../src/sql/ddl_create_tables.sql)

---

## Component Responsibilities

| Component | Role in Architecture |
|-----------|---------------------|
| **Kaggle Ingest** | Downloads a public insurance dataset from Kaggle via the Kaggle API; maps source column names to the pipeline schema; injects schema-level defaults for required columns absent in the source file; auto-derives member and provider tables when not explicitly provided |
| **Configuration / Connection** | Resolves database credentials from environment variables or a config file; credentials must never appear in logs |
| **Load** | Truncates and reloads the three core entity tables in a single atomic transaction; idempotent — safe to re-run |
| **Transform** | Joins the three core entities; derives age and age-band from date of birth; computes claim frequency, paid totals, monthly trends, loss ratios, network utilization, and diagnosis-level summaries |
| **ML Model** | Labels the top-decile of total paid amount as high-cost; scales continuous features before encoding categoricals; applies class-weight correction for the resulting label imbalance |
| **Report** | Reads all pipeline outputs (kpis.csv, monthly.csv, loss_ratio.csv, network_summary.csv, diagnosis_summary.csv, model_metrics.txt) and assembles them into a structured six-sheet Excel workbook |

---

## Key Design Principles

**Single responsibility per stage** — each pipeline stage does exactly one thing. This makes stages independently testable and replaceable without touching adjacent stages.

**Atomic persistence** — the ingest stage treats the full set of entity tables as one logical unit. It truncates and reloads all three tables inside a single database transaction. A failure in any single table write rolls back all writes in that batch, preventing partial / inconsistent state in the database. This is the Python equivalent of wrapping multiple SAS `PROC APPEND` calls inside a single database transaction.

**Schema-flexible Kaggle ingest** — real-world public datasets rarely match an internal schema out of the box. The Kaggle ingest layer uses a declarative YAML config (`config/kaggle.yaml`) to rename columns and inject defaults for missing fields, decoupling the pipeline schema from the source dataset structure. Switching to a different Kaggle dataset requires only a config change.

**Idempotent ingest** — running the load step multiple times produces the same result. The loader truncates existing data before inserting, so re-running the pipeline does not accumulate duplicates.

**Correct ML preprocessing** — features with different scales must be normalised before entering a linear model. Numeric features (e.g. age) are standardised; categorical features are one-hot encoded. The label is highly imbalanced (top-decile threshold → ~10 % positive), so class weighting is applied during training to prevent the model from collapsing to the majority class.

**Credential safety** — database passwords and Kaggle API keys must never appear in log output. The connection layer redacts credentials from any logged connection string before writing to any output.

**Rich transform outputs** — the transform stage produces five separate CSV files (KPI summary, monthly trends, loss ratios, network utilization, and diagnosis summary) so that each can be consumed independently by reporting tools, dashboards, or downstream pipelines.
