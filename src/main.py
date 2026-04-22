"""
main.py
-------
Top-level script that runs the whole pipeline:

  1. Build (or rebuild) the SQLite database from the Excel workbook.
  2. Run the four analytical SQL queries.
  3. Save the matching plots into img/.

Run from the project root:
    python src/main.py            # build database + plots
    python src/main.py --skip-db  # plots only (DB must exist)
"""

# argparse handles command-line flags.
import argparse
# sys is used to exit early if something is wrong.
import sys

# Project imports.
from analysis import ECAnalyser
from config import DB_PATH, SCHEMA_PATH, XLSX_PATH
from database import Database
from ingest import DataIngestor
from plots import plot_all


def parse_args():
    """Read the optional command-line flags."""
    parser = argparse.ArgumentParser(
        description="Build the EC database and regenerate report plots."
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip rebuilding the database (use the existing file).",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip plot generation.",
    )
    return parser.parse_args()


def build_database():
    """Drop and rebuild every table, then load the Excel workbook."""
    # If the spreadsheet is not in data/, we can't do anything.
    if not XLSX_PATH.exists():
        sys.exit(
            f"Could not find the Excel file at {XLSX_PATH}.\n"
            f"Please copy 'Depersonalised EC .xlsx' into the data/ folder."
        )

    print(f"Building database at {DB_PATH} ...")

    # 1. Open the database connection.
    db = Database(DB_PATH)
    db.connect()

    # 2. Re-create every table (the SQL script drops them first).
    db.run_schema(SCHEMA_PATH)

    # 3. Load the workbook and insert every row.
    ingestor = DataIngestor(XLSX_PATH)
    ingestor.run(db)

    # 4. Print a quick sanity check of how many rows we loaded.
    n_claims = db.scalar("SELECT COUNT(*) FROM claims")
    n_students = db.scalar("SELECT COUNT(*) FROM students")
    n_modules = db.scalar("SELECT COUNT(*) FROM modules")
    print(f"  Loaded {n_claims} claims, "
          f"{n_students} students, {n_modules} modules.")

    # 5. Close the database connection.
    db.close()


def run_analyses_and_plots():
    """Run every analytical query and save every plot."""
    print("Running analytical queries ...")

    # Open the database.
    db = Database(DB_PATH)
    db.connect()

    # Build the analyser and run all four queries.
    analyser = ECAnalyser(db)
    results = analyser.run_all()
    for name, df in results.items():
        print(f"  {name}: {len(df)} rows returned")

    # Save every plot.
    print("Saving plots ...")
    paths = plot_all(results)
    for path in paths:
        # Print just the filename so the output is short.
        print(f"  wrote img/{path.name}")

    # Close the database.
    db.close()


def main():
    """Entry point - run whichever steps the user asked for."""
    args = parse_args()

    # Step 1 - build or refresh the database.
    if not args.skip_db:
        build_database()

    # Step 2 - regenerate every plot.
    if not args.skip_plots:
        run_analyses_and_plots()

    print("Done.")


# Standard "run only if launched directly" guard.
if __name__ == "__main__":
    main()
