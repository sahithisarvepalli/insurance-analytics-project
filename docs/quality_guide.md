# ✅ Code Quality Guide

> **Concept:** Before code reaches the main branch, it passes through three automated gates: *style*, *correctness*, and *health*. These run automatically on every push via GitHub Actions CI.

---

## 🚦 The Three Quality Gates

```
Every git push / pull request triggers:

  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
  │  1️⃣ Lint         │──▶│  2️⃣ Test         │──▶│  3️⃣ SonarCloud  │
  │  "Grammar check" │   │  "Does it work?" │   │  "Health score" │
  │                 │   │                 │   │                 │
  │ black           │   │ pytest          │   │ Technical debt  │
  │ flake8/pylint   │   │ PostgreSQL DB   │   │ Coverage trend  │
  │ mypy            │   │ coverage.xml    │   │ Quality gate    │
  │ bandit          │   │ junit-report    │   │                 │
  └─────────────────┘   └─────────────────┘   └─────────────────┘
       ❌ messy code          ❌ broken logic        ❌ poor design
```

### Gate 1 — Lint (Style + Safety)

| Tool | What it catches |
|------|----------------|
| `black` | Inconsistent formatting |
| `flake8` | PEP8 violations, unused imports |
| `pylint` | Logic smells, undefined names |
| `mypy` | Type errors |
| `bandit` | Security vulnerabilities |

Run locally: `make lint` or `make format` (auto-fix formatting)

### Gate 2 — Test (Correctness)

- Spins up a real **PostgreSQL** container
- Runs `pytest` against live data
- Produces `coverage.xml` + `junit-report.xml` (used by SonarCloud)

Run locally: `make test`

### Gate 3 — SonarCloud (Health)

- Reads test reports from Gate 2 (no DB needed)
- Tracks coverage %, code smells, and bugs over time
- Enforces a **Quality Gate**: >80% coverage, zero new critical issues

View your dashboard at [sonarcloud.io](https://sonarcloud.io)

---

## 🔧 New Project Setup Checklist

Setting up quality gates for a new repo? Follow these steps:

- [ ] **1. Import to SonarCloud**
  - sonarcloud.io → "+" → Analyze new project → import your GitHub repo
  - ⚠️ **Turn Automatic Analysis OFF** (Administration → Analysis Method) — we push reports from GitHub Actions instead

- [ ] **2. Add GitHub Secrets** (Settings → Secrets and variables → Actions)
  - `SONAR_TOKEN` — from SonarCloud Account Security settings
  - `CODECOV_TOKEN` — from Codecov repository settings

- [ ] **3. Match the project key**
  - `sonar.projectKey` in `sonar-project.properties` must match the key in `.github/workflows/ci.yml`

---

## ⚠️ Common Gotchas

| Gotcha | What to do |
|--------|-----------|
| Connecting to `localhost:5432` in unit tests | Only do this if your GitHub Actions job has a `services: postgres` block |
| Adding a new source folder (e.g. `analytics/`) | Add it to `sonar.sources` in `sonar-project.properties` |
| SonarCloud can't see git history | Use `fetch-depth: 0` in your checkout step |
| Coverage score drops from test scripts | Exclude them in `sonar-project.properties` under `sonar.coverage.exclusions` |

---

## 🎯 What "Passing" Looks Like

```
✅ Lint job     → green checkmark on your PR
✅ Test job     → all tests pass, coverage uploaded
✅ SonarCloud   → Quality Gate: PASSED
                   Coverage ≥ 80%
                   New critical issues = 0
```
