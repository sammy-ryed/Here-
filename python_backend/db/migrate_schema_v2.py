"""
migrate_schema_v2.py — ALTER TABLE migrations for existing PostgreSQL databases.

Run this ONLY if you ran migrate_postgres.py BEFORE the Step 3 schema additions
were included (i.e., you already have the Step 1/2 tables but NOT the Step 3 columns).

If you ran migrate_postgres.py after the Step 3 changes were added, you do NOT
need to run this — the columns already exist.

Usage:
    python db/migrate_schema_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/here')

STATEMENTS = [
    # New tables
    """
    CREATE TABLE IF NOT EXISTS sections (
        id         SERIAL PRIMARY KEY,
        name       TEXT NOT NULL,
        year       INTEGER,
        department TEXT,
        batch      TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id         SERIAL PRIMARY KEY,
        name       TEXT NOT NULL,
        code       TEXT NOT NULL,
        section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS teacher_sections (
        teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
        PRIMARY KEY (teacher_id, section_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id              SERIAL PRIMARY KEY,
        teacher_id      INTEGER NOT NULL REFERENCES users(id),
        section_id      INTEGER NOT NULL REFERENCES sections(id),
        subject_id      INTEGER NOT NULL REFERENCES subjects(id),
        started_at      TIMESTAMP DEFAULT NOW(),
        confirmed_at    TIMESTAMP DEFAULT NULL,
        teacher_gps_lat DOUBLE PRECISION DEFAULT NULL,
        teacher_gps_lon DOUBLE PRECISION DEFAULT NULL,
        status          TEXT NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'confirmed', 'voided')),
        photo_count     INTEGER DEFAULT 0,
        processed_at    TIMESTAMP DEFAULT NULL
    )
    """,
    # New columns on existing tables
    "ALTER TABLE students   ADD COLUMN IF NOT EXISTS section_id INTEGER REFERENCES sections(id)",
    "ALTER TABLE attendance ADD COLUMN IF NOT EXISTS session_id INTEGER REFERENCES sessions(id)",
    # New indexes
    "CREATE INDEX IF NOT EXISTS idx_sessions_teacher ON sessions(teacher_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_section ON sessions(section_id)",
    "CREATE INDEX IF NOT EXISTS idx_subjects_section ON subjects(section_id)",
]


def run():
    print(f"Connecting to: {DATABASE_URL[:40]}...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    for i, stmt in enumerate(STATEMENTS, 1):
        label = stmt.strip()[:60].replace('\n', ' ')
        try:
            cur.execute(stmt)
            print(f"  [{i}/{len(STATEMENTS)}] OK  — {label}")
        except Exception as e:
            print(f"  [{i}/{len(STATEMENTS)}] ERR — {label}\n          {e}")
            conn.close()
            sys.exit(1)

    conn.close()
    print("\n✅ Schema v2 migration complete.")


if __name__ == '__main__':
    run()
