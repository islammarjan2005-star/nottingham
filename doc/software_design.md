# Software Design

## Overview

The code is split across a few small files, one per job. Anyone who
opens `src/main.py` can follow the whole pipeline end to end.

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

- `config.py` - paths, sheet names and the outcome-category map in one
  place so they're easy to find.
- `schema.sql` - CREATE TABLE statements for all 6 tables. Drops
  everything first so it can be re-run.
- `database.py` - small sqlite3 wrapper class (connect, close,
  run_schema, executemany, read_sql, scalar).
- `ingest.py` - reads the xlsx once, builds Python dicts/lists, writes
  them into the database. Nothing else touches the spreadsheet.
- `analysis.py` - one method per question, each returning a DataFrame.
- `plots.py` - one plotting function per chart, saving PNGs into img/.
- `main.py` - entry point: parse flags, build the DB, save the plots.
- `eda.ipynb` - exploratory notebook with rough plots that helped me
  pick the questions for the report.

## Reproducibility

Running `python src/main.py` from the project root rebuilds the
database and regenerates every image in `img/`. The report can then
be read on GitHub and every plot shows the latest version of the data.
