"""
ingest.py
---------
Reads the source Excel workbook (`Depersonalised EC .xlsx`) and writes
its contents into the SQLite database in normalised form.

Per the assessment brief, after this module has run, all further
analysis should be done with SQL against the database - the Excel file
is not touched again.

The class is split into small, well-named methods so that each step
(load workbook, build dataframes, insert rows) can be read on its own.
"""

# Standard library imports.
import re
from pathlib import Path

# Third-party imports.
import openpyxl
import pandas as pd

# Project imports.
from config import (
    OUTCOME_CATEGORY,
    SHEET_CLAIMS,
    SHEET_LOOKUPS,
)


# ---------------------------------------------------------------------
# A small helper used in several places to clean up cell values that may
# be strings with stray whitespace, the literal "N/A", or None.
# ---------------------------------------------------------------------
def _clean_text(value):
    """Return a tidy string or None for an Excel cell value."""
    # Treat None as missing.
    if value is None:
        return None
    # Pandas NaN floats also need to be treated as missing - otherwise
    # str(NaN) becomes the literal string "nan".
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    # Coerce to string in case the cell came back as a number.
    text = str(value).strip()
    # Treat empty strings, "N/A" (any case), the literal "nan", and the
    # non-breaking-space character as missing too.
    if text == "" or text.lower() in ("n/a", "nan") or text == "\xa0":
        return None
    return text


def _clean_date(value):
    """Return an ISO date string (YYYY-MM-DD) or None."""
    # openpyxl returns datetime objects for date cells.
    if value is None:
        return None
    # Pandas NaN/NaT floats need to be treated as missing too.
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    # Some date columns also contain the literal text "N/A".
    if isinstance(value, str):
        # Try a couple of common explicit formats first, then fall back
        # to pandas' generic parser. Trying explicit formats avoids the
        # "format guessed" warning that pandas otherwise emits.
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return pd.to_datetime(value, format=fmt).date().isoformat()
            except (ValueError, TypeError):
                continue
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date().isoformat()
    # Datetime/date object: return its ISO date part.
    try:
        return value.date().isoformat()
    except AttributeError:
        return None


def _parse_outcome_code(raw):
    """Extract the leading letter/number code from an outcome label.

    Examples:
        "A. Rejected - grounds are not acceptable" -> "A"
        "G. Approved - sufficient grounds..."      -> "G"
        "4. Not considered- claim submitted..."    -> "4"
        "N/A" / None / ""                          -> None
    """
    text = _clean_text(raw)
    if text is None:
        return None
    # Match a leading letter or digit followed by a "." and a space.
    match = re.match(r"^([A-Za-z0-9])\.\s", text)
    if not match:
        return None
    # Always store the code in upper case so "g" and "G" merge.
    return match.group(1).upper()


