# 🚀 Setup Guide

> **Concept:** This project needs **Python**, **PostgreSQL** (for storing data), and **Kaggle credentials** (for downloading the dataset). You can run it locally or inside a Docker dev container.

---

## ✅ What You Need

| Tool           | Version | Why                                                        |
| -------------- | ------- | ---------------------------------------------------------- |
| Python         | 3.11+   | Runs all pipeline code                                     |
| PostgreSQL     | 15+     | Stores claims data                                         |
| Docker         | any     | Easiest way to run PostgreSQL (or the whole dev container) |
| Kaggle account | —       | Download the insurance dataset                             |

---

## 🅰️ Option A — Dev Container (Recommended)

> **Best for:** Teams, beginners, zero-config setup. Everything runs automatically inside Docker.

**Prerequisites:** VS Code + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) + Docker Desktop

```
Step 1 → Clone the repo and open it in VS Code
Step 2 → VS Code prompts "Reopen in Container" → click it
            (or Ctrl+Shift+P → "Dev Containers: Reopen in Container")
Step 3 → Wait ~3–5 min for first build ☕
Step 4 → You're in! Run:  make help
```

**The container auto-configures:**

- ✅ Python 3.11 + all dependencies
- ✅ PostgreSQL 15 running at `db:5432`
- ✅ Schema created and seeded
- ✅ Jupyter kernel + VS Code extensions

---

## 🅱️ Option B — Local Setup

> **Best for:** Running outside Docker, CI environments, or if you prefer manual control.

```bash
# 1. Clone
git clone <repo-url>
cd insurance-analytics-project

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .                   # installs src/ as a package

# 4. Start PostgreSQL (via Docker)
docker run --name insurdb \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=insurdb \
  -p 5432:5432 -d postgres:15

# 5. Set environment variables  (or copy .env.example → .env)
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insurdb
export KAGGLE_USERNAME=your_kaggle_username
export KAGGLE_KEY=your_kaggle_api_key

# 6. Init schema + load data
make db-init
make kaggle-load

# 7. Run the pipeline and open the dashboard
make pipeline-local
# Dashboard written to outputs/dashboard.html — open it in a browser
open outputs/dashboard.html        # macOS
# xdg-open outputs/dashboard.html  # Linux
```

---

## 🔑 Environment Variables

Copy `.env.example` → `.env` for local dev (never commit `.env`).

| Variable          | Default     | Description                                      |
| ----------------- | ----------- | ------------------------------------------------ |
| `DB_HOST`         | `localhost` | Postgres host                                    |
| `DB_PORT`         | `5432`      | Postgres port                                    |
| `DB_USER`         | `postgres`  | Postgres user                                    |
| `DB_PASS`         | `postgres`  | Postgres password                                |
| `DB_NAME`         | `insurdb`   | Database name                                    |
| `KAGGLE_USERNAME` | —           | Your Kaggle username                             |
| `KAGGLE_KEY`      | —           | Kaggle API key (from kaggle.com → Account → API) |

---

## 🧪 Running Tests

```bash
make test                           # all tests with coverage
pytest tests/ -v -m integration    # integration tests (requires live DB)
```

---

## 🔧 Troubleshooting

<details>
<summary>❌ DB connection refused</summary>

```bash
pg_isready -h localhost -p 5432    # Is PostgreSQL running?
echo $DATABASE_URL                 # Is the env var set?
```

</details>

<details>
<summary>❌ Dashboard is empty or shows "No data available"</summary>

The dashboard reads from the CSV files in `outputs/`. Run the pipeline first:

```bash
make pipeline-local    # runs transform → model → DW → dashboard
```

</details>

<details>
<summary>❌ plotly not found when generating dashboard</summary>

```bash
pip install -r requirements-dashboard.txt
```

</details>

<details>
<summary>❌ Jupyter kernel not found</summary>

```bash
python -m ipykernel install --user --name=insurance --display-name="Insurance Analytics"
```

</details>

<details>
<summary>❌ Duplicate data after re-running load</summary>

The loader uses `TRUNCATE … RESTART IDENTITY CASCADE` before each insert — re-running is safe.
For a full clean slate: `make db-reset`

</details>

<details>
<summary>❌ Port 8888 already in use</summary>

```bash
jupyter lab --port=8890
```

</details>
