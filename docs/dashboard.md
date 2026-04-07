# Reports Dashboard — Architecture Guide

This document explains how the insurance analytics pipeline publishes interactive
reports on GitHub (current implementation), how to run the full local dashboard
against millions of rows of data, and what an industry-standard visualization
stack would look like as a future enhancement.

---

## Current Implementation — GitHub-Native Dashboard

### How it works

After every successful `client-analytics` workflow run the pipeline produces
**three complementary views** of the same data, all free and built into GitHub:

| View                           | Where to find it                                                 | Interactivity                                             |
| ------------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------- |
| **GitHub Actions Job Summary** | `Actions → <run> → Summary tab`                                  | Tables, emoji KPI cards — no download needed              |
| **Interactive HTML Dashboard** | Download `report-<client>-run*` artifact → open `dashboard.html` | Full Plotly charts — pan, zoom, hover, filter             |
| **GitHub Pages site**          | `https://<owner>.github.io/<repo>/` (after Pages is enabled)     | Persistent URL, same Plotly charts, index page per client |

### Architecture diagram

```
client-analytics.yml
│
├─ analytics (matrix: client_a, client_b)
│   ├─ src/load.py          → Postgres
│   ├─ src/transform.py     → outputs/<client>/{kpis,monthly,...}.csv
│   ├─ src/model.py         → outputs/<client>/model_metrics.txt
│   ├─ src/dw_load.py       → outputs/<client>/insurance_dw.duckdb
│   ├─ src/report.py        → outputs/<client>/insurance_summary.xlsx
│   ├─ src/generate_html_report.py → outputs/<client>/dashboard.html  ← NEW
│   ├─ Write Job Summary    → GitHub Actions run summary page          ← NEW
│   └─ Upload artifact      → GitHub Artifacts (30-day retention)
│
└─ publish-dashboard (after analytics)                                  ← NEW
    ├─ Download client_a + client_b artifacts
    ├─ Build index.html linking to all client dashboards
    └─ Deploy to GitHub Pages → https://<owner>.github.io/<repo>/
```

### Technology choices

