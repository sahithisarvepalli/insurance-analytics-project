# ⚙️ Orchestration

> **Concept:** *Orchestration* means automatically scheduling and running your pipeline on a timer — so it runs every day without you manually typing commands. This project has two independent ways to do this.

---

## 🔀 Two Ways to Run the Pipeline

```
┌────────────────────────────────┐   ┌────────────────────────────────┐
│         🌀 Airflow             │   │      ☁️ GitHub Actions          │
│   (runs on YOUR machine)       │   │   (runs on GitHub's cloud)      │
│                                │   │                                 │
│  • Visual UI at localhost:8080 │   │  • Triggered by schedule/push   │
│  • See task logs in browser    │   │  • No extra setup needed        │
│  • Re-run failed tasks easily  │   │  • Outputs saved as artifacts   │
│  • Self-hosted, free           │   │  • Free (public repos)          │
└────────────────────────────────┘   └────────────────────────────────┘
         ↓ local Postgres                    ↓ throwaway Postgres
         (different DBs — no conflict)
```

> 💡 They are completely independent. You can use one, both, or neither.

---

## 🌀 Airflow — Local Setup

Apache Airflow is **free and open-source** (no sign-up required).

### Quick Start

```bash
# 1. Make sure the dev container is running (creates the shared Docker network)

# 2. From a HOST terminal (not the dev container), start Airflow:
cd airflow
docker compose -f docker-compose-airflow.yml up -d

# 3. Watch startup (wait for "Listening at: http://0.0.0.0:8080")
docker compose -f docker-compose-airflow.yml logs -f airflow-webserver

# 4. Open http://localhost:8080
#    Username: admin  |  Password: admin
```

### Running the Pipeline

```
① Click "insurance_analytics_pipeline" in the DAG list
② Click ▶ Trigger DAG (top right)
③ Watch tasks go green:
   kaggle_ingest → transform → ml_model → generate_excel_report
④ Click any task → Log tab to see output
```

### Stop Airflow

```bash
cd airflow
docker compose -f docker-compose-airflow.yml down
```

### Airflow UI at a Glance

| View | What you see |
|------|-------------|
| **DAGs list** | All DAGs, schedule, last run status |
| **Graph** | Visual dependency graph of tasks |
| **Grid** | History of all runs (🟢 success / 🔴 fail) |
| **Task → Log** | Full stdout/stderr for any task |

---

## ☁️ GitHub Actions — Cloud Schedule

The file `.github/workflows/scheduled-pipeline.yml` runs the pipeline automatically on GitHub's servers **every day at 06:30 UTC**.

### One-time Setup

1. Go to **GitHub → your repo → Settings → Secrets and variables → Actions**
2. Add two secrets:

| Secret | Where to get it |
|--------|----------------|
| `KAGGLE_USERNAME` | Your Kaggle username |
| `KAGGLE_KEY` | Kaggle → Account → API → Create New Token |

3. Go to **Actions tab** → click **"Scheduled Pipeline"** → **Run workflow** (first manual trigger)

### Downloading Outputs

After each run: **workflow run page → Artifacts** → download `pipeline-outputs-<run_number>`

Contains: `kpis.csv`, `monthly.csv`, `loss_ratio.csv`, `network_summary.csv`, `diagnosis_summary.csv`, `model_metrics.txt`, `insurance_summary.xlsx`

---

## 🛠️ Troubleshooting

<details>
<summary>❌ Port 8080 already in use</summary>

```bash
lsof -i :8080   # find what's using it
# Then change ports in docker-compose-airflow.yml: "9090:8080"
```
</details>

<details>
<summary>❌ DAG not showing in Airflow UI</summary>

```bash
# Check for Python errors in the DAG file
docker exec -it airflow-airflow-scheduler-1 python /opt/airflow/dags/insurance_pipeline_dag.py
# Force rescan
docker exec -it airflow-airflow-scheduler-1 airflow dags reserialize
```
</details>

<details>
<summary>❌ "relation insurance.member does not exist"</summary>

The analytics DB needs its schema set up first:

```bash
# Inside the dev container terminal
psql "$DATABASE_URL" -f src/sql/ddl_create_tables.sql
```
</details>

<details>
<summary>🕐 Change the schedule</summary>

Edit `AIRFLOW_PIPELINE_SCHEDULE` in `airflow/docker-compose-airflow.yml`:

| Cron | Meaning |
|------|---------|
| `0 6 * * *` | Daily at 06:00 UTC |
| `0 6 * * 1-5` | Weekdays only |
| `0 */6 * * *` | Every 6 hours |

Restart: `docker compose -f docker-compose-airflow.yml restart airflow-scheduler`
</details>
