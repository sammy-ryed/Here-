"""
migrate_postgres.py — Create ALL PostgreSQL tables for the HERE backend.

Covers:
  Step 1: students, embeddings, attendance, registration_tokens
  Step 2: users
  Step 3: sections, subjects, teacher_sections, sessions
         + section_id FK on students, session_id FK on attendance

Run once (idempotent — uses IF NOT EXISTS):
    python db/migrate_postgres.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/here')

DDL = [
    # ── Step 2: users (referenced by teacher_sections, sessions) ─────────────
    """
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        username      TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL CHECK (role IN ('admin', 'teacher')),
        created_at    TIMESTAMP DEFAULT NOW()
    )
    """,

    # ── Step 3: sections ──────────────────────────────────────────────────────
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

    # ── Step 1: students ──────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS students (
        id             SERIAL PRIMARY KEY,
        name           TEXT NOT NULL,
        roll_no        TEXT UNIQUE NOT NULL,
        embedding      BYTEA,
        embedding_json TEXT,
        created_at     TIMESTAMP DEFAULT NOW(),
        section        TEXT DEFAULT NULL,
        course         TEXT DEFAULT NULL,
        dept           TEXT DEFAULT NULL,
        room_no        TEXT DEFAULT NULL,
        email          TEXT DEFAULT NULL,
        section_id     INTEGER REFERENCES sections(id)
    )
    """,

    # ── Step 1: embeddings ────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS embeddings (
        id             SERIAL PRIMARY KEY,
        student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        embedding      BYTEA NOT NULL,
        embedding_json TEXT,
        created_at     TIMESTAMP DEFAULT NOW()
    )
    """,

    # ── Step 1: registration_tokens ───────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS registration_tokens (
        token      TEXT PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        expires_at TIMESTAMP NOT NULL,
        used_at    TIMESTAMP DEFAULT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,

    # ── Step 3: subjects ──────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id         SERIAL PRIMARY KEY,
        name       TEXT NOT NULL,
        code       TEXT NOT NULL,
        section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,

    # ── Step 3: teacher_sections ──────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS teacher_sections (
        teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
        PRIMARY KEY (teacher_id, section_id)
    )
    """,

    # ── Step 3: sessions ──────────────────────────────────────────────────────
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

    # ── Step 1: attendance (session_id added here so it references sessions) ──
    """
    CREATE TABLE IF NOT EXISTS attendance (
        id         SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        date       TEXT NOT NULL,
        status     TEXT NOT NULL,
        confidence REAL DEFAULT NULL,
        timestamp  TIMESTAMP DEFAULT NOW(),
        session_id INTEGER REFERENCES sessions(id),
        UNIQUE(student_id, date)
    )
    """,

    # ── Indexes ───────────────────────────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_roll_no           ON students(roll_no)",
    "CREATE INDEX IF NOT EXISTS idx_student_id        ON embeddings(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_attendance_date   ON attendance(date)",
    "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_token_student     ON registration_tokens(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_teacher  ON sessions(teacher_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_section  ON sessions(section_id)",
    "CREATE INDEX IF NOT EXISTS idx_subjects_section  ON subjects(section_id)",
]


def run():
    print("⚠️  Connecting to Supabase PostgreSQL — make sure your IP is allowlisted in")
    print("    Supabase Dashboard → Settings → Database → Network")
    print(f"Connecting to: {DATABASE_URL[:40]}...")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    conn.autocommit = True
    cur = conn.cursor()

    for i, statement in enumerate(DDL, 1):
        stmt = statement.strip()
        label = stmt.split('\n')[0][:60]
        try:
            cur.execute(stmt)
            print(f"  [{i}/{len(DDL)}] OK  — {label}")
        except Exception as e:
            print(f"  [{i}/{len(DDL)}] ERR — {label}\n          {e}")
            conn.close()
            sys.exit(1)

    conn.close()
    print("\n✅ Migration complete — all tables and indexes created.")


if __name__ == '__main__':
    run()
