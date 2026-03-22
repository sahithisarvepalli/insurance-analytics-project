# Concepts Folder: Learning Python Concepts from Insurance Analytics

This folder contains small, standalone Python scripts to help you understand and practice the key concepts used in the main insurance analytics application. Each script focuses on 1-2 concepts and is designed to be simple, runnable, and educational.

## 📚 Concepts Covered

1. **01_argparse_basics.py**: Command-line argument parsing with `argparse`.
2. **02_csv_read_write.py**: Reading and writing CSV files with `pandas`.
3. **03_db_connection.py**: Database connections and queries with `SQLAlchemy`.
4. **04_pandas_transform.py**: Data manipulation and aggregation with `pandas`.
5. **05_synthetic_data.py**: Generating random data with `numpy`.
6. **06_ml_basics.py**: Basic machine learning with `scikit-learn`.
7. **07_logging.py**: Logging messages with Python's `logging` module.
8. **08_config_loading.py**: Loading YAML config with environment variable expansion.
9. **09_excel_report.py**: Writing Excel files with `pandas` and `openpyxl`.
10. **10_testing_basics.py**: Writing and running tests with `pytest`.
11. **11_date_handling.py**: Working with dates using `pandas` and `datetime`.

## 🚀 How to Use

1. **Run each script individually** to see it in action:
   ```bash
   python concepts/01_argparse_basics.py --name "YourName" --age 25
   python concepts/02_csv_read_write.py
   # etc.
   ```

2. **Modify and experiment**: Change values, add features, break and fix them to learn.

3. **Read the code**: Each script has comments explaining what's happening.

4. **Connect to the main app**: Once you understand these, revisit the main `src/` files — they'll make much more sense!

## 📋 Detailed Instructions for Each Concept File

### 1. 01_argparse_basics.py
**Purpose**: Learn how to parse command-line arguments in Python scripts.
**How to Run**:
- Basic: `python concepts/01_argparse_basics.py`
- With args: `python concepts/01_argparse_basics.py --name Alice --age 30`
- Help: `python concepts/01_argparse_basics.py --help`
**What It Does**: Prints a greeting using provided name/age or defaults.
**Experiment**: Add a new argument like `--city` and modify the print statement.

### 2. 02_csv_read_write.py
**Purpose**: Practice reading from and writing to CSV files using pandas.
**How to Run**: `python concepts/02_csv_read_write.py`
**What It Does**: Creates sample data, writes to CSV, reads it back, and prints.
**Experiment**: Change the data (add columns), filter rows when reading.

### 3. 03_db_connection.py
**Purpose**: Understand database connections and basic queries with SQLAlchemy.
**How to Run**: `python concepts/03_db_connection.py` (assumes DB is running).
**What It Does**: Connects to DB, creates a table, inserts data, queries it.
**Experiment**: Add more columns to the table or try a different query.

### 4. 04_pandas_transform.py
**Purpose**: Learn data transformation and aggregation with pandas.
**How to Run**: `python concepts/04_pandas_transform.py`
**What It Does**: Creates sample data, groups by categories, computes sums/means.
**Experiment**: Add more aggregations or filter the data before grouping.

### 5. 05_synthetic_data.py
**Purpose**: Generate synthetic data using numpy's random functions.
**How to Run**: `python concepts/05_synthetic_data.py`
**What It Does**: Generates random ages, amounts, and categories; prints stats.
**Experiment**: Change distributions (e.g., use normal instead of uniform).

### 6. 06_ml_basics.py
**Purpose**: Introduction to machine learning pipelines with scikit-learn.
**How to Run**: `python concepts/06_ml_basics.py`
**What It Does**: Trains a simple classifier on synthetic data, prints accuracy.
**Experiment**: Try a different model (e.g., RandomForest) or add features.

### 7. 07_logging.py
**Purpose**: Use Python's logging module for debugging and info messages.
**How to Run**: `python concepts/07_logging.py`
**What It Does**: Logs messages at different levels (info, warning, error).
**Experiment**: Add more log statements or change log levels.

### 8. 08_config_loading.py
**Purpose**: Load configuration from YAML files with env var expansion.
**How to Run**: `python concepts/08_config_loading.py`
**What It Does**: Reads config.yaml, expands vars, prints the config.
**Experiment**: Set an env var (e.g., `export DB_HOST=localhost`) and see it expand.

### 9. 09_excel_report.py
**Purpose**: Create Excel reports with multiple sheets using pandas.
**How to Run**: `python concepts/09_excel_report.py`
**What It Does**: Writes sample data to an Excel file with sheets.
**Experiment**: Add more sheets or format the Excel (colors, etc.).

### 10. 10_testing_basics.py
**Purpose**: Write and run unit tests with pytest.
**How to Run**: `python -m pytest concepts/10_testing_basics.py -v`
**What It Does**: Tests a simple function for correctness.
**Experiment**: Add more test cases or test a different function.

### 11. 11_date_handling.py
**Purpose**: Work with dates in pandas and datetime.
**How to Run**: `python concepts/11_date_handling.py`
**What It Does**: Parses dates, calculates ages, formats output.
**Experiment**: Add date arithmetic or handle different date formats.

## 📋 Learning Plan

- Start with basics (1-3): CLI, files, DB.
- Move to data (4-5): Pandas, numpy.
- Advanced (6-8): ML, logging, config.
- Output (9-11): Reports, tests, dates.

After completing these, you'll be ready to understand the full insurance analytics project!