| Component          | Technology                                         | Why                                                          |
| ------------------ | -------------------------------------------------- | ------------------------------------------------------------ |
| Interactive charts | [Plotly](https://plotly.com/python/) (open-source) | Self-contained HTML; no server; pan/zoom/hover built-in      |
| Job Summary tables | GitHub Actions `GITHUB_STEP_SUMMARY`               | Zero setup; rendered in the Actions UI                       |
| Hosting            | GitHub Pages (free)                                | Permanent URL; no external service; CI deploys automatically |
| Data               | Pipeline CSVs (`outputs/<client>/*.csv`)           | Reuses existing transform outputs; no extra DB query         |

### Enabling GitHub Pages (one-time setup)

GitHub Pages deployment is built into the workflow but requires a one-time
repository setting:

1. Go to **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Save. The next workflow run will publish the dashboard automatically.

The published URL will be:

```
https://<owner>.github.io/<repo>/
```

Per-client dashboards are at:

```
https://<owner>.github.io/<repo>/client_a/dashboard.html
https://<owner>.github.io/<repo>/client_b/dashboard.html
```

### Viewing without GitHub Pages

If Pages is not enabled, each workflow run still produces downloadable artifacts:

1. Go to **Actions → Client Analytics Pipeline → <run>**.
2. Scroll to **Artifacts** and download `report-<client>-run<N>`.
3. Unzip and open `dashboard.html` in any browser.

The HTML file is fully self-contained — the Plotly JS bundle is embedded
inline from the installed package at generation time, so no internet connection
is needed to view the charts.

---

## 🖥️ Running the Full Dashboard Locally (Millions of Rows)

The CI pipeline uses **20 synthetic seed rows** so tests finish in seconds.
The GitHub Pages site reflects those same seed rows.

To see real analytics on your full Kaggle dataset (hundreds of thousands to
millions of claims), run the pipeline entirely on your local machine.

### Prerequisites

| Requirement                            | Notes                                       |
| -------------------------------------- | ------------------------------------------- |
| Dev Container running                  | Provides PostgreSQL, Python, all deps       |
| Kaggle credentials set                 | See [Setup Guide](setup.md)                 |
| `requirements-dashboard.txt` installed | `pip install -r requirements-dashboard.txt` |

---

### Option 1 — One-command local run (recommended)

```bash
# 1. Load full Kaggle dataset into PostgreSQL  (~2-5 min for large datasets)
make kaggle-load

# 2. Run the full pipeline then open the dashboard
make pipeline-local
```

`make pipeline-local` runs `transform → model → dw_load → dashboard` in
sequence and prints the path to the generated HTML file.

To view it in a browser — **recommended for dev containers**: start a local
HTTP server and VS Code will automatically show a clickable **"Open in Browser"**
link in the terminal and in the **Ports** panel:

```bash
make serve-dashboard
# → http://localhost:8000/dashboard.html
# VS Code detects port 8000 and shows "Open in Browser" automatically
```

Press **Ctrl+C** to stop the server when done.

Alternatively, if you are running outside a dev container:

```bash
make open-dashboard   # generates + opens in default OS browser
```

Or just open the file directly — no server needed:

```
outputs/dashboard.html
```

---

### Option 2 — Step-by-step (for debugging or partial runs)

```bash
# Step 1 — Load data (only needed once, or after schema reset)
make kaggle-load

# Step 2 — Compute KPIs and CSV aggregations
python -m src.transform --output-dir outputs

# Step 3 — Train the high-cost member model
python -m src.model --output-dir outputs

# Step 4 — Build the DuckDB star-schema warehouse
python -m src.dw_load \
    --output-dir outputs \
    --dw-path outputs/insurance_dw.duckdb

# Step 5 — Generate the interactive HTML dashboard
python -m src.generate_html_report \
    --output-dir outputs \
    --client-name "My Full Dataset" \
    --out outputs/dashboard.html

# Step 6 — Open in browser (Linux)
xdg-open outputs/dashboard.html
# macOS:
# open outputs/dashboard.html
```

---

### Option 3 — Client-specific data

If your data lives in `config/clients/` (e.g. `client_a.yaml`):

```bash
# Load client data
python -m src.load --client-config config/clients/client_a.yaml

# Run the full pipeline for that client
make pipeline-local CLIENT=client_a

# The dashboard is written to:
#   outputs/client_a/dashboard.html
```

---

### Option 4 — Interactive exploration in JupyterLab

For ad-hoc queries and custom charts against the full DuckDB warehouse:

```bash
# Start JupyterLab
make run-jupyterlab
# → opens at http://localhost:8888
```

Open `notebooks/dw_sample_queries.ipynb` — it connects directly to
`outputs/insurance_dw.duckdb` and runs analytical queries against the
star-schema fact and summary tables.

You can write any DuckDB SQL to explore millions of rows with sub-second
response times, e.g.:

```python
import duckdb
con = duckdb.connect("outputs/insurance_dw.duckdb")

# Top diagnosis codes by paid total
con.execute("""
    SELECT diagnosis_code, COUNT(*) AS claims, SUM(paid_amount) AS paid_total
    FROM fact_claims
    GROUP BY 1
    ORDER BY paid_total DESC
    LIMIT 20
""").df()
```

---

### Performance tips for large datasets

| Tip                              | Detail                                                                                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Increase Postgres `work_mem`** | `SET work_mem = '256MB';` speeds up the JOIN in `transform.py`                                                                                                     |
| **Use DuckDB for analytics**     | After the first load, all aggregation queries run against `insurance_dw.duckdb` without touching Postgres — DuckDB is columnar and handles millions of rows easily |
| **Parallel ingest**              | The client-analytics CI workflow processes multiple clients in parallel via a matrix strategy — you can do the same locally with a shell loop                      |
| **Re-run only changed stages**   | Each stage writes its own outputs — skip `kaggle-load` and go straight to `make pipeline-local` if the DB is already loaded                                        |
| **Chunked Kaggle downloads**     | Large Kaggle datasets are written in chunks of 10 000 rows by `load.py` to keep memory usage flat                                                                  |

---

The GitHub Pages approach works well for small teams and free access. As the
platform scales, a dedicated BI stack offers richer features: live queries,
row-level security, scheduled alerts, and multi-source data federation.

### Option A — Apache Superset (recommended open-source BI)

```
DuckDB / PostgreSQL  →  Apache Superset  →  Browser
```

| Feature         | Detail                                                       |
| --------------- | ------------------------------------------------------------ |
| License         | Apache 2.0 — fully free                                      |
| Hosting         | Self-hosted on any cloud VM or Kubernetes                    |
| Connects to     | PostgreSQL, DuckDB, Snowflake, BigQuery, 40+ databases       |
| Charts          | 40+ chart types; drag-and-drop dashboards                    |
| Security        | Row-level security, LDAP/SAML SSO, per-dashboard permissions |
| CI integration  | Superset API can import dashboard JSON from CI artifacts     |
| Effort to adopt | Medium — Docker Compose setup, ~1-2 days initial config      |

Superset can connect directly to the `insurance_dw.duckdb` warehouse produced
by `src/dw_load.py`, providing live ad-hoc exploration on top of the same
star-schema fact tables.

### Option B — Grafana (strong for time-series & operational metrics)

```
PostgreSQL  →  Grafana  →  Browser
```

| Feature         | Detail                                                       |
| --------------- | ------------------------------------------------------------ |
| License         | AGPL 3.0 — free for self-hosted use                          |
| Hosting         | Docker / Grafana Cloud free tier                             |
| Connects to     | PostgreSQL, InfluxDB, Loki, 80+ data sources                 |
| Charts          | Time-series, gauge, heatmap, bar; alerting built-in          |
| CI integration  | Dashboard-as-code via `grafana-cli` + JSON provisioning      |
| Effort to adopt | Low — official Docker image; PostgreSQL plugin pre-installed |

Best choice if the team already operates a Grafana instance for infrastructure
monitoring and wants to add insurance KPIs alongside.

### Option C — Metabase (fastest to adopt)

```
PostgreSQL / DuckDB  →  Metabase  →  Browser
```

| Feature         | Detail                                                |
| --------------- | ----------------------------------------------------- |
| License         | AGPL 3.0 open-source edition — free                   |
| Hosting         | Docker one-liner; Metabase Cloud free tier available  |
| Connects to     | PostgreSQL, DuckDB (via JDBC), BigQuery, many more    |
| Charts          | Point-and-click; SQL questions; dashboards            |
| CI integration  | Metabase API supports programmatic dashboard creation |
| Effort to adopt | Very low — 15-minute setup                            |

Metabase's self-service SQL questions allow business analysts to explore claims
data without writing code.

### Comparison table

|                    | GitHub Pages (current) | Apache Superset    | Grafana               | Metabase           |
| ------------------ | ---------------------- | ------------------ | --------------------- | ------------------ |
| Cost               | Free                   | Free (self-hosted) | Free (self-hosted)    | Free (self-hosted) |
| Setup effort       | Zero                   | Medium             | Low                   | Very low           |
| Live queries       | No (static HTML)       | Yes                | Yes                   | Yes                |
| Row-level security | No                     | Yes                | Yes                   | Yes (Enterprise)   |
| Alerting           | No                     | Yes                | Yes                   | Yes                |
| Embedded charts    | Via iframe             | Via iframe         | Via iframe            | Via iframe         |
| Custom branding    | Full (HTML/CSS)        | Limited            | Limited               | Limited            |
| Offline capable    | Yes (downloaded HTML)  | No                 | No                    | No                 |
| CI/CD integration  | Native (this repo)     | Via API            | Via JSON provisioning | Via API            |

### Recommended migration path

```
Phase 1 (now)     GitHub Pages + Plotly HTML       — zero cost, zero infra
Phase 2 (6 months) Add Metabase on a $5/mo VM       — live queries, self-service SQL
Phase 3 (1 year)  Migrate to Apache Superset        — RBAC, SSO, production BI
Phase 4 (future)  Superset + dbt + Snowflake        — full modern data stack
```

The pipeline's DuckDB warehouse (`insurance_dw.duckdb`) and the PostgreSQL
star-schema tables are already structured for any of these tools — no
re-modelling required.

---

## File reference

| File                                     | Purpose                                                            |
| ---------------------------------------- | ------------------------------------------------------------------ |
| `src/generate_html_report.py`            | Generates the self-contained Plotly HTML dashboard                 |
| `requirements-dashboard.txt`             | Plotly dependency (installed only in the dashboard CI step)        |
| `.github/workflows/client-analytics.yml` | Orchestrates analytics, dashboard generation, and Pages deployment |
| `docs/dashboard.md`                      | This document                                                      |
