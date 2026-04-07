# 📓 Jupyter Notebooks

This directory contains interactive Jupyter notebooks for data exploration, analysis, and experimentation with the Insurance Analytics project.

## Quick Start

### Option 1: Using Make (Recommended)

```bash
# Start JupyterLab (recommended - better interface)
make run-jupyterlab

# OR start Jupyter Notebook (classic interface)
make run-jupyter
```

### Option 2: Using Command Line

```bash
# Start JupyterLab
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# OR start Jupyter Notebook
jupyter notebook --ip=0.0.0.0 --port=8889 --no-browser --allow-root
```

## Access Notebooks

- **JupyterLab**: http://localhost:8888
- **Jupyter Notebook**: http://localhost:8889

## Notebook Organization

```
notebooks/
├── myfirst.ipynb              # Guided intro: connect, explore claims data, troubleshoot
├── dw_sample_queries.ipynb    # Analytical SQL queries against insurance_dw.duckdb (star schema)
└── README.md                  # This file
```

New notebooks can be added here as needed. Recommended naming convention:
`01_exploratory_analysis.ipynb`, `02_kpi_dashboard.ipynb`, etc.

## Using the Python Environment

The notebooks automatically use the project's Python environment with all dependencies installed:

- **pandas, numpy**: Data manipulation
- **scikit-learn**: ML algorithms
- **matplotlib, seaborn, plotly**: Visualization
- **SQLAlchemy**: Database access
- **All packages in requirements.txt**

## Example Notebook

To create a new notebook:

```python
# First cell - imports
import pandas as pd
from sqlalchemy import create_engine
import os

# Get database connection
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# Query claims data
query = "SELECT * FROM insurance.claim LIMIT 10"
df = pd.read_sql(query, engine)
df.head()
```

> **Tip:** The database must be seeded first. Run `make kaggle-load` (requires Kaggle credentials)
> or `make db-init` followed by `make kaggle-load` if starting fresh.
> After loading, run `make pipeline-local` to populate the DuckDB warehouse that
> `dw_sample_queries.ipynb` queries.

## Tips

1. **Always restart kernel** after modifying source code in `src/`
2. **Use `%load_ext autoreload`** for automatic reloading:
   ```python
   %load_ext autoreload
   %autoreload 2
   from src import transform
   ```
3. **Save outputs** to `notebooks/outputs/` for tracking
4. **Use `pd.set_option()`** for better display:
   ```python
   pd.set_option('display.max_rows', 100)
   pd.set_option('display.max_columns', None)
   ```

## Best Practices

- ✅ Keep notebooks focused on specific tasks
- ✅ Document findings in markdown cells
- ✅ Extract reusable code to `src/` modules
- ✅ Version notebooks in git (use jupyterlab-git)
- ✅ Create reproducible examples with fixed seeds
- ✅ Clear outputs before committing

## Troubleshooting

**Issue**: Jupyter kernel not found

```bash
python -m ipykernel install --user --name=insurance --display-name="Insurance Analytics"
jupyter notebook --generate-config
```

**Issue**: Port already in use

```bash
# Use different port
jupyter lab --port=8890
```

**Issue**: Can't connect to database

```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Verify database is running
pg_isready -h db -p 5432
```

## Related Commands

- `make test` - Run unit tests
- `make lint` - Check code quality
- `make format` - Auto-format Python code
- `make kaggle-load` - Download Kaggle dataset and load into the database
- `make clean` - Clean cache and artifacts
