"""
ingest.py
---------
Reads the Excel workbook (Depersonalised EC .xlsx) and writes its rows
into the SQLite database in the right order so that foreign keys work.

After this module has run, the rest of the project only uses SQL
against the database - we don't open the spreadsheet again.
"""

# openpyxl can read .xlsx files row by row.
import openpyxl

# Constants (sheet names and the outcome category map) live in config.
from config import OUTCOME_CATEGORY, SHEET_CLAIMS


# ---------------------------------------------------------------------
# Two small helper functions to clean up the values that come out of
# Excel. We define them as plain functions (not methods) because they
# don't need any state.
# ---------------------------------------------------------------------

def clean_text(value):
    """Return a tidy string, or None if the cell is empty/missing."""
    # Treat None as missing.
    if value is None:
        return None
    # Strip whitespace.
    text = str(value).strip()
    # Treat blank strings, "N/A" (any case) and the non-breaking space
    # character as missing.
    if text == "" or text.lower() == "n/a" or text == "\xa0":
        return None
    return text


def clean_date(value):
    """Return a date as 'YYYY-MM-DD' text, or None if missing."""
    # Excel date cells come back as datetime objects.
    if value is None:
        return None
    # If the cell is text like "N/A" we return None.
    if isinstance(value, str):
        return None
    # Datetime objects have a date() method that returns just the date.
    try:
        return value.date().isoformat()
    except AttributeError:
        return None


def parse_outcome_code(label):
    """Pull the leading code letter/number out of an outcome label.

    Example: 'A. Rejected - grounds not acceptable' -> 'A'
             'G. Approved ...'                       -> 'G'
             'N/A' or None                           -> None
    """
    # Use the helper above to handle None / N/A / blank.
    text = clean_text(label)
    if text is None:
        return None
    # The codes are always followed by ". " - split on that.
    parts = text.split(". ", 1)
    if len(parts) < 2:
        return None
    code = parts[0].strip()
    # We only accept a single letter or single digit code.
    if len(code) == 1:
        return code.upper()
    return None


# ---------------------------------------------------------------------
# Main ingestion class. We use a class (rather than a script) so that
# each step (load workbook, build rows, populate DB) has its own method
# and the order is easy to follow.
# ---------------------------------------------------------------------

