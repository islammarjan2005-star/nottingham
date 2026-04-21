# Source Code

## Overview

This directory contains all of the Python source code for the project.

## Files

- [`config.py`](config.py) - Hard-coded paths, sheet names and the
  outcome-category mapping. Single place to change if files move.
- [`schema.sql`](schema.sql) - SQL `CREATE TABLE` statements for the
  six normalised tables. Re-runnable.
- [`database.py`](database.py) - `Database` class - small wrapper
  around `sqlite3` with `with`-block support.
- [`ingest.py`](ingest.py) - `DataIngestor` class - reads the workbook
  with `openpyxl` and populates the database.
- [`analysis.py`](analysis.py) - `ECAnalyser` class - one method per
  analytical question, each returning a pandas DataFrame.
- [`plots.py`](plots.py) - One plotting function per question, saving
  PNGs into `../img/`.
- [`main.py`](main.py) - Entry point. Run `python src/main.py` from
  the project root.
- [`eda.ipynb`](eda.ipynb) - Exploratory notebook used to shape the
  questions in `REPORT.md`.
- [`requirements.txt`](requirements.txt) - Python dependencies.

## Running

From the project root:

```bash
pip install -r src/requirements.txt
python src/main.py
```

This will rebuild `data/ec_claims.db` from
`data/Depersonalised EC .xlsx` and regenerate every PNG in `../img/`.
