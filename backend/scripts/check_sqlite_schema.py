"""Dev utility: prints tables + seeded roles from a SQLite database file.

Usage: python scripts/check_sqlite_schema.py <db-file>
Phase-1 helper only (SQLite dev/validation); production uses PostgreSQL.
"""

import sqlite3
import sys

_TABLES = "select name from sqlite_master where type='table' order by name"


def main() -> None:
    db_path = sys.argv[1] if len(sys.argv) > 1 else "alembic_check.db"
    conn = sqlite3.connect(db_path)
    tables = [row[0] for row in conn.execute(_TABLES)]
    print("tables:", tables)
    if "roles" in tables:
        print("roles:", [tuple(row) for row in conn.execute("select id, name from roles order by id")])
    if "alembic_version" in tables:
        print("alembic_version:", [row[0] for row in conn.execute("select version_num from alembic_version")])
    conn.close()


if __name__ == "__main__":
    main()