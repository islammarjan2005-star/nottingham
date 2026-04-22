"""
ingest.py - read the EC spreadsheet and load it into the database.

Only this file touches the xlsx. Everything else (analysis, plots) uses
SQL against the database that this script builds.
"""

import openpyxl
from config import OUTCOME_CATEGORY, SHEET_CLAIMS


def clean_text(value):
    """Return a tidy string or None for an Excel cell value."""
    if value is None:
        return None
    text = str(value).strip()
    # Treat blank, "N/A" and the non-breaking-space char as missing.
    if text == "" or text.lower() == "n/a" or text == "\xa0":
        return None
    return text


def clean_date(value):
    """Convert a datetime cell to an ISO date string (YYYY-MM-DD)."""
    if value is None:
        return None
    if isinstance(value, str):
        # We only accept real date cells, not text like "N/A".
        return None
    try:
        return value.date().isoformat()
    except AttributeError:
        return None


def parse_outcome_code(label):
    """Pull the 1-character code from an outcome label.

    e.g. 'A. Rejected - grounds not acceptable' -> 'A'
    """
    text = clean_text(label)
    if text is None:
        return None
    parts = text.split(". ", 1)
    if len(parts) < 2:
        return None
    code = parts[0].strip()
    if len(code) == 1:
        return code.upper()
    return None


