"""
analysis.py - SQL queries for the four assessment questions.

One method on ECAnalyser per question. Each runs a SELECT and returns
a pandas DataFrame so it can be plotted straight away.
"""

import pandas as pd


class ECAnalyser:
    """Run the four analytical questions against the database."""

    def __init__(self, db):
        self.db = db

    def q1_days_before_deadline(self):
        """Q1 - days between submission and the affected assessment date.

        Negative value = submitted before deadline.
        """
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

    def q2_top_modules(self):
        """Q2 - top 15 modules by claim count, broken down by outcome.

        Done in two steps: first get the top 15, then for each of them
        ask how many claims fall into each outcome category.
        """
        # Step 1: the 15 busiest modules.
        top_df = self.db.read_sql(
            "SELECT module_code, COUNT(*) AS total "
            "FROM claims "
            "WHERE module_code IS NOT NULL "
            "GROUP BY module_code "
            "ORDER BY total DESC "
            "LIMIT 15"
        )

        # Step 2: outcome breakdown for each of those 15 modules.
        # We build up a list of dicts and turn it into a DataFrame at
        # the end.
        rows = []
        for code in top_df["module_code"]:
            cur = self.db.conn.execute(
                "SELECT outcomes.category, COUNT(*) "
                "FROM claims "
                "LEFT JOIN outcomes "
                "  ON outcomes.outcome_code = claims.outcome_code "
                "WHERE claims.module_code = ? "
                "GROUP BY outcomes.category",
                (code,),
            )
            for category, count in cur.fetchall():
                rows.append({
                    "module_code": code,
                    "outcome_category": category,
                    "claim_count": count,
                })
        return pd.DataFrame(rows)

    def q3_response_time_by_month(self):
        """Q3 - days from submission to Panel approval, by month posted."""
        sql = """
            SELECT
                strftime('%Y-%m', posted_date) AS posted_month,
                CAST(julianday(date_approved) - julianday(posted_date)
                     AS INTEGER) AS response_days
            FROM claims
            WHERE posted_date IS NOT NULL
              AND date_approved IS NOT NULL
              AND julianday(date_approved) >= julianday(posted_date)
            ORDER BY posted_month
        """
        return self.db.read_sql(sql)

    def q4_outcome_by_assessment_type(self):
        """Q4 - count of claims for each (assessment type, outcome)."""
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

    def run_all(self):
        """Run every question and return the DataFrames in a dict."""
        return {
            "q1": self.q1_days_before_deadline(),
            "q2": self.q2_top_modules(),
            "q3": self.q3_response_time_by_month(),
            "q4": self.q4_outcome_by_assessment_type(),
        }
