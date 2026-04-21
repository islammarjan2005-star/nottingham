"""
database.py
-----------
A very small wrapper around the standard library ``sqlite3`` module.
We use a class so that the rest of the project has a single, named
object representing "the database", which is tidier than passing a raw
connection around.

The class is deliberately kept short: just enough to open / close the
connection, run the schema script, and execute parameterised SQL.
"""

# Standard library imports.
import sqlite3
from pathlib import Path

# Project imports.
import pandas as pd


class Database:
    """A thin wrapper around an sqlite3 connection.

    Usage::

        db = Database("data/ec_claims.db")
        db.connect()
        db.run_schema("src/schema.sql")
        db.executemany("INSERT INTO modules VALUES (?, ?)", rows)
        df = db.read_sql("SELECT * FROM claims")
        db.close()

    The class also supports the ``with`` statement so the connection is
    closed automatically.
    """

    def __init__(self, db_path):
        # Store the path as a Path object for convenience.
        self.db_path = Path(db_path)
        # The sqlite3 connection is created lazily in connect().
        self.conn = None

    # ----- context manager helpers ----------------------------------
    def __enter__(self):
        # Allow `with Database(path) as db:` style usage.
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        # Always close the connection, even if an exception happened.
        self.close()

    # ----- connection management ------------------------------------
    def connect(self):
        """Open the SQLite connection and turn on foreign-key support."""
        # Make sure the parent directory exists - sqlite3 will not create
        # missing folders for us.
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Open the connection. detect_types is set so that DATE/TIMESTAMP
        # columns come back as Python objects when needed.
        self.conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # Foreign keys are off by default in SQLite; enable them.
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self):
        """Close the SQLite connection if it is open."""
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    # ----- schema and bulk inserts ----------------------------------
    def run_schema(self, schema_path):
        """Execute the SQL script that creates all tables."""
        # Read the .sql file as text...
        sql_text = Path(schema_path).read_text(encoding="utf-8")
        # ...and run every statement in it.
        self.conn.executescript(sql_text)
        self.conn.commit()

    def executemany(self, sql, rows):
        """Run a parameterised INSERT for many rows in one transaction."""
        # Using executemany inside a single commit is much faster than
        # calling execute() in a Python loop.
        self.conn.executemany(sql, rows)
        self.conn.commit()

    # ----- querying --------------------------------------------------
    def read_sql(self, sql, params=None):
        """Run a SELECT and return the result as a pandas DataFrame.

        We use pandas here because every analysis in this project
        ultimately wants tabular data for plotting.
        """
        return pd.read_sql_query(sql, self.conn, params=params or {})

    def scalar(self, sql, params=None):
        """Run a SELECT that returns a single value (e.g. COUNT(*))."""
        cur = self.conn.execute(sql, params or [])
        row = cur.fetchone()
        return row[0] if row else None
