# Orchestration Guide — Airflow + GitHub Actions

This guide walks you through setting up **Apache Airflow** and a **GitHub Actions
scheduled workflow** for the Insurance Analytics pipeline.  Both run in parallel
— Airflow for local / server orchestration, GitHub Actions for cloud-based CI/CD.

---

## Table of Contents

1. [Do I need an Airflow account / subscription?](#1-do-i-need-an-airflow-account--subscription)
2. [Architecture overview](#2-architecture-overview)
3. [Airflow setup — local / dev container](#3-airflow-setup--local--dev-container)
4. [Airflow UI walkthrough](#4-airflow-ui-walkthrough)
5. [GitHub Actions scheduled workflow](#5-github-actions-scheduled-workflow)
6. [Credentials & secrets reference](#6-credentials--secrets-reference)
7. [FAQ & troubleshooting](#7-faq--troubleshooting)

---

## 1. Do I need an Airflow account / subscription?

**No.**  Apache Airflow is **100 % free and open-source** (Apache-2.0 licence).
There is no sign-up, no licence key, and no subscription.

| Option | Cost | What you get |
|--------|------|--------------|
| **Self-hosted (this guide)** | $0 | Full Airflow running via Docker on your laptop or a VM |
| **Managed cloud services** (optional, for later) | Paid | AWS MWAA, GCP Cloud Composer, Astronomer — they host Airflow for you |

For learning and this project, **self-hosted via Docker Compose** is all you need.

---

## 2. Architecture overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Your laptop / VM                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Dev Container  (docker-compose.yml)                 │    │
│  │   app  ←──── your code + Python                      │    │
│  │   db   ←──── PostgreSQL 15  (insurdb)                │    │
│  └──────────────────────────────────────────────────────┘    │
│                           │                                  │
│              insurance-network (shared Docker network)       │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Airflow stack  (docker-compose-airflow.yml)         │    │
│  │   airflow-postgres  ←── metadata DB (separate)       │    │
│  │   airflow-webserver ←── UI on http://localhost:8080   │    │
│  │   airflow-scheduler ←── picks up & runs DAG tasks    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions (cloud)                                      │
│   scheduled-pipeline.yml → runs daily at 06:30 UTC           │
│   ci-postgres.yml        → runs on push / PR (existing)      │
└──────────────────────────────────────────────────────────────┘
```

Key points:
- Airflow gets its **own Postgres** (`airflow-postgres`) for internal metadata.
  It connects to your **existing** analytics DB (`db`) to run pipeline tasks.
- GitHub Actions runs **independently** — it spins up a fresh Postgres each run.
  No conflict with Airflow.

---

## 3. Airflow setup — local / dev container

### Prerequisites

| Tool | Check | Install |
|------|-------|---------|
| Docker | `docker --version` | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| Docker Compose v2 | `docker compose version` | Bundled with Docker Desktop |

No other accounts, keys, or sign-ups required.

### Step-by-step

#### A. Make sure the dev container is running

Your dev container creates a Docker network called `insurance-network`.
Airflow services join this network so they can reach the `db` (Postgres)
service defined in `.devcontainer/docker-compose.yml`.

```bash
# If not already inside the dev container, open VS Code and
# Ctrl+Shift+P → "Dev Containers: Reopen in Container"
```

#### B. Create the shared Docker network (one-time)

From a **host terminal** (not the dev container terminal):

```bash
docker network create insurance-network 2>/dev/null || true
```

> The dev container's `docker-compose.yml` already defines this network.
> If the dev container is running, the network already exists — the
> command above is a safe no-op in that case.

#### C. Start Airflow

From a **host terminal**, in the repo root:

```bash
cd airflow
docker compose -f docker-compose-airflow.yml up -d
```

First run will:
1. Pull the `apache/airflow:2.10.4-python3.11` image (~1.5 GB).
2. Start `airflow-postgres` (Airflow metadata DB).
3. Run `airflow-init` — creates tables and an **admin** user.
4. Start the **webserver** (port 8080) and **scheduler**.

Watch startup progress:

```bash
docker compose -f docker-compose-airflow.yml logs -f airflow-init
# Wait until you see "airflow-init exited with code 0"

docker compose -f docker-compose-airflow.yml logs -f airflow-webserver
# Wait until you see "Listening at: http://0.0.0.0:8080"
```

#### D. Log in to the Airflow UI

Open **http://localhost:8080** in your browser.

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

You'll see the DAG **`insurance_analytics_pipeline`** listed.

#### E. Trigger a manual run

1. Click the DAG name to open it.
2. Click the **▶ Trigger DAG** button (top right).
3. Watch the tasks go green one by one:
   `generate_synthetic_data → load_csv_to_postgres → run_transform_kpis + run_ml_model → generate_excel_report`
4. Click any task → **Log** to see stdout/stderr.

#### F. Stop Airflow

```bash
cd airflow
docker compose -f docker-compose-airflow.yml down
# Add -v to also remove the metadata DB volume (clean reset)
```

---

## 4. Airflow UI walkthrough

| View | What you see |
|------|--------------|
| **DAGs list** | All DAGs, their schedule, last run status, next run time |
| **Graph** | Visual dependency graph of your 5 tasks |
| **Grid** | History of all runs, colour-coded (green = success, red = fail) |
| **Task Instance → Log** | Full stdout/stderr for a specific task execution |
| **Admin → Connections** | Database connections (not needed here — we use env vars) |
| **Admin → Variables** | Key-value config you can reference in DAGs |

### Common actions

| Goal | How |
|------|-----|
| Pause the schedule | Toggle the switch next to the DAG name |
| Re-run a failed task | Click the failed task → **Clear** → confirm |
| Backfill past dates | `docker exec airflow-scheduler airflow dags backfill -s 2025-01-01 -e 2025-01-31 insurance_analytics_pipeline` |
| Change schedule | Edit `AIRFLOW_PIPELINE_SCHEDULE` env var in `docker-compose-airflow.yml` and restart |

---

## 5. GitHub Actions scheduled workflow

The file `.github/workflows/scheduled-pipeline.yml` runs the **same pipeline**
in GitHub's cloud. It is completely independent of Airflow.

### How it works

- **Trigger**: cron `30 6 * * *` (daily 06:30 UTC) **+ manual** via the
  "Run workflow" button on the Actions tab.
- **Environment**: spins up a fresh `postgres:15` service container, installs
  deps, runs all 5 pipeline steps, and uploads outputs as a build artifact.
- **No secrets needed**: the workflow uses the same public Postgres credentials
  already in the repo — everything runs inside the ephemeral GitHub runner.

### How to enable / configure

1. **Push** the new workflow file to `main`:
   ```bash
   git add .github/workflows/scheduled-pipeline.yml
   git commit -m "feat: add scheduled pipeline workflow"
   git push
   ```
2. Go to **GitHub → your repo → Actions** tab.
   You'll see "Scheduled Pipeline" listed.
3. Click **Run workflow** to trigger it manually the first time.
4. Subsequent runs happen automatically at 06:30 UTC daily.

### Downloading outputs

After each run, go to the workflow run page → **Artifacts** section →
download `pipeline-outputs-<run_number>`.  It contains:
- `kpis.csv`
- `monthly.csv`
- `model_metrics.txt`
- `insurance_summary.xlsx`

### Does it conflict with Airflow?

**No.** They are fully independent:
- Airflow runs on your local machine / server, writes to your local Postgres.
- GitHub Actions runs on GitHub's cloud runners with a throwaway Postgres.
- Even if both run at the same time, they target different databases.

---

## 6. Credentials & secrets reference

### What credentials exist in this project?

| Credential | Where used | Value | Secret? |
|------------|-----------|-------|---------|
| Analytics Postgres | `DATABASE_URL` | `postgres:postgres@db:5432/insurdb` | Dev-only — fine to hardcode |
| Airflow Postgres | `docker-compose-airflow.yml` | `airflow:airflow@airflow-postgres:5432/airflow` | Airflow-internal — no sensitive data |
| Airflow UI login | browser | `admin` / `admin` | Local dev only |
| `SONAR_TOKEN` | GitHub Actions CI | Stored in repo Settings → Secrets | **Yes — never commit** |
| `CODECOV_TOKEN` | GitHub Actions CI | Stored in repo Settings → Secrets | **Yes — never commit** |

### Do I need to add any new secrets for the scheduled pipeline?

**No.** The scheduled pipeline workflow uses only the Postgres credentials
already in the workflow file.  No external API tokens are required.

### For production deployment (later)

If you ever deploy Airflow to a real server or managed service:
1. Change all `postgres`/`admin` passwords to strong random values.
2. Store `DATABASE_URL` in Airflow **Connections** (Admin → Connections), not
   in environment variables.
3. Use Airflow **Secrets Backend** (Vault, AWS Secrets Manager, GCP Secret
   Manager) for credential management.
4. Enable Airflow RBAC and disable the default `admin` user.

---

## 7. FAQ & troubleshooting

### Q: "Port 8080 is already in use"

```bash
# Find what's using it
lsof -i :8080
# Change the port in docker-compose-airflow.yml:
#   ports: ["9090:8080"]
```

### Q: "DAG not showing up in the UI"

```bash
# Check for Python syntax errors in the DAG file
docker exec -it airflow-airflow-scheduler-1 python /opt/airflow/dags/insurance_pipeline_dag.py

# Force a DAG file rescan
docker exec -it airflow-airflow-scheduler-1 airflow dags reserialize
```

### Q: "Task fails with 'relation insurance.member does not exist'"

The analytics Postgres (`db`) needs the schema initialised first.  Make sure
the dev container ran the schema setup:

```bash
# Inside the dev container terminal
psql "$DATABASE_URL" -f sql/ddl_create_tables.sql
```

### Q: "How do I change the schedule?"

Edit `AIRFLOW_PIPELINE_SCHEDULE` in `airflow/docker-compose-airflow.yml`:

| Cron expression | Meaning |
|----------------|---------|
| `0 6 * * *` | Every day at 06:00 UTC |
| `0 6 * * 1-5` | Weekdays only at 06:00 |
| `0 */6 * * *` | Every 6 hours |
| `0 6 1 * *` | First day of every month |

Then restart: `docker compose -f docker-compose-airflow.yml restart airflow-scheduler`

### Q: "How do I view task logs?"

- **Airflow UI**: click any task in the Grid/Graph view → **Log** tab.
- **Terminal**: `docker compose -f docker-compose-airflow.yml logs airflow-scheduler`
- **Files**: logs are persisted in `airflow/logs/` on your host machine.

### Q: "Can I use PythonOperator instead of BashOperator?"

Yes.  Replace each `BashOperator` with a `PythonOperator` that imports and
calls the function directly:

```python
from airflow.operators.python import PythonOperator
from src.transform import run_transform

transform = PythonOperator(
    task_id="run_transform_kpis",
    python_callable=run_transform,
)
```

This is cleaner but requires the Airflow worker to have your `src` package
installed.  The `BashOperator` approach works out of the box without any
package installation inside the Airflow container beyond pip dependencies.
