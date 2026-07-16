import os
import sys

import psycopg


def get_database_url():
    """Return DATABASE_URL or exit loudly. NEVER fall back to a local default.

    The silent fallback to `dbname=trailsearch` was the bug that loaded 388
    rows into local Postgres while a remote DB stayed empty. Fail fast instead.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit(
            "ERROR: DATABASE_URL is not set.\n"
            "Export your Postgres connection string before running, e.g.:\n"
            '  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"\n'
            "Refusing to fall back to a local database."
        )
    return url


def connect():
    """Open a psycopg connection to the database named by DATABASE_URL."""
    return psycopg.connect(get_database_url())