class DataIngestor:
    """Loads the EC spreadsheet and writes everything into the database."""

    def __init__(self, xlsx_path):
        # The path to the .xlsx file we will read from.
        self.xlsx_path = xlsx_path
        # The sheet rows will live here once we've loaded them.
        self.rows = []

    # -----------------------------------------------------------------
    # Step 1 - read every data row out of the spreadsheet.
    # -----------------------------------------------------------------
    def load_rows(self):
        """Open the workbook and copy every data row into self.rows."""
        # Open the workbook in read-only mode (faster, less memory).
        wb = openpyxl.load_workbook(
            self.xlsx_path, read_only=True, data_only=True
        )
        # Get the worksheet that holds the claims.
        sheet = wb[SHEET_CLAIMS]

        # The first sheet row is a "section" header and the second row
        # holds the real column headers, so the data starts at row 3.
        all_rows = list(sheet.iter_rows(values_only=True))
        data_rows = all_rows[2:]

        # Skip rows where the PostID column (index 6) is blank.
        for row in data_rows:
            if row[6] is not None:
                self.rows.append(row)

    # -----------------------------------------------------------------
    # Step 2 - turn the raw rows into rows ready to insert into the DB.
    # -----------------------------------------------------------------
    def build_records(self):
        """Build dictionaries / lists for each table.

        Returns a tuple of:
            (courses_set, modules_dict, students_dict,
             outcomes_dict, claims_list, updates_dict)
        """
        # We use a set for courses so duplicates disappear automatically.
        courses_set = set()
        # module_code -> module_title
        modules_dict = {}
        # student_id -> dict of attributes
        students_dict = {}
        # outcome_code -> (description, category)
        outcomes_dict = {}
        # one tuple per (form, module) row that goes into `claims`.
        claims_list = []
        # PostID -> tuple of admin-trail dates for `claim_updates`.
        updates_dict = {}

        # Loop through every data row of the spreadsheet.
        for row in self.rows:
            # Pull out the columns we care about, by their position
            # in the source sheet. The numbers come from the "Column"
            # comments in src/schema.sql and the column listing we
            # checked during EDA.
            outcome_label   = row[1]    # B - Outcome
            grounds_reason  = row[5]    # F - Reason if grounds not OK
            post_id         = clean_text(row[6])    # G - PostID
            posted_date     = clean_date(row[7])    # H - Posted
            course_name     = clean_text(row[8])    # I - Course
            student_id      = clean_text(row[9])    # J - Student ID
            year_of_study   = row[10]               # K - Year of study
            level_student   = clean_text(row[11])   # L - Level
            distance_learn  = clean_text(row[12])   # M - Distance learner
            tier4_visa      = clean_text(row[13])   # N - Tier 4 visa
            support_plan    = clean_text(row[14])   # O - Support plan
            form_reason     = clean_text(row[15])   # P - Why completing
            affected_from   = clean_date(row[16])   # Q - When affected
            affected_to     = clean_date(row[17])   # R - Date to
            self_cert_exam  = clean_text(row[20])   # U - Self cert
            module_code     = clean_text(row[22])   # W - Module code
            module_title    = clean_text(row[23])   # X - Module title
            assessment_type = clean_text(row[24])   # Y - Type of assessment
            assess_date     = clean_date(row[25])   # Z - Date affected
            extension_date  = clean_date(row[35])   # AJ - Extension date
            latest_notified = clean_date(row[36])   # AK - Latest notified
            prev_notified_1 = clean_date(row[37])   # AL
            prev_notified_2 = clean_date(row[38])   # AM
            mark_reweight   = clean_text(row[39])   # AN
            finalist        = clean_text(row[40])   # AO
            prov_notified   = clean_date(row[41])   # AP
            date_approved   = clean_date(row[0])    # A - Date approved
            campus_end      = clean_date(row[32])   # AG
            campus_added    = clean_date(row[33])   # AH
            moodle_updated  = clean_date(row[34])   # AI
            prev_outcome_1  = clean_text(row[31])   # AF
            latest_outcome  = clean_text(row[30])   # AE

            # Parse the leading code out of the outcome label.
            outcome_code = parse_outcome_code(outcome_label)

            # ---- dimension: courses --------------------------------
            if course_name is not None:
                courses_set.add(course_name)

            # ---- dimension: modules --------------------------------
            if module_code is not None and module_code not in modules_dict:
                modules_dict[module_code] = module_title

            # ---- dimension: students -------------------------------
            # If we've never seen this student before, save their attrs.
            # If we have, we leave the existing record alone.
            if student_id is not None and student_id not in students_dict:
                # Year of study can be a number or None - keep as-is.
                if isinstance(year_of_study, str):
                    year_of_study = clean_text(year_of_study)
                students_dict[student_id] = {
                    "course_name": course_name,
                    "year_of_study": year_of_study,
                    "level_of_student": level_student,
                    "distance_learner": distance_learn,
                    "tier4_visa": tier4_visa,
                    "support_plan": support_plan,
                    "finalist": finalist,
                }

            # ---- dimension: outcomes -------------------------------
            if outcome_code is not None and outcome_code not in outcomes_dict:
                description = clean_text(outcome_label)
                category = OUTCOME_CATEGORY.get(outcome_code, "Other")
                outcomes_dict[outcome_code] = (description, category)

            # ---- fact: claims --------------------------------------
            # One row per (PostID, module).
            claims_list.append((
                post_id,
                student_id,
                module_code,
                outcome_code,
                posted_date,
                date_approved,
                affected_from,
                affected_to,
                assess_date,
                extension_date,
                assessment_type,
                form_reason,
                clean_text(grounds_reason),
                self_cert_exam,
                latest_notified,
                mark_reweight,
                prov_notified,
            ))

            # ---- supplementary: claim_updates ----------------------
            # The admin trail belongs to the PostID, not to the module
            # row, so we keep the first one we see for each PostID.
            if post_id not in updates_dict:
                updates_dict[post_id] = (
                    post_id,
                    campus_end,
                    campus_added,
                    moodle_updated,
                    prev_notified_1,
                    prev_notified_2,
                    prev_outcome_1,
                    latest_outcome,
                )

        return (courses_set, modules_dict, students_dict,
                outcomes_dict, claims_list, updates_dict)

    # -----------------------------------------------------------------
    # Step 3 - write everything into the database.
    # -----------------------------------------------------------------
    def populate(self, db):
        """Insert dimension and fact rows into the database in order."""
        (courses_set, modules_dict, students_dict,
         outcomes_dict, claims_list, updates_dict) = self.build_records()

        # ---- outcomes -----------------------------------------------
        outcomes_rows = []
        for code, (description, category) in outcomes_dict.items():
            outcomes_rows.append((code, description, category))
        db.executemany(
            "INSERT OR IGNORE INTO outcomes "
            "(outcome_code, description, category) VALUES (?, ?, ?)",
            outcomes_rows,
        )

        # ---- courses ------------------------------------------------
        courses_rows = []
        for name in sorted(courses_set):
            courses_rows.append((name,))
        db.executemany(
            "INSERT OR IGNORE INTO courses (course_name) VALUES (?)",
            courses_rows,
        )

        # Read the auto-generated course IDs back so we can use them
        # as foreign keys when we insert students.
        course_lookup = {}
        cursor = db.conn.execute("SELECT course_name, course_id FROM courses")
        for course_name, course_id in cursor.fetchall():
            course_lookup[course_name] = course_id

        # ---- modules ------------------------------------------------
        modules_rows = []
        for code, title in modules_dict.items():
            modules_rows.append((code, title))
        db.executemany(
            "INSERT OR IGNORE INTO modules (module_code, module_title) "
            "VALUES (?, ?)",
            modules_rows,
        )

        # ---- students -----------------------------------------------
        students_rows = []
        for student_id, attrs in students_dict.items():
            # Look up the course's surrogate ID; may be None.
            course_id = course_lookup.get(attrs["course_name"])
            # year_of_study may be None or a number; leave it as-is.
            year = attrs["year_of_study"]
            students_rows.append((
                student_id,
                course_id,
                year,
                attrs["level_of_student"],
                attrs["distance_learner"],
                attrs["tier4_visa"],
                attrs["support_plan"],
                attrs["finalist"],
            ))
        db.executemany(
            "INSERT OR IGNORE INTO students "
            "(student_id, course_id, year_of_study, level_of_student,"
            " distance_learner, tier4_visa, support_plan, finalist) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            students_rows,
        )

        # ---- claims (fact table) ------------------------------------
        # We use a plain INSERT because the surrogate primary key
        # claim_row_id is auto-generated.
        db.executemany(
            "INSERT INTO claims "
            "(claim_id, student_id, module_code, outcome_code,"
            " posted_date, date_approved, when_affected_from,"
            " when_affected_to, date_of_assessment_affected,"
            " extension_date, type_of_assessment, form_reason,"
            " grounds_reject_reason, self_cert_exam,"
            " latest_notified_date, mark_reweighted,"
            " provisional_notified_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            claims_list,
        )

        # ---- claim_updates (per form) -------------------------------
        updates_rows = list(updates_dict.values())
        db.executemany(
            "INSERT OR IGNORE INTO claim_updates "
            "(claim_id, campus_end_date, campus_added, moodle_updated,"
            " previous_notified_1, previous_notified_2,"
            " previous_outcome_1, latest_outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            updates_rows,
        )

    # -----------------------------------------------------------------
    # Convenience: run all three steps in order.
    # -----------------------------------------------------------------
    def run(self, db):
        """Do everything in one call."""
        self.load_rows()
        self.populate(db)
