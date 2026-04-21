"""
database.py
-----------
A small class that wraps Python's built-in `sqlite3` module so the
rest of the project has one tidy object to talk to.

The class only does five things:
  * open the connection
  * close the connection
  * run the SQL script that creates the tables
  * insert lots of rows in one go (executemany)
  * read a SELECT back as a pandas DataFrame
"""

# We need sqlite3 from the standard library to talk to the database.
import sqlite3

# We need pandas so read_sql can return a tidy DataFrame.
import pandas as pd


class Database:
    """A simple wrapper around an sqlite3 connection."""

    def __init__(self, db_path):
        # Save the path so we know where to open the database file.
        self.db_path = db_path
        # We'll create the connection later in connect().
        self.conn = None

    def connect(self):
        """Open the SQLite connection."""
        # Open (or create) the database file.
        self.conn = sqlite3.connect(self.db_path)
        # Foreign keys are off by default in SQLite, so turn them on.
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Save any pending changes and close the database."""
        # Commit so nothing is lost.
        self.conn.commit()
        # Close the file.
        self.conn.close()

    def run_schema(self, schema_path):
        """Run the SQL file that creates all the tables."""
        # Read the whole .sql file as a single string.
        with open(schema_path) as f:
            sql_script = f.read()
        # executescript runs every statement in the file.
        self.conn.executescript(sql_script)
        # Save changes.
        self.conn.commit()

    def executemany(self, sql, rows):
        """Insert many rows in one transaction."""
        # executemany is faster than calling execute in a loop.
        self.conn.executemany(sql, rows)
        # Save changes.
        self.conn.commit()

    def read_sql(self, sql, params=None):
        """Run a SELECT and return the result as a pandas DataFrame."""
        # If no parameters were given, use an empty dict.
        if params is None:
            params = {}
        # pandas knows how to talk to a sqlite3 connection directly.
        return pd.read_sql_query(sql, self.conn, params=params)

    def scalar(self, sql):
        """Run a SELECT that returns a single number (e.g. COUNT(*))."""
        # execute returns a cursor; fetchone() gives back the first row.
        row = self.conn.execute(sql).fetchone()
        # The number is the first (and only) value in that row.
        return row[0]