class DataIngestor:
    """Loads the EC spreadsheet and writes everything into the database."""

    def __init__(self, xlsx_path):
        self.xlsx_path = xlsx_path
        # These get filled by build_records():
        self.courses = set()
        self.modules = {}
        self.students = {}
        self.outcomes = {}
        self.claims = []
        self.updates = {}

    def load_rows(self):
        """Read every data row out of the claims sheet."""
        wb = openpyxl.load_workbook(
            self.xlsx_path, read_only=True, data_only=True,
        )
        sheet = wb[SHEET_CLAIMS]

        # The first two rows of the sheet are header rows so real data
        # starts at row 3 (index 2).
        all_rows = list(sheet.iter_rows(values_only=True))
        data_rows = all_rows[2:]

        rows = []
        for row in data_rows:
            # PostID lives in column G (index 6). Skip blank rows.
            if row[6] is None:
                continue
            rows.append(row)
        return rows

    def build_records(self):
        """Turn the raw spreadsheet rows into data ready for the DB."""
        for row in self.load_rows():
            # Pull out the columns we care about by position.
            post_id = clean_text(row[6])
            posted_date = clean_date(row[7])
            date_approved = clean_date(row[0])
            outcome_label = row[1]
            outcome_code = parse_outcome_code(outcome_label)

            # Student + course info
            course_name = clean_text(row[8])
            student_id = clean_text(row[9])
            year_of_study = row[10]
            if isinstance(year_of_study, str):
                year_of_study = clean_text(year_of_study)
            level_of_student = clean_text(row[11])
            distance_learner = clean_text(row[12])
            tier4_visa = clean_text(row[13])
            support_plan = clean_text(row[14])
            finalist = clean_text(row[40])

            # Claim details
            form_reason = clean_text(row[15])
            affected_from = clean_date(row[16])
            affected_to = clean_date(row[17])
            self_cert_exam = clean_text(row[20])
            module_code = clean_text(row[22])
            module_title = clean_text(row[23])
            type_of_assessment = clean_text(row[24])
            date_of_assessment_affected = clean_date(row[25])
            grounds_reject_reason = clean_text(row[5])
            extension_date = clean_date(row[35])
            latest_notified_date = clean_date(row[36])
            mark_reweighted = clean_text(row[39])
            provisional_notified_date = clean_date(row[41])

            # Admin-trail columns for claim_updates
            campus_end_date = clean_date(row[32])
            campus_added = clean_date(row[33])
            moodle_updated = clean_date(row[34])
            previous_notified_1 = clean_date(row[37])
            previous_notified_2 = clean_date(row[38])
            previous_outcome_1 = clean_text(row[31])
            latest_outcome = clean_text(row[30])

            # Put the values into our dimension collections.
            if course_name is not None:
                self.courses.add(course_name)

            if module_code is not None and module_code not in self.modules:
                self.modules[module_code] = module_title

            if student_id is not None and student_id not in self.students:
                self.students[student_id] = {
                    "course_name": course_name,
                    "year_of_study": year_of_study,
                    "level_of_student": level_of_student,
                    "distance_learner": distance_learner,
                    "tier4_visa": tier4_visa,
                    "support_plan": support_plan,
                    "finalist": finalist,
                }

            if outcome_code is not None and outcome_code not in self.outcomes:
                description = clean_text(outcome_label)
                category = OUTCOME_CATEGORY.get(outcome_code, "Other")
                self.outcomes[outcome_code] = (description, category)

            # Add the fact row for claims.
            self.claims.append((
                post_id, student_id, module_code, outcome_code,
                posted_date, date_approved,
                affected_from, affected_to, date_of_assessment_affected,
                extension_date, type_of_assessment, form_reason,
                grounds_reject_reason, self_cert_exam,
                latest_notified_date, mark_reweighted,
                provisional_notified_date,
            ))

            # Admin trail belongs to the whole form, not the module row,
            # so only keep one copy per PostID.
            if post_id not in self.updates:
                self.updates[post_id] = (
                    post_id, campus_end_date, campus_added, moodle_updated,
                    previous_notified_1, previous_notified_2,
                    previous_outcome_1, latest_outcome,
                )

    def populate(self, db):
        """Write every record into the database."""
        self.build_records()

        # Insert outcomes first.
        outcomes_rows = []
        for code, info in self.outcomes.items():
            description, category = info
            outcomes_rows.append((code, description, category))
        db.executemany(
            "INSERT OR IGNORE INTO outcomes (outcome_code, description, category) "
            "VALUES (?, ?, ?)",
            outcomes_rows,
        )

        # Insert courses.
        courses_rows = [(name,) for name in sorted(self.courses)]
        db.executemany(
            "INSERT OR IGNORE INTO courses (course_name) VALUES (?)",
            courses_rows,
        )

        # Read the course IDs back so we can link students to their course.
        course_lookup = {}
        cur = db.conn.execute("SELECT course_name, course_id FROM courses")
        for name, course_id in cur.fetchall():
            course_lookup[name] = course_id

        # Insert modules.
        modules_rows = []
        for code, title in self.modules.items():
            modules_rows.append((code, title))
        db.executemany(
            "INSERT OR IGNORE INTO modules (module_code, module_title) "
            "VALUES (?, ?)",
            modules_rows,
        )

        # Insert students.
        students_rows = []
        for sid, attrs in self.students.items():
            course_id = course_lookup.get(attrs["course_name"])
            students_rows.append((
                sid,
                course_id,
                attrs["year_of_study"],
                attrs["level_of_student"],
                attrs["distance_learner"],
                attrs["tier4_visa"],
                attrs["support_plan"],
                attrs["finalist"],
            ))
        db.executemany(
            "INSERT OR IGNORE INTO students "
            "(student_id, course_id, year_of_study, level_of_student, "
            "distance_learner, tier4_visa, support_plan, finalist) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            students_rows,
        )

        # Insert claims (the surrogate PK claim_row_id is auto-generated).
        db.executemany(
            "INSERT INTO claims "
            "(claim_id, student_id, module_code, outcome_code, "
            "posted_date, date_approved, when_affected_from, "
            "when_affected_to, date_of_assessment_affected, "
            "extension_date, type_of_assessment, form_reason, "
            "grounds_reject_reason, self_cert_exam, "
            "latest_notified_date, mark_reweighted, "
            "provisional_notified_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            self.claims,
        )

        # Insert claim_updates (one row per PostID).
        updates_rows = list(self.updates.values())
        db.executemany(
            "INSERT OR IGNORE INTO claim_updates "
            "(claim_id, campus_end_date, campus_added, moodle_updated, "
            "previous_notified_1, previous_notified_2, "
            "previous_outcome_1, latest_outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            updates_rows,
        )

    def run(self, db):
        """Convenience method - load + populate in one call."""
        self.populate(db)
