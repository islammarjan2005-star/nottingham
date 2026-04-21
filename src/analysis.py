"""
analysis.py
-----------
Pure-SQL analytical queries for the four assessment questions.

Each method on ``ECAnalyser`` runs one SQL statement against the SQLite
database and returns a pandas DataFrame ready for plotting. Keeping the
SQL in named methods (rather than scattered through scripts) makes it
easy to re-use the same query in the EDA notebook and in the report
pipeline.
"""

# Project imports.
from database import Database


class ECAnalyser:
    """Run the four analytical questions defined in REPORT.md."""

    def __init__(self, db):
        # The constructor just stores a reference to an open Database.
        self.db = db

    # -----------------------------------------------------------------
    # Q1 - Do EC claims cluster around assessment deadlines?
    # -----------------------------------------------------------------
    def q1_days_before_deadline(self):
        """Days between claim submission and the affected assessment date.

        A negative value means the claim was submitted **before** the
        deadline (the usual case). A positive value means the claim was
        submitted **after** the deadline (often a self-certified late
        submission). The query also returns the outcome category so the
        plot can split the distribution by approved vs. rejected.
        """
        sql = """
            SELECT
                c.claim_id,
                CAST(julianday(c.posted_date)
                     - julianday(c.date_of_assessment_affected) AS INTEGER)
                    AS days_after_deadline,
                COALESCE(o.category, 'Unknown') AS outcome_category
            FROM claims c
            LEFT JOIN outcomes o ON o.outcome_code = c.outcome_code
            WHERE c.posted_date IS NOT NULL
              AND c.date_of_assessment_affected IS NOT NULL
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Q2 - Which modules attract the most EC claims?
    # -----------------------------------------------------------------
    def q2_top_modules(self, top_n=15):
        """Top ``top_n`` modules by claim count, broken down by outcome."""
        sql = """
            WITH counts AS (
                SELECT module_code, COUNT(*) AS total
                FROM claims
                WHERE module_code IS NOT NULL
                GROUP BY module_code
                ORDER BY total DESC
                LIMIT :top_n
            )
            SELECT
                m.module_code,
                COALESCE(m.module_title, m.module_code) AS module_title,
                COALESCE(o.category, 'Unknown') AS outcome_category,
                COUNT(c.claim_id) AS claim_count
            FROM counts cn
            JOIN modules  m ON m.module_code   = cn.module_code
            JOIN claims   c ON c.module_code   = cn.module_code
            LEFT JOIN outcomes o ON o.outcome_code = c.outcome_code
            GROUP BY m.module_code, outcome_category
            ORDER BY (
                SELECT total FROM counts WHERE module_code = m.module_code
            ) DESC, outcome_category
        """
        # Note: pandas read_sql_query handles named ":param" placeholders
        # for SQLite.
        return self.db.read_sql(sql, params={"top_n": top_n})

    # -----------------------------------------------------------------
    # Q3 - How does the Panel response time change over the year?
    #      (additional question for C-band)
    # -----------------------------------------------------------------
    def q3_response_time_by_month(self):
        """Days between submission and Panel decision, grouped by month."""
        sql = """
            SELECT
                strftime('%Y-%m', posted_date) AS posted_month,
                CAST(julianday(date_approved)
                     - julianday(posted_date) AS INTEGER)
                    AS response_days
            FROM claims
            WHERE posted_date IS NOT NULL
              AND date_approved IS NOT NULL
              AND julianday(date_approved) >= julianday(posted_date)
            ORDER BY posted_month
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Q4 - Approval rate by student level / finalist status.
    # -----------------------------------------------------------------
    def q4_outcome_by_assessment_type(self):
        """Outcome breakdown for each type of assessment.

        Coursework, examinations and the smaller categories (in-class
        tests, presentations, dissertation, placement) attract claims
        in very different volumes. This query returns one row per
        (assessment type, outcome category) so the plot can show both
        the total claim volume and the approval rate side-by-side.
        """
        sql = """
            SELECT
                COALESCE(c.type_of_assessment, 'Unknown')
                    AS type_of_assessment,
                COALESCE(o.category, 'Unknown') AS outcome_category,
                COUNT(*) AS claim_count
            FROM claims c
            LEFT JOIN outcomes o ON o.outcome_code = c.outcome_code
            WHERE c.type_of_assessment IS NOT NULL
            GROUP BY type_of_assessment, outcome_category
            ORDER BY type_of_assessment, outcome_category
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Convenience: a small dictionary returned by run_all() so that the
    # report-builder code does not have to call each method by name.
    # -----------------------------------------------------------------
    def run_all(self):
        return {
            "q1": self.q1_days_before_deadline(),
            "q2": self.q2_top_modules(),
            "q3": self.q3_response_time_by_month(),
            "q4": self.q4_outcome_by_assessment_type(),
        }
