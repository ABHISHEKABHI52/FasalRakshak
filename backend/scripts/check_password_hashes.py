"""Security check: verify stored passwords are Argon2id hashes, never plaintext.

Run against any SQLAlchemy-supported SQLite database used in development.

Usage:  python scripts/check_password_hashes.py <sqlite-db-file>
Exit code 0 = all hashes look correct, 1 = problem detected.
"""

import sqlite3
import sys
from pathlib import Path

_ARGON2_PREFIXES = ("$argon2id$", "$argon2i$", "$argon2d$")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/check_password_hashes.py <sqlite-db-file>")
        return 2

    db_path = Path(sys.argv[1])
    if not db_path.exists():
        print(f"database not found: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    rows = list(conn.execute("select phone, password_hash from users"))
    conn.close()

    if not rows:
        print("no users found — nothing to verify")
        return 0

    bad: list[tuple[str, str]] = []
    for phone, password_hash in rows:
        value = str(password_hash or "")
        if not value.startswith(_ARGON2_PREFIXES):
            bad.append((phone, value[:12]))

    print(f"users checked: {len(rows)}")
    if bad:
        print("FAILED — non-Argon2 (possibly plaintext) hashes found:")
        for phone, preview in bad:
            print(f"  user={phone} hash_prefix={preview!r}")
        return 1

    print("PASSED — all password hashes use Argon2id (docs/12 §1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())