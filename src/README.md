# Source Code

All the Python source code for the project.

## Files

- [`config.py`](config.py) - paths, sheet names and the
  outcome-category mapping. One place to change if files move.
- [`schema.sql`](schema.sql) - `CREATE TABLE` statements for the
  six tables. Re-runnable.
- [`database.py`](database.py) - `Database` class, a small wrapper
  around `sqlite3`.
- [`ingest.py`](ingest.py) - `DataIngestor` class. Reads the
  workbook with `openpyxl` and loads the tables.
- [`analysis.py`](analysis.py) - `ECAnalyser` class. One method per
  question, each returning a pandas DataFrame.
- [`plots.py`](plots.py) - one plotting function per question, each
  saves a PNG into `../img/`.
- [`main.py`](main.py) - entry point. Run `python src/main.py` from
  the project root.
- [`eda.ipynb`](eda.ipynb) - exploratory notebook I used to pick
  the questions in `REPORT.md`.
- [`requirements.txt`](requirements.txt) - Python dependencies.

## Running

From the project root:

```bash
pip install -r src/requirements.txt
python src/main.py
```

This rebuilds `data/ec_claims.db` from
`data/Depersonalised EC Tracker 2020-2021.xlsx` and re-generates every PNG in
`../img/`.
