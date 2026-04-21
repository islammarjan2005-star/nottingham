# Images

## Overview

This directory contains images used in the report and documentation. The
images are referenced from Markdown files using **relative paths** so that
they render both on GitHub and from a downloaded zip of the repository.

## Files

All plots in this directory are produced by `python src/main.py`. If the
file is missing, re-run the pipeline.

- `q1_claims_vs_deadline_hist.png` — Q1 distribution of days between
  claim submission and the affected assessment date (histogram).
- `q1_claims_vs_deadline_box.png` — Q1 box plot of the same metric, split
  by approved vs. rejected claims.
- `q2_top_modules.png` — Q2 horizontal stacked bar of the modules with
  the most EC claims, coloured by outcome category.
- `q3_response_time_monthly.png` — Q3 monthly box plot of Panel response
  time (days from posting to approval) over the academic year.
- `q4_outcome_by_level.png` — Q4 grouped bar chart of approval rate by
  student level and finalist status.
- `er_diagram.png` — optional static render of the database ER diagram
  (the live Mermaid version lives in `doc/database_design.md`).
