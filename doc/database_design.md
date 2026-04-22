# Database Design

## Overview

The source data is a single Excel sheet (`EC Claims 20-21`) with 43
columns and one row per (form, module) pair. Loading that straight
into one giant table would mean repeating the same student details,
course name and outcome description thousands of times, so instead I
split it into six tables with foreign keys between them.

## ER diagram

```mermaid
erDiagram
    courses     ||--o{ students      : "is enrolled on"
    students    ||--o{ claims        : "submits"
    modules     ||--o{ claims        : "is target of"
    outcomes    ||--o{ claims        : "categorises"
    claims      }|--|| claim_updates : "has admin trail"

    courses {
        int  course_id PK
        text course_name
    }
    students {
        text student_id PK
        int  course_id FK
        int  year_of_study
        text level_of_student
        text distance_learner
        text tier4_visa
        text support_plan
        text finalist
    }
    modules {
        text module_code PK
        text module_title
    }
    outcomes {
        text outcome_code PK
        text description
        text category
    }
    claims {
        int  claim_row_id PK
        text claim_id
        text student_id FK
        text module_code FK
        text outcome_code FK
        text posted_date
        text date_approved
        text when_affected_from
        text when_affected_to
        text date_of_assessment_affected
        text extension_date
        text type_of_assessment
        text form_reason
        text grounds_reject_reason
        text self_cert_exam
        text latest_notified_date
        text mark_reweighted
        text provisional_notified_date
    }
    claim_updates {
        text claim_id PK
        text campus_end_date
        text campus_added
        text moodle_updated
        text previous_notified_1
        text previous_notified_2
        text previous_outcome_1
        text latest_outcome
    }
```

## Why each table is separate

- **courses** - course names are long strings, so I stored them once
  with a surrogate integer `course_id` and pointed each student at
  their course.
- **students** - one student often submits several claims, and their
  attributes (level, finalist, distance learner, visa) are properties
  of the student, not of each claim, so they belong here.
- **modules** - module code and title go together, one row per module.
- **outcomes** - the "Outcome" column in the spreadsheet uses codes A
  to H plus a few numeric codes. I kept them in their own lookup table
  so the analytical SQL can just JOIN on the code and pick up both the
  description and a simpler `category` (Approved / Rejected / Other).
- **claims** - the main table, one row per (form, module). PostID is
  not unique (a single form can list multiple modules), so I used an
  auto-incrementing `claim_row_id` as the primary key and kept
  `claim_id` as a non-unique column.
- **claim_updates** - the admin-trail dates (Campus updated, Moodle
  updated, previous notifications) belong to the whole form, not each
  module row, so I split them out.

## Data-type choices

- Identifiers (`student_id`, `module_code`, `claim_id`) are `TEXT`
  because they aren't numbers (e.g. `FRM00712`, `COMP4031`).
- Dates are stored as ISO text (`YYYY-MM-DD`). SQLite doesn't have a
  real date type, but ISO dates sort correctly and `julianday()` /
  `strftime()` can still work with them.
- `outcomes.category` duplicates information that could be derived
  from `outcome_code`, but storing it saves a `CASE WHEN` in every
  analytical query.

## Running the schema

The schema is in [`src/schema.sql`](../src/schema.sql) and is loaded
by `Database.run_schema()`. The script drops every table first so the
whole pipeline can be re-run without errors.
