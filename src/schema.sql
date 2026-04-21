-- =====================================================================
-- schema.sql
-- ZDAT1001 Portfolio Part 2 - normalised SQLite schema for the EC dataset
-- =====================================================================
-- The schema is split into three small dimension tables (courses,
-- modules, outcomes), one student dimension table, and one main fact
-- table (claims). This avoids repeating long course names or outcome
-- descriptions in every claim row, making the database smaller and the
-- analytical SQL easier to read.
-- ---------------------------------------------------------------------

-- Foreign keys are off by default in SQLite, so turn them on.
PRAGMA foreign_keys = ON;

-- Drop everything first so the script can be re-run safely.
DROP TABLE IF EXISTS claim_updates;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS outcomes;

-- ---------------------------------------------------------------------
-- DIMENSION: courses
-- One row per distinct course name in the source spreadsheet.
-- We use an INTEGER surrogate key because the original course names are
-- long strings with trailing whitespace - storing them once is tidier.
-- ---------------------------------------------------------------------
CREATE TABLE courses (
    course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT    NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- DIMENSION: modules
-- One row per module code (e.g. "COMP4031"). Module title may be NULL
-- because the source data sometimes leaves it blank.
-- ---------------------------------------------------------------------
CREATE TABLE modules (
    module_code  TEXT PRIMARY KEY,
    module_title TEXT
);

-- ---------------------------------------------------------------------
-- DIMENSION: outcomes
-- Lookup table for the Quality Manual outcome letters used in column B
-- of the source spreadsheet (e.g. "A", "G", "H"). The descriptions come
-- from the "Data validation" sheet of the workbook.
-- ---------------------------------------------------------------------
CREATE TABLE outcomes (
    outcome_code TEXT PRIMARY KEY,         -- e.g. "A", "G", "H", "4"
    description  TEXT NOT NULL,            -- human-readable label
    category     TEXT NOT NULL             -- "Approved" / "Rejected" / "Other"
);

-- ---------------------------------------------------------------------
-- DIMENSION: students
-- One row per anonymised student ID. The source row also carries a few
-- attributes (level, year, distance learner flag) that we attach here so
-- that they are not duplicated in every claim made by that student.
-- ---------------------------------------------------------------------
CREATE TABLE students (
    student_id        TEXT    PRIMARY KEY,
    course_id         INTEGER REFERENCES courses(course_id),
    year_of_study     INTEGER,
    level_of_student  TEXT,
    distance_learner  TEXT,                -- "Yes" / "No"
    tier4_visa        TEXT,                -- "Yes" / "No"
    support_plan      TEXT,                -- "Yes" / "No"
    finalist          TEXT                 -- "Yes" / "No"
);

-- ---------------------------------------------------------------------
-- FACT: claims
-- One row per (submitted form, module) pair from "EC Claims 20-21".
-- A single form (PostID) can list several affected modules, so PostID
-- is *not* unique; we use a surrogate INTEGER primary key instead.
-- Dates are stored as ISO TEXT (YYYY-MM-DD) so SQLite's julianday() and
-- strftime() functions work directly on them.
-- ---------------------------------------------------------------------
CREATE TABLE claims (
    claim_row_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id                    TEXT    NOT NULL,               -- PostID (not unique)
    student_id                  TEXT    REFERENCES students(student_id),
    module_code                 TEXT    REFERENCES modules(module_code),
    outcome_code                TEXT    REFERENCES outcomes(outcome_code),
    posted_date                 TEXT,                           -- when student submitted
    date_approved               TEXT,                           -- when Panel decided
    when_affected_from          TEXT,                           -- start of impact
    when_affected_to            TEXT,                           -- end of impact
    date_of_assessment_affected TEXT,                           -- assessment deadline / exam date
    extension_date              TEXT,                           -- granted extension (if any)
    type_of_assessment          TEXT,                           -- "Coursework" / "Exam" / etc.
    form_reason                 TEXT,                           -- "Why is the form being completed"
    grounds_reject_reason       TEXT,                           -- only for rejections
    self_cert_exam              TEXT,                           -- self-certified exam absence?
    latest_notified_date        TEXT,                           -- most recent date student notified
    mark_reweighted             TEXT,                           -- May/June reweighting flag
    provisional_notified_date   TEXT
);

-- ---------------------------------------------------------------------
-- ASSOCIATIVE: claim_updates
-- Optional one-to-one extension of "claims" that holds the
-- administrative timeline columns ("Campus updated...", "Moodle
-- updated...", previous notification dates). Splitting these out keeps
-- the main claims table focused on claim attributes and lets us answer
-- "did the system get updated?" questions in isolation.
-- ---------------------------------------------------------------------
CREATE TABLE claim_updates (
    claim_id              TEXT PRIMARY KEY,                     -- = PostID
    campus_end_date       TEXT,
    campus_added          TEXT,
    moodle_updated        TEXT,
    previous_notified_1   TEXT,
    previous_notified_2   TEXT,
    previous_outcome_1    TEXT,
    latest_outcome        TEXT
);

-- ---------------------------------------------------------------------
-- Helpful indexes for the analytical queries used in src/analysis.py.
-- ---------------------------------------------------------------------
CREATE INDEX idx_claims_module   ON claims(module_code);
CREATE INDEX idx_claims_outcome  ON claims(outcome_code);
CREATE INDEX idx_claims_posted   ON claims(posted_date);
CREATE INDEX idx_claims_form     ON claims(claim_id);
