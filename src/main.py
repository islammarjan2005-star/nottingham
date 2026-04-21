"""
main.py
-------
Top-level entry point that orchestrates the whole pipeline:

    1. Build (or rebuild) the SQLite database from the Excel workbook.
    2. Run the four analytical SQL queries.
    3. Save the matching plots into ``img/``.

Run with:
    python src/main.py            # build everything
    python src/main.py --skip-db  # plots only (DB must already exist)
"""

# Standard library imports.
import argparse
import sys

# Project imports.
from analysis import ECAnalyser
from config import DB_PATH, SCHEMA_PATH, XLSX_PATH
from database import Database
from ingest import DataIngestor
from plots import plot_all


def parse_args():
    """Tiny command-line interface using argparse."""
    parser = argparse.ArgumentParser(
        description="Build the EC database and regenerate all report plots."
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip rebuilding the database (use the existing file).",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip plot generation (useful when only loading data).",
    )
    return parser.parse_args()


def build_database():
    """Drop and rebuild every table, then load the Excel workbook."""
    # Make sure the spreadsheet is actually present.
    if not XLSX_PATH.exists():
        sys.exit(
            f"Could not find the Excel file at {XLSX_PATH}.\n"
            f"Please copy 'Depersonalised EC .xlsx' into the data/ folder."
        )

    print(f"Building database at {DB_PATH} ...")
    with Database(DB_PATH) as db:
        # 1. Re-create the tables defined in schema.sql.
        db.run_schema(SCHEMA_PATH)
        # 2. Read the workbook and insert rows.
        ingestor = DataIngestor(XLSX_PATH)
        ingestor.run(db)
        # 3. Print a quick sanity-check count.
        n_claims = db.scalar("SELECT COUNT(*) FROM claims")
        n_students = db.scalar("SELECT COUNT(*) FROM students")
        n_modules = db.scalar("SELECT COUNT(*) FROM modules")
        print(f"  Loaded {n_claims} claims, "
              f"{n_students} students, {n_modules} modules.")


def run_analyses_and_plots():
    """Re-run every analytical query and save every plot."""
    print("Running analytical queries ...")
    with Database(DB_PATH) as db:
        results = ECAnalyser(db).run_all()
        for name, df in results.items():
            print(f"  {name}: {len(df)} rows returned")

        print("Saving plots ...")
        paths = plot_all(results)
        for p in paths:
            print(f"  wrote {p.relative_to(p.parents[1])}")


def main():
    args = parse_args()

    # Step 1 - build or refresh the database.
    if not args.skip_db:
        build_database()

    # Step 2 - regenerate all report plots.
    if not args.skip_plots:
        run_analyses_and_plots()

    print("Done.")


if __name__ == "__main__":
    main()
