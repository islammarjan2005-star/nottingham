# Software Design

## Overview

The code is split into a few small files, one per job. If you open
`main.py` you can follow the whole thing from start to finish.

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

- `config.py` - paths, sheet names and the outcome-category mapping,
  all in one place so they're easy to change.
- `schema.sql` - CREATE TABLE statements for the 6 tables. Drops
  everything first so it can be re-run.
- `database.py` - small class that wraps sqlite3 (connect, close,
  run_schema, executemany, read_sql, scalar).
- `ingest.py` - reads the xlsx once, builds Python dicts/lists and
  writes them into the database. Nothing else touches the xlsx.
- `analysis.py` - one method per question, each returning a
  DataFrame.
- `plots.py` - one plotting function per chart, saving PNGs into
  img/.
- `main.py` - entry point: parses the flags, builds the DB, saves
  the plots.
- `eda.ipynb` - exploratory notebook with rough plots that I used
  to pick the report questions.

## Reproducibility

Running `python src/main.py` from the project root rebuilds the
database and remakes all the images. That way the report on GitHub
always shows the latest data.
