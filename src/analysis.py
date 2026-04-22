"""
SQL queries for the four questions.

Each method on ECAnalyser runs one SELECT and returns a pandas
DataFrame so plots.py can draw it.
"""

import pandas as pd


class ECAnalyser:

    def __init__(self, db):
        self.db = db

    def q1_days_before_deadline(self):
        """How many days before or after the deadline each claim was filed.

        A negative number means the claim was filed before the deadline.
        """
        sql = (
            "SELECT claims.claim_id, "
            " CAST(julianday(claims.posted_date) "
            "      - julianday(claims.date_of_assessment_affected) AS INTEGER)"
            "   AS days_after_deadline, "
            " outcomes.category AS outcome_category "
            "FROM claims "
            "LEFT JOIN outcomes ON outcomes.outcome_code = claims.outcome_code "
            "WHERE claims.posted_date IS NOT NULL "
            "  AND claims.date_of_assessment_affected IS NOT NULL"
        )
        return self.db.read_sql(sql)

    def q2_top_modules(self):
        """Find the 15 busiest modules and their outcome breakdown.

        Done in two steps: one query to get the top 15 module codes,
        then a query per module for its outcome counts.
        """
        top_df = self.db.read_sql(
            "SELECT module_code, COUNT(*) AS total "
            "FROM claims "
            "WHERE module_code IS NOT NULL "
            "GROUP BY module_code "
            "ORDER BY total DESC "
            "LIMIT 15"
        )

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
        """Panel response time (days) grouped by month of submission."""
        sql = (
            "SELECT strftime('%Y-%m', posted_date) AS posted_month, "
            " CAST(julianday(date_approved) - julianday(posted_date) "
            "      AS INTEGER) AS response_days "
            "FROM claims "
            "WHERE posted_date IS NOT NULL "
            "  AND date_approved IS NOT NULL "
            "  AND julianday(date_approved) >= julianday(posted_date) "
            "ORDER BY posted_month"
        )
        return self.db.read_sql(sql)

    def q4_outcome_by_assessment_type(self):
        """Count of claims grouped by assessment type and outcome."""
        sql = (
            "SELECT claims.type_of_assessment, "
            " outcomes.category AS outcome_category, "
            " COUNT(*) AS claim_count "
            "FROM claims "
            "LEFT JOIN outcomes ON outcomes.outcome_code = claims.outcome_code "
            "WHERE claims.type_of_assessment IS NOT NULL "
            "GROUP BY claims.type_of_assessment, outcomes.category "
            "ORDER BY claims.type_of_assessment, outcomes.category"
        )
        return self.db.read_sql(sql)

    def run_all(self):
        """Run every question and collect the results in a dict."""
        return {
            "q1": self.q1_days_before_deadline(),
            "q2": self.q2_top_modules(),
            "q3": self.q3_response_time_by_month(),
            "q4": self.q4_outcome_by_assessment_type(),
        }
