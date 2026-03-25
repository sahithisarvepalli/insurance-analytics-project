# Architecture

## Pipeline

The pipeline is a linear, stage-gated ETL + ML workflow. Each stage has a single responsibility and hands off its output (files or database tables) to the next stage. Stages can be run independently or sequentially end-to-end.

```
  ┌──────────────────────┐
  │  Data Generation     │  Produces reproducible synthetic datasets
  │  (members/providers/ │  representing the insurance domain entities
  │   claims)            │
  └──────────┬───────────┘
             │ flat files (CSV)
             ▼
  ┌──────────────────────┐
  │  Load / Ingest       │  Validates, normalises, and persists
  │                      │  all entities atomically into the database
  └──────────┬───────────┘
             │ relational tables
             ▼
  ┌──────────────────────┐
  │  Transform / KPIs    │  Joins entities, derives business metrics
  │                      │  (age bands, network status, loss ratios),
  │                      │  and writes aggregated summaries
  └──────────┬───────────┘
             │ aggregated outputs
             ▼
  ┌──────────────────────┐
  │  ML Modelling        │  Builds a binary classification model to
  │                      │  identify high-cost members; persists metrics
  └──────────┬───────────┘
             │ model metrics
             ▼
  ┌──────────────────────┐
  │  Reporting           │  Consolidates KPIs, trends, and model results
  │                      │  into a multi-sheet workbook for stakeholders
  └──────────────────────┘
```

**Alternate ingest path** — data can bypass the CSV stage and be seeded directly into the database from the generation layer, useful for CI and rapid iteration.

---

## SAS Equivalents

This project intentionally mirrors SAS workflows in Python. The table below maps each pipeline stage to its SAS counterpart for practitioners transitioning from a SAS/DB2 background.

| Pipeline Stage | SAS Equivalent |
|----------------|---------------|
| Synthetic data generation | `PROC SURVEYSELECT`, `PROC SQL` with `RAND()` |
| Load / Ingest | `PROC IMPORT`, `LIBNAME` engine |
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
| **Claims Enhanced** | Enriched claims (derived layer) | Calculated fields added during transformation (age, age band, etc.) |
| **KPI Summary** | Aggregated business metrics | Claim frequency, paid totals, averages — grouped by age band, region, network status |
| **Model Predictions** | Scored output | High-cost probability and flag per member |

Full DDL: [`sql/ddl_create_tables.sql`](../sql/ddl_create_tables.sql)

---

## Component Responsibilities

| Component | Role in Architecture |
|-----------|---------------------|
| **Data Generation** | Produces statistically representative synthetic data for all three core entities; primary keys must be unique |
| **Configuration / Connection** | Resolves database credentials from environment variables or a config file; credentials must never appear in logs |
| **Ingest (CSV path)** | Normalises date representations across tool versions before writing; all entity writes are a single all-or-nothing transaction |
| **Ingest (direct seed path)** | Generates and persists data in one step without a CSV intermediate; same atomicity guarantee as the CSV path |
| **Transform** | Joins the three core entities; derives age and age-band from date of birth; computes claim frequency, paid totals, and monthly trends |
| **ML Model** | Labels the top-decile of total paid amount as high-cost; scales continuous features before encoding categoricals; applies class-weight correction for the resulting label imbalance |
| **Report** | Reads pipeline outputs and assembles them into a structured Excel workbook |

---

## Key Design Principles

**Single responsibility per stage** — each pipeline stage does exactly one thing. This makes stages independently testable and replaceable without touching adjacent stages.

**Atomic persistence** — the ingest stage treats the full set of entity tables as one logical unit. A failure in any single table write rolls back all writes in that batch, preventing partial / inconsistent state in the database. This is the Python equivalent of wrapping multiple SAS `PROC APPEND` calls inside a single database transaction.

**Reproducible data generation** — synthetic data is produced from a seeded random number generator. Given the same seed and row counts, the output is byte-for-byte identical across environments, which is critical for deterministic CI runs and reproducible ML experiments.

**Entity key integrity** — primary keys in generated data must be unique. Key generation uses sampling without replacement rather than random draw-with-replacement to guarantee this at the generation layer, before any database constraint is encountered.

**Correct ML preprocessing** — features with different scales must be normalised before entering a linear model. Numeric features (e.g. age) are standardised; categorical features are one-hot encoded. The label is highly imbalanced (top-decile threshold → ~10 % positive), so class weighting is applied during training to prevent the model from collapsing to the majority class.

**Credential safety** — database passwords must never appear in log output. The connection layer redacts credentials from any logged connection string before writing to any output.

**Date portability** — date serialisation formats can vary across tool versions. The ingest layer detects and normalises alternative representations (e.g. epoch-nanosecond integers written by older tooling) to a canonical date type before the database write.
