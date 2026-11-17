#!/bin/sh
# Start the API and prove the shipped database is readable.
#
# The container is read-only at runtime, so the database must open without
# needing to create any side-car file. If it cannot, the service must fail
# loudly instead of serving an empty tool.
set -eu

DB="${PARLAMENT_DB:-/app/data/parlament.db}"

if [ ! -f "$DB" ]; then
	echo "FATAL: no database at $DB - the image was built without data" >&2
	exit 1
fi

python - "$DB" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
# Read the SQLite header bytes directly: bytes 18/19 are the file format
# write/read version. (2, 2) means WAL mode, which needs -wal/-shm side-cars
# and cannot be opened on the read-only runtime filesystem. Using a raw
# header read avoids sqlite3 creating those side-cars during the check.
with open(path, "rb") as fh:
    header = fh.read(100)
if header[:16] != b"SQLite format 3\x00":
    raise SystemExit("FATAL: not a SQLite database")
if header[18] == 2 or header[19] == 2:
    raise SystemExit(
        "FATAL: shipped database is in WAL mode — run scripts/prepare_db.py "
        "before publishing the release (journal_mode must be DELETE)"
    )
conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
try:
    status = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if status != "ok":
        raise SystemExit(f"FATAL: database integrity check failed: {status}")
    tables = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    people = conn.execute("SELECT count(*) FROM person").fetchone()[0]
    memberships = conn.execute("SELECT count(*) FROM membership").fetchone()[0]
finally:
    conn.close()
print(f"database ok: {tables} tables, {people} persons, {memberships} memberships")
PY

exec "$@"
