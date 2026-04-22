-- schema.sql
-- Tables for the EC claims database.
-- There are 6 tables: courses, modules, outcomes and students are the
-- "dimension" tables, claims is the main table and claim_updates holds
-- extra admin info per form.

-- Drop everything first so we can re-run the script without errors.
DROP TABLE IF EXISTS claim_updates;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS outcomes;


-- Courses: one row per distinct course name from the spreadsheet.
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL UNIQUE
);


-- Modules: one row per module code.
CREATE TABLE modules (
    module_code TEXT PRIMARY KEY,
    module_title TEXT
);


-- Outcomes: lookup table for the Quality Manual codes (A, B, G, H etc).
-- Category groups them into Approved / Rejected / Other for plotting.
CREATE TABLE outcomes (
    outcome_code TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    category TEXT NOT NULL
);


-- Students: one row per student id.
CREATE TABLE students (
    student_id TEXT PRIMARY KEY,
    course_id INTEGER REFERENCES courses(course_id),
    year_of_study INTEGER,
    level_of_student TEXT,
    distance_learner TEXT,
    tier4_visa TEXT,
    support_plan TEXT,
    finalist TEXT
);


-- Claims: the main table. One row per (form, module) because a single
-- form can list several modules. Dates are stored as 'YYYY-MM-DD' text.
CREATE TABLE claims (
    claim_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    student_id TEXT REFERENCES students(student_id),
    module_code TEXT REFERENCES modules(module_code),
    outcome_code TEXT REFERENCES outcomes(outcome_code),
    posted_date TEXT,
    date_approved TEXT,
    when_affected_from TEXT,
    when_affected_to TEXT,
    date_of_assessment_affected TEXT,
    extension_date TEXT,
    type_of_assessment TEXT,
    form_reason TEXT,
    grounds_reject_reason TEXT,
    self_cert_exam TEXT,
    latest_notified_date TEXT,
    mark_reweighted TEXT,
    provisional_notified_date TEXT
);


-- claim_updates: extra admin dates keyed by PostID (the form id).
CREATE TABLE claim_updates (
    claim_id TEXT PRIMARY KEY,
    campus_end_date TEXT,
    campus_added TEXT,
    moodle_updated TEXT,
    previous_notified_1 TEXT,
    previous_notified_2 TEXT,
    previous_outcome_1 TEXT,
    latest_outcome TEXT
);
