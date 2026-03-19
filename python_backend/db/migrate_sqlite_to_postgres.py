"""
migrate_sqlite_to_postgres.py — One-time data migration from SQLite → PostgreSQL.

Reads every row from db/attendance.db and upserts into PostgreSQL.
Covers all 4 original tables: students, embeddings, attendance, registration_tokens.

Safe to re-run: uses ON CONFLICT DO NOTHING / DO UPDATE where appropriate.
Prints per-table row counts before and after.

Usage:
    python db/migrate_sqlite_to_postgres.py

Run AFTER migrate_postgres.py (tables must exist in Postgres already).
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.environ.get('SQLITE_PATH', os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'db', 'attendance.db'
))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/here')


def pg_count(pg_cur, table: str) -> int:
    pg_cur.execute(f'SELECT COUNT(*) FROM {table}')
    return pg_cur.fetchone()[0]


def migrate():
    print("⚠️  Connecting to Supabase PostgreSQL — make sure your IP is allowlisted in")
    print("    Supabase Dashboard → Settings → Database → Network")
    print(f"Source (SQLite) : {SQLITE_PATH}")
    print(f"Target (Postgres): {DATABASE_URL[:40]}...\n")

    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: SQLite file not found at {SQLITE_PATH}")
        sys.exit(1)

    sq = sqlite3.connect(SQLITE_PATH)
    sq.row_factory = sqlite3.Row
    sq_cur = sq.cursor()

    pg = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor, sslmode='require')
    pg_cur = pg.cursor()

    total_migrated = 0

    # ── 1. students ───────────────────────────────────────────────────────────
    print("── students ──")
    sq_cur.execute("SELECT * FROM students")
    sq_rows = sq_cur.fetchall()
    before = pg_count(pg_cur, 'students')
    print(f"  SQLite rows : {len(sq_rows)}")
    print(f"  PG rows before: {before}")

    for r in sq_rows:
        pg_cur.execute(
            '''
            INSERT INTO students
                (id, name, roll_no, embedding, embedding_json, created_at,
                 section, course, dept, room_no, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            ''',
            (
                r['id'], r['name'], r['roll_no'],
                bytes(r['embedding']) if r['embedding'] else None,
                r['embedding_json'],
                r['created_at'],
                r['section'] if 'section' in r.keys() else None,
                r['course'] if 'course' in r.keys() else None,
                r['dept'] if 'dept' in r.keys() else None,
                r['room_no'] if 'room_no' in r.keys() else None,
                r['email'] if 'email' in r.keys() else None,
            )
        )
    pg.commit()
    after = pg_count(pg_cur, 'students')
    inserted = after - before
    total_migrated += inserted
    print(f"  Inserted    : {inserted}  |  PG rows after: {after}\n")

    # Reset sequence so new inserts don't clash with migrated IDs
    pg_cur.execute("SELECT setval('students_id_seq', (SELECT MAX(id) FROM students))")
    pg.commit()

    # ── 2. embeddings ─────────────────────────────────────────────────────────
    print("── embeddings ──")
    sq_cur.execute("SELECT * FROM embeddings")
    sq_rows = sq_cur.fetchall()
    before = pg_count(pg_cur, 'embeddings')
    print(f"  SQLite rows : {len(sq_rows)}")
    print(f"  PG rows before: {before}")

    for r in sq_rows:
        pg_cur.execute(
            '''
            INSERT INTO embeddings (id, student_id, embedding, embedding_json, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            ''',
            (
                r['id'], r['student_id'],
                bytes(r['embedding']) if r['embedding'] else None,
                r['embedding_json'] if 'embedding_json' in r.keys() else None,
                r['created_at'],
            )
        )
    pg.commit()
    after = pg_count(pg_cur, 'embeddings')
    inserted = after - before
    total_migrated += inserted
    print(f"  Inserted    : {inserted}  |  PG rows after: {after}\n")

    pg_cur.execute("SELECT setval('embeddings_id_seq', GREATEST((SELECT COALESCE(MAX(id),1) FROM embeddings), 1))")
    pg.commit()

    # ── 3. attendance ─────────────────────────────────────────────────────────
    print("── attendance ──")
    sq_cur.execute("SELECT * FROM attendance")
    sq_rows = sq_cur.fetchall()
    before = pg_count(pg_cur, 'attendance')
    print(f"  SQLite rows : {len(sq_rows)}")
    print(f"  PG rows before: {before}")

    for r in sq_rows:
        pg_cur.execute(
            '''
            INSERT INTO attendance (id, student_id, date, status, confidence, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            ''',
            (
                r['id'], r['student_id'], r['date'], r['status'],
                r['confidence'] if 'confidence' in r.keys() else None,
                r['timestamp'],
            )
        )
    pg.commit()
    after = pg_count(pg_cur, 'attendance')
    inserted = after - before
    total_migrated += inserted
    print(f"  Inserted    : {inserted}  |  PG rows after: {after}\n")

    pg_cur.execute("SELECT setval('attendance_id_seq', GREATEST((SELECT COALESCE(MAX(id),1) FROM attendance), 1))")
    pg.commit()

    # ── 4. registration_tokens ────────────────────────────────────────────────
    print("── registration_tokens ──")
    sq_cur.execute("SELECT * FROM registration_tokens")
    sq_rows = sq_cur.fetchall()
    before = pg_count(pg_cur, 'registration_tokens')
    print(f"  SQLite rows : {len(sq_rows)}")
    print(f"  PG rows before: {before}")

    for r in sq_rows:
        pg_cur.execute(
            '''
            INSERT INTO registration_tokens (token, student_id, expires_at, used_at, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (token) DO NOTHING
            ''',
            (r['token'], r['student_id'], r['expires_at'],
             r['used_at'], r['created_at'])
        )
    pg.commit()
    after = pg_count(pg_cur, 'registration_tokens')
    inserted = after - before
    total_migrated += inserted
    print(f"  Inserted    : {inserted}  |  PG rows after: {after}\n")

    sq.close()
    pg_cur.close()
    pg.close()

    print(f"✅ Migration complete — {total_migrated} total rows inserted across 4 tables.")


if __name__ == '__main__':
    migrate()
