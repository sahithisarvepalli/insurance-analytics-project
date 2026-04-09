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

### A1 — Clone repository into a container volume (recommended for Docker Desktop / WSL2)

This workflow stores the code inside a Docker-managed volume rather than a host bind-mount.
It avoids Windows-path / WSL bind-mount instability and works reliably when Docker Desktop is running.

```
Step 1 → Open VS Code
Step 2 → Ctrl+Shift+P → "Dev Containers: Clone Repository in Container Volume…"
Step 3 → Enter:  https://github.com/sahithisarvepalli/insurance-analytics-project
Step 4 → VS Code clones the repo into a Docker volume and builds the container (~3–5 min ☕)
Step 5 → You're in! Run:  make help
```

### A2 — Reopen existing local clone in container (bind-mount workflow)

```
Step 1 → Clone the repo to your WSL2 filesystem (e.g. ~/projects/)
             git clone https://github.com/sahithisarvepalli/insurance-analytics-project \
               ~/projects/insurance-analytics-project
Step 2 → Open the folder in VS Code
Step 3 → VS Code prompts "Reopen in Container" → click it
             (or Ctrl+Shift+P → "Dev Containers: Reopen in Container")
Step 4 → Wait ~3–5 min for first build ☕
Step 5 → You're in! Run:  make help
```

> **💡 WSL2 + Docker Desktop users:** Always store the repository inside the WSL2 filesystem
> (e.g. `~/projects/insurance-analytics-project`), **not** on the Windows drive (`/mnt/c/...`).
> Bind-mounting Windows paths through Docker Desktop causes path-resolution conflicts.
> Docker Desktop can remain running — it is required for Sonar MCP and Airflow.

**The container auto-configures:**

- ✅ Python 3.11 + all dependencies
- ✅ PostgreSQL 15 running at `db:5432`
- ✅ Schema created and seeded
- ✅ Jupyter kernel + VS Code extensions

> **If DB init fails on first build:** The container will still open successfully. Run
> `make setup` once inside the container to initialize the database and load sample data.

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
<summary>❌ Dev container fails with "unexpected end of parent stream" or `.gitconfig` errors</summary>

This happens when the host `~/.gitconfig` is a **directory** instead of a file.
VS Code Dev Containers tries to copy it into the container as a file, which fails.

**Automatic fix:** The `initializeCommand` in `devcontainer.json` now repairs this automatically
before each container start.

**Manual fix (if still needed):** From a WSL or Linux terminal on the host:
```bash
# Check whether the path is a directory
ls -ld ~/.gitconfig

# If it is, replace it with an empty file
rm -rf ~/.gitconfig && touch ~/.gitconfig
```

Then rebuild the container (`Dev Containers: Rebuild and Reopen in Container`).

</details>

<details>
<summary>❌ Dev container rebuild fails with Exit code 1 (Docker Desktop running)</summary>

Prefer the **Clone in Container Volume** workflow (Option A1 above) — the workspace lives
inside a Docker-managed volume so there are no Windows/WSL bind-mount conflicts.

If you need the bind-mount workflow (Option A2):
- Store the repo inside the WSL2 filesystem (`~/projects/...`), **not** `/mnt/c/...`
- Ensure **Docker Desktop → Settings → Resources → WSL Integration** has your Ubuntu distro enabled
- Clean rebuild: `Dev Containers: Clean Up Dev Containers`, then `Dev Containers: Rebuild and Reopen in Container`

</details>

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
