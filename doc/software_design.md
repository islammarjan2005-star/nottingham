# Software Design

## Overview

The code is split into a small number of files, each with one clear
job. The entry point is `src/main.py`, which calls the rest in
order, so reading that file gives you the whole pipeline from start
to finish.

## Class diagram

```mermaid
classDiagram
    class Database {
        +str db_path
        +sqlite3.Connection conn
        +connect()
        +close()
        +run_schema(schema_path)
        +executemany(sql, rows)
        +read_sql(sql, params) DataFrame
        +scalar(sql)
    }

    class DataIngestor {
        +str xlsx_path
        +set courses
        +dict modules
        +dict students
        +dict outcomes
        +list claims
        +dict updates
        +load_rows() list
        +build_records()
        +populate(db)
        +run(db)
    }

    class ECAnalyser {
        +Database db
        +q1_days_before_deadline() DataFrame
        +q2_top_modules() DataFrame
        +q3_response_time_by_month() DataFrame
        +q4_outcome_by_assessment_type() DataFrame
        +run_all() dict
    }

    class plots {
        <<module>>
        +plot_q1_histogram(df)
        +plot_q1_boxplot(df)
        +plot_q2_top_modules(df)
        +plot_q3_response_time(df)
        +plot_q4_volume(df)
        +plot_q4_approval_rate(df)
        +plot_all(results) list
    }

    class main {
        <<module>>
        +parse_args()
        +build_database()
        +run_analyses_and_plots()
        +main()
    }

    main ..> Database
    main ..> DataIngestor
    main ..> ECAnalyser
    main ..> plots
    DataIngestor ..> Database
    ECAnalyser ..> Database
```

## Pipeline

```mermaid
flowchart LR
    A([Excel workbook]) --> B[DataIngestor]
    B --> C[(SQLite<br/>ec_claims.db)]
    C --> D[ECAnalyser<br/>SQL queries]
    D --> E[plots module]
    E --> F([img/*.png])
    F --> G([REPORT.md])
```

## What each file does

- `config.py` - paths, sheet names and the outcome-category mapping.
  Keeping the constants in one place means that if the file layout
  or the codes change, only this file needs updating.
- `schema.sql` - CREATE TABLE statements for the six tables. Drops
  everything first so the script can be re-run safely.
- `database.py` - small `Database` class that wraps sqlite3
  (connect, close, run_schema, executemany, read_sql, scalar).
- `ingest.py` - reads the xlsx once with openpyxl, builds plain
  Python dicts and lists from the cells, then writes them into the
  database. Per the brief, nothing else touches the xlsx.
- `analysis.py` - `ECAnalyser` class with one method per question.
  Each method runs one SQL query and returns a pandas DataFrame.
- `plots.py` - one plotting function per chart, each saving a PNG
  into `img/` with consistent colours and labels.
- `main.py` - entry point that parses the command-line flags,
  builds the database and saves the plots in turn.
- `eda.ipynb` - exploratory notebook containing rough plots I used
  to decide which questions to include in the report. This gives
  the clear distinction between EDA and stakeholder plots that the
  marking rubric asks for.

## Reproducibility

Running `python src/main.py` from the project root rebuilds the
database from scratch and regenerates every image in `img/`. This
means the images embedded in `REPORT.md` always reflect the current
data and the current analytical code - no manual steps required.
