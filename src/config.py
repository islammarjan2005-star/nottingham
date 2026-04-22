"""Paths and constants used across the project."""

from pathlib import Path

# Work out where the project root is (the folder above src/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
IMG_DIR = PROJECT_ROOT / "img"
SRC_DIR = PROJECT_ROOT / "src"

# The spreadsheet file in the data folder (note the space in the name -
# that's how the assessment download spells it).
XLSX_FILENAME = "Depersonalised EC .xlsx"
XLSX_PATH = DATA_DIR / XLSX_FILENAME
DB_PATH = DATA_DIR / "ec_claims.db"
SCHEMA_PATH = SRC_DIR / "schema.sql"

# Sheet names in the source workbook.
SHEET_CLAIMS = "EC Claims 20-21"
SHEET_LOOKUPS = "Data validation"

# The "Outcome" column uses single-letter / single-digit codes. Bucket
# them into three higher-level categories for plotting.
OUTCOME_CATEGORY = {
    "A": "Rejected",
    "B": "Rejected",
    "C": "Rejected",
    "D": "Rejected",
    "E": "Rejected",
    "F": "Rejected",
    "G": "Approved",
    "H": "Approved",
    "4": "Other",
    "5": "Other",
    "6": "Other",
    "7": "Other",
}
