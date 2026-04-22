"""
main.py - run the whole pipeline.

Usage (from the project root):
    python src/main.py              # rebuild DB and regenerate plots
    python src/main.py --skip-db    # just redo the plots
    python src/main.py --skip-plots # just load the data
"""

import argparse
import sys

from analysis import ECAnalyser
from config import DB_PATH, SCHEMA_PATH, XLSX_PATH
from database import Database
from ingest import DataIngestor
from plots import plot_all


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build the EC database and regenerate report plots."
    )
    parser.add_argument("--skip-db", action="store_true",
                        help="Skip rebuilding the database.")
    parser.add_argument("--skip-plots", action="store_true",
                        help="Skip plot generation.")
    return parser.parse_args()


def build_database():
    """Drop and rebuild every table, then load the Excel workbook."""
    if not XLSX_PATH.exists():
        sys.exit(
            f"Could not find the Excel file at {XLSX_PATH}.\n"
            f"Please copy 'Depersonalised EC .xlsx' into the data/ folder."
        )

    print(f"Building database at {DB_PATH} ...")

    db = Database(DB_PATH)
    db.connect()
    db.run_schema(SCHEMA_PATH)

    ingestor = DataIngestor(XLSX_PATH)
    ingestor.run(db)

    n_claims = db.scalar("SELECT COUNT(*) FROM claims")
    n_students = db.scalar("SELECT COUNT(*) FROM students")
    n_modules = db.scalar("SELECT COUNT(*) FROM modules")
    print(f"  Loaded {n_claims} claims, "
          f"{n_students} students, {n_modules} modules.")

    db.close()


def run_analyses_and_plots():
    """Run the analytical queries and save every plot."""
    print("Running analytical queries ...")

    db = Database(DB_PATH)
    db.connect()

    analyser = ECAnalyser(db)
    results = analyser.run_all()
    for name, df in results.items():
        print(f"  {name}: {len(df)} rows returned")

    print("Saving plots ...")
    paths = plot_all(results)
    for path in paths:
        print(f"  wrote img/{path.name}")

    db.close()


def main():
    args = parse_args()
    if not args.skip_db:
        build_database()
    if not args.skip_plots:
        run_analyses_and_plots()
    print("Done.")


if __name__ == "__main__":
    main()
