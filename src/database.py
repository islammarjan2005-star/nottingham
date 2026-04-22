"""Small class that wraps the sqlite3 connection so the other files
don't have to worry about it."""

import sqlite3
import pandas as pd


class Database:
    """Wraps an sqlite3 connection."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        # Turn foreign keys on - they are off by default in sqlite.
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        self.conn.commit()
        self.conn.close()

    def run_schema(self, schema_path):
        """Run the CREATE TABLE script."""
        with open(schema_path) as f:
            sql = f.read()
        self.conn.executescript(sql)
        self.conn.commit()

    def executemany(self, sql, rows):
        """Insert lots of rows in one go. Faster than a loop."""
        self.conn.executemany(sql, rows)
        self.conn.commit()

    def read_sql(self, sql, params=None):
        """Run a SELECT and return the result as a pandas DataFrame."""
        if params is None:
            params = {}
        return pd.read_sql_query(sql, self.conn, params=params)

    def scalar(self, sql):
        """Run a SELECT that returns one value (e.g. COUNT(*))."""
        row = self.conn.execute(sql).fetchone()
        return row[0]