class DataIngestor:
    """Load the Excel workbook and populate a Database instance."""

    def __init__(self, xlsx_path):
        # Store the Excel file path. We delay opening the workbook until
        # ``load_workbook`` is called so the constructor stays cheap.
        self.xlsx_path = Path(xlsx_path)
        # Will hold the openpyxl workbook once loaded.
        self.workbook = None
        # Will hold a pandas DataFrame with one row per source claim.
        self.raw_claims = None

    # -----------------------------------------------------------------
    # Step 1: load the workbook into memory.
    # -----------------------------------------------------------------
    def load_workbook(self):
        """Open the .xlsx file using openpyxl in read-only mode."""
        # read_only=True is much faster for large sheets and uses less
        # memory because rows are streamed rather than fully loaded.
        # data_only=True returns calculated values instead of formulas.
        self.workbook = openpyxl.load_workbook(
            self.xlsx_path,
            read_only=True,
            data_only=True,
        )

    # -----------------------------------------------------------------
    # Step 2: turn the EC Claims sheet into a tidy pandas DataFrame.
    # -----------------------------------------------------------------
    def build_raw_claims_dataframe(self):
        """Read the claims sheet into a DataFrame with friendly columns."""
        # Grab the worksheet object.
        sheet = self.workbook[SHEET_CLAIMS]

        # The first row of the source sheet is a "section header" and
        # the second row is the real column header. We therefore skip
        # row 1 and use row 2 as the header.
        all_rows = list(sheet.iter_rows(values_only=True))
        header = list(all_rows[1])
        body = all_rows[2:]

        # Build a DataFrame using the original (verbose) column names.
        df = pd.DataFrame(body, columns=header)

        # Drop any completely-blank rows that openpyxl picked up at the
        # bottom of the sheet.
        df = df.dropna(how="all")

        # Rename the verbose columns to short, snake_case names that we
        # can use throughout the project. We list every column we
        # actually need; everything else is dropped.
        rename_map = {
            "PostID": "claim_id",
            "Posted": "posted_date",
            "Date approved by Panel": "date_approved",
            "Outcome": "outcome_raw",
            "If grounds not acceptable - please select reason": "grounds_reject_reason",
            "Course": "course_name",
            "Student ID": "student_id",
            "Year of Study": "year_of_study",
            "Level of Student": "level_of_student",
            "Are you a distance learner?": "distance_learner",
            "Are you a Tier 4 Visa holder?": "tier4_visa",
            "Does this EC claim relate to a disability (or long-term condition) already covered by a Support Plan?": "support_plan",
            "Why is the form being completed": "form_reason",
            "When were you affected": "when_affected_from",
            "Date to:": "when_affected_to",
            "Module code": "module_code",
            "Module Title": "module_title",
            "Type of Assessment": "type_of_assessment",
            "Date of assessment affected": "date_of_assessment_affected",
            "Extension Date": "extension_date",
            "Latest date Student Notified": "latest_notified_date",
            "MAY/JUNE: mark to be reweighted": "mark_reweighted",
            "Finalist?": "finalist",
            "Provisional mark notification to student": "provisional_notified_date",
            "Campus updated - end date": "campus_end_date",
            "Campus updated - EC added": "campus_added",
            "Moodle updated": "moodle_updated",
            "Previous date Student Notified 1": "previous_notified_1",
            "Previous date Student Notified 2": "previous_notified_2",
            "Previous outcome template sent 1": "previous_outcome_1",
            "Latest outcome template sent": "latest_outcome",
        }
        # Some of the long header strings contain literal newlines, so
        # match them by whether they start with the expected prefix
        # rather than relying on an exact string match.
        for col in df.columns:
            if isinstance(col, str) and col.startswith("If you are self-certifying"):
                rename_map[col] = "self_cert_exam"

        # Apply the rename and keep only the columns we actually use.
        df = df.rename(columns=rename_map)
        # The source spreadsheet has two "Extension Date" columns, which
        # both rename to ``extension_date``. Drop the duplicates so each
        # column name is unique (keeping the first occurrence).
        df = df.loc[:, ~df.columns.duplicated()]
        keep = [v for v in dict.fromkeys(rename_map.values()) if v in df.columns]
        df = df[keep].copy()

        # Tidy up text columns and parse dates.
        text_cols = [
            "claim_id", "outcome_raw", "course_name", "student_id",
            "level_of_student", "distance_learner", "tier4_visa",
            "support_plan", "form_reason", "module_code", "module_title",
            "type_of_assessment", "self_cert_exam",
            "grounds_reject_reason", "mark_reweighted", "finalist",
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].map(_clean_text)

        date_cols = [
            "posted_date", "date_approved", "when_affected_from",
            "when_affected_to", "date_of_assessment_affected",
            "extension_date", "latest_notified_date",
            "provisional_notified_date", "campus_end_date",
            "campus_added", "moodle_updated",
            "previous_notified_1", "previous_notified_2",
        ]
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].map(_clean_date)

        # Coerce year_of_study to a nullable integer (it can be missing).
        df["year_of_study"] = pd.to_numeric(
            df["year_of_study"], errors="coerce"
        ).astype("Int64")

        # Derive the outcome code from the outcome label.
        df["outcome_code"] = df["outcome_raw"].map(_parse_outcome_code)

        # Drop rows where we don't have the bare-minimum identifiers.
        df = df.dropna(subset=["claim_id"])

        # Final pass: replace any remaining NaN with Python None so that
        # SQLite stores them as NULL rather than the literal string
        # "nan". ``object`` dtype is needed so None survives.
        df = df.astype(object).where(df.notna(), None)

        # Save and return for chaining.
        self.raw_claims = df.reset_index(drop=True)
        return self.raw_claims

    # -----------------------------------------------------------------
    # Step 3: insert dimension and fact rows into the database.
    # -----------------------------------------------------------------
    def populate(self, db):
        """Insert all dimension and fact rows into ``db``.

        The order is important because the fact table (claims) has
        foreign keys back to the dimensions.
        """
        df = self.raw_claims

        # ---- outcomes dimension --------------------------------------
        # Build the lookup table from the labels we actually saw plus
        # the OUTCOME_CATEGORY mapping defined in config.py.
        outcome_rows = (
            df.dropna(subset=["outcome_code"])
              .groupby("outcome_code")["outcome_raw"].first()
              .reset_index()
        )
        outcome_payload = []
        for _, row in outcome_rows.iterrows():
            code = row["outcome_code"]
            outcome_payload.append((
                code,
                row["outcome_raw"],
                OUTCOME_CATEGORY.get(code, "Other"),
            ))
        db.executemany(
            "INSERT OR IGNORE INTO outcomes (outcome_code, description, category)"
            " VALUES (?, ?, ?)",
            outcome_payload,
        )

        # ---- courses dimension ---------------------------------------
        course_names = sorted(df["course_name"].dropna().unique())
        db.executemany(
            "INSERT OR IGNORE INTO courses (course_name) VALUES (?)",
            [(name,) for name in course_names],
        )
        # Read the auto-generated IDs back so we can reference them.
        course_lookup = dict(
            db.read_sql("SELECT course_name, course_id FROM courses").values
        )

        # ---- modules dimension ---------------------------------------
        module_rows = (
            df.dropna(subset=["module_code"])
              .groupby("module_code")["module_title"].first()
              .reset_index()
        )
        db.executemany(
            "INSERT OR IGNORE INTO modules (module_code, module_title)"
            " VALUES (?, ?)",
            list(module_rows.itertuples(index=False, name=None)),
        )

        # ---- students dimension --------------------------------------
        # For each student we keep the most recent (last) row's
        # attributes, on the assumption later rows reflect the latest
        # truth.
        student_rows = (
            df.dropna(subset=["student_id"])
              .drop_duplicates(subset=["student_id"], keep="last")
        )
        student_payload = []
        for _, row in student_rows.iterrows():
            student_payload.append((
                row["student_id"],
                course_lookup.get(row["course_name"]),
                int(row["year_of_study"]) if pd.notna(row["year_of_study"]) else None,
                row["level_of_student"],
                row["distance_learner"],
                row["tier4_visa"],
                row["support_plan"],
                row["finalist"],
            ))
        db.executemany(
            "INSERT OR IGNORE INTO students "
            "(student_id, course_id, year_of_study, level_of_student,"
            " distance_learner, tier4_visa, support_plan, finalist)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            student_payload,
        )

        # ---- claims fact table ---------------------------------------
        claim_payload = []
        for _, row in df.iterrows():
            claim_payload.append((
                row["claim_id"],
                row.get("student_id"),
                row.get("module_code"),
                row.get("outcome_code"),
                row.get("posted_date"),
                row.get("date_approved"),
                row.get("when_affected_from"),
                row.get("when_affected_to"),
                row.get("date_of_assessment_affected"),
                row.get("extension_date"),
                row.get("type_of_assessment"),
                row.get("form_reason"),
                row.get("grounds_reject_reason"),
                row.get("self_cert_exam"),
                row.get("latest_notified_date"),
                row.get("mark_reweighted"),
                row.get("provisional_notified_date"),
            ))
        # Plain INSERT (the surrogate primary key auto-increments).
        # The grain of the table is one row per (form, module) pair,
        # which matches the source spreadsheet exactly.
        db.executemany(
            "INSERT INTO claims "
            "(claim_id, student_id, module_code, outcome_code,"
            " posted_date, date_approved, when_affected_from,"
            " when_affected_to, date_of_assessment_affected,"
            " extension_date, type_of_assessment, form_reason,"
            " grounds_reject_reason, self_cert_exam,"
            " latest_notified_date, mark_reweighted,"
            " provisional_notified_date)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            claim_payload,
        )

        # ---- claim_updates supplementary table -----------------------
        # The administrative-timeline columns belong to the *form*
        # (PostID), not to each module-row, so we deduplicate by
        # claim_id before inserting and use INSERT OR IGNORE.
        update_rows = df.drop_duplicates(subset=["claim_id"], keep="first")
        update_payload = []
        for _, row in update_rows.iterrows():
            update_payload.append((
                row["claim_id"],
                row.get("campus_end_date"),
                row.get("campus_added"),
                row.get("moodle_updated"),
                row.get("previous_notified_1"),
                row.get("previous_notified_2"),
                row.get("previous_outcome_1"),
                row.get("latest_outcome"),
            ))
        db.executemany(
            "INSERT OR IGNORE INTO claim_updates "
            "(claim_id, campus_end_date, campus_added, moodle_updated,"
            " previous_notified_1, previous_notified_2,"
            " previous_outcome_1, latest_outcome)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            update_payload,
        )

    # -----------------------------------------------------------------
    # Convenience: do everything in one call.
    # -----------------------------------------------------------------
    def run(self, db):
        """Load the workbook, build the DataFrame, populate the DB."""
        self.load_workbook()
        self.build_raw_claims_dataframe()
        self.populate(db)
