📊 CI/CD, Code Quality & SonarCloud Guide

This document explains how our GitHub Actions pipeline works, why we use specific tools, and what to keep in mind when adding new code to this monorepo.

🛠 Why do we have these Jobs?
Our pipeline is split into three distinct stages to ensure the code is clean, safe, and functional.

1. The lint Job (The "Grammar" Check)

* Reasoning: To ensure all developers follow the same coding style (PEP8) and to catch "dumb" errors (like unused variables or missing imports) before they even run.
* Tools: black (formatting), flake8/pylint (linting), mypy (type checking), and bandit (security).
* Outcome: A consistent codebase that is easy for anyone to read. If this fails, it usually means your code is "messy" or has potential security holes.

2. The test Job (The "Functional" Check)

* Reasoning: This job spins up a real PostgreSQL database in a Docker container to verify that our SQL queries and Python logic actually work with data.
* Outcome: A coverage.xml (showing which lines were tested) and a junit-report.xml (showing which tests passed/failed).
* Crucial Step: We Upload these reports as "Artifacts" so the next job can use them.

3. The sonarcloud Job (The "Health" Report)

* Reasoning: SonarCloud tracks "Technical Debt" over time. It looks for "Code Smells" (code that works but is poorly designed) and "Bugs" that standard linters might miss.
* Outcome: A dashboard in SonarCloud showing your test coverage percentage and quality gates.
* The "Secret" Fix: This job does not run tests. It downloads the reports from the test job. This avoids Connection Refused errors because SonarCloud doesn't need the database; it only needs the results of the tests.

---

🚀 How to Set Up a New Project (The Checklist)

If you create a new repository or organization, follow these steps:

Step 1: Manual SonarCloud Import

   1. Log in to SonarCloud.io.
   2. Click "+" > Analyze new project.
   3. Import your GitHub repository.
   4. CRITICAL: Go to Administration > Analysis Method and turn Automatic Analysis to OFF.
   * Why? Because we are pushing reports from GitHub Actions, and Sonar cannot handle two sources of data at once.

Step 2: GitHub Secrets
Ensure these secrets are added in GitHub Settings > Secrets and variables > Actions:

* SONAR_TOKEN: Found in your SonarCloud Account Security settings.
* CODECOV_TOKEN: Found in your Codecov repository settings.

Step 3: Match the Keys
The sonar.projectKey in your sonar-project.properties must match the key in your .github/workflows/ci.yml file exactly.


---

⚠️ Things to Pay Attention To

   1. Database Connection: Never try to connect to localhost:5432 in a unit test unless you have defined a services: postgres block in that specific GitHub job.
   2. Mono-repo Paths: If you add a new folder (e.g., analytics/), make sure to add it to the sonar.sources list in sonar-project.properties.
   3. Fetch Depth: In the YAML, always use fetch-depth: 0 during checkout. Without this, SonarCloud cannot see the Git history and won't know who to blame for new code smells!
   4. Coverage Exclusions: If you have folders with "synthetic data" or "scripts," exclude them in the properties file so they don't lower your overall coverage score.

---

📈 Expected Outcomes

* Green Checkmark: All tests passed, code is formatted, and no major security flaws found.
* Quality Gate Passed: SonarCloud confirms your new code has >80% coverage and zero new "Critical" issues.
