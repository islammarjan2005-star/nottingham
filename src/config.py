"""
config.py
---------
Central place for all of the constants used by the project. Keeping the
hard-coded paths and column names here means that if a file is renamed
or moved, only this one file needs to change.
"""

# Standard library imports.
from pathlib import Path

# ---------------------------------------------------------------------
# Project paths.
# ---------------------------------------------------------------------
# PROJECT_ROOT points at the top-level folder of the repository (the
# parent of the src/ directory). We compute it from __file__ so the
# code works no matter where the user runs `python` from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folder that holds the raw spreadsheet (git-ignored) and the SQLite DB.
DATA_DIR = PROJECT_ROOT / "data"

# Folder where generated plots are written. The REPORT.md file
# references images here using relative paths.
IMG_DIR = PROJECT_ROOT / "img"

# Source directory (used to locate schema.sql).
SRC_DIR = PROJECT_ROOT / "src"

# ---------------------------------------------------------------------
# File names.
# ---------------------------------------------------------------------
# Default name of the input spreadsheet. The trailing space before the
# extension is preserved exactly because that is how the file is named
# in the assessment download.
XLSX_FILENAME = "Depersonalised EC .xlsx"

# Full path to the input spreadsheet.
XLSX_PATH = DATA_DIR / XLSX_FILENAME

# Path to the SQLite database file that ingestion will create.
DB_PATH = DATA_DIR / "ec_claims.db"

# Path to the schema definition.
SCHEMA_PATH = SRC_DIR / "schema.sql"

# ---------------------------------------------------------------------
# Spreadsheet sheet names (taken from the source workbook).
# ---------------------------------------------------------------------
SHEET_CLAIMS = "EC Claims 20-21"
SHEET_LOOKUPS = "Data validation"

# ---------------------------------------------------------------------
# Outcome category mapping. The Quality Manual codes (column B of the
# claims sheet) are letters A-H plus a few numeric codes. We bucket them
# into three high-level categories so plots can colour by category.
# ---------------------------------------------------------------------
OUTCOME_CATEGORY = {
    "A": "Rejected",
    "B": "Rejected",
    "C": "Rejected",
    "D": "Rejected",
    "E": "Rejected",
    "F": "Rejected",
    "G": "Approved",
    "H": "Approved",   # provisionally approved, deferred to exam board
    "4": "Other",      # not considered - claim out of time
    "5": "Other",      # not considered - evidence out of time
    "6": "Other",      # not eligible - after exam board
    "7": "Other",      # max periods exceeded
}
