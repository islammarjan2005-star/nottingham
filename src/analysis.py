"""
analysis.py
-----------
SQL queries for the four assessment questions.

We use a class with one method per question. Each method runs a single
SQL SELECT against the database and returns the result as a pandas
DataFrame, ready to be plotted in plots.py.
"""

# We need pandas to glue several small DataFrames together in Q2.
import pandas as pd


class ECAnalyser:
    """Run the four analytical questions."""

    def __init__(self, db):
        # Save the Database object so the methods can use it.
        self.db = db

    # -----------------------------------------------------------------
    # Q1 - Do EC claims cluster around assessment deadlines?
    # -----------------------------------------------------------------
    def q1_days_before_deadline(self):
        """How many days before/after the deadline is each claim filed?"""
        # julianday() turns a date into a Julian day number, so
        # subtracting two of them gives a difference in days.
        # A negative value means the claim was filed before the deadline.
        sql = """
            SELECT
                claims.claim_id,
                CAST(julianday(claims.posted_date)
                     - julianday(claims.date_of_assessment_affected)
                     AS INTEGER) AS days_after_deadline,
                outcomes.category AS outcome_category
            FROM claims
            LEFT JOIN outcomes ON outcomes.outcome_code = claims.outcome_code
            WHERE claims.posted_date IS NOT NULL
              AND claims.date_of_assessment_affected IS NOT NULL
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Q2 - Which modules attract the most EC claims?
    # -----------------------------------------------------------------
    def q2_top_modules(self):
        """Top 15 modules by claim count, broken down by outcome.

        We do this in two steps so the SQL stays simple:
          1. Find the 15 module codes with the most claims.
          2. For each module, ask for its outcome breakdown.
        """
        # Step 1 - get the top 15 module codes.
        top_df = self.db.read_sql(
            "SELECT module_code, COUNT(*) AS total "
            "FROM claims "
            "WHERE module_code IS NOT NULL "
            "GROUP BY module_code "
            "ORDER BY total DESC "
            "LIMIT 15"
        )

        # Step 2 - loop over those modules and ask for each one.
        all_breakdowns = []
        for code in top_df["module_code"]:
            per_module = self.db.read_sql(
                "SELECT outcomes.category AS outcome_category, "
                "       COUNT(*) AS claim_count "
                "FROM claims "
                "LEFT JOIN outcomes "
                "  ON outcomes.outcome_code = claims.outcome_code "
                "WHERE claims.module_code = ? "
                "GROUP BY outcomes.category",
                params=(code,),
            )
            # Add the module code so we know which rows belong to which.
            per_module["module_code"] = code
            all_breakdowns.append(per_module)

        # Stick the small DataFrames together into one big one.
        return pd.concat(all_breakdowns, ignore_index=True)

    # -----------------------------------------------------------------
    # Q3 - How does the Panel response time vary across the year?
    # -----------------------------------------------------------------
    def q3_response_time_by_month(self):
        """Days from posting to Panel approval, grouped by month."""
        sql = """
            SELECT
                strftime('%Y-%m', posted_date) AS posted_month,
                CAST(julianday(date_approved)
                     - julianday(posted_date) AS INTEGER) AS response_days
            FROM claims
            WHERE posted_date IS NOT NULL
              AND date_approved IS NOT NULL
              AND julianday(date_approved) >= julianday(posted_date)
            ORDER BY posted_month
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Q4 - How does the outcome differ by type of assessment?
    # -----------------------------------------------------------------
    def q4_outcome_by_assessment_type(self):
        """Count of claims for each (assessment type, outcome category)."""
        sql = """
            SELECT
                claims.type_of_assessment,
                outcomes.category AS outcome_category,
                COUNT(*) AS claim_count
            FROM claims
            LEFT JOIN outcomes ON outcomes.outcome_code = claims.outcome_code
            WHERE claims.type_of_assessment IS NOT NULL
            GROUP BY claims.type_of_assessment, outcomes.category
            ORDER BY claims.type_of_assessment, outcomes.category
        """
        return self.db.read_sql(sql)

    # -----------------------------------------------------------------
    # Convenience: run every query and return them in a dict.
    # -----------------------------------------------------------------
    def run_all(self):
        """Run every question and return the DataFrames in a dict."""
        return {
            "q1": self.q1_days_before_deadline(),
            "q2": self.q2_top_modules(),
            "q3": self.q3_response_time_by_month(),
            "q4": self.q4_outcome_by_assessment_type(),
        }
