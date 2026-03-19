"""
Database management for student records and attendance.
Migrated from SQLite to PostgreSQL using psycopg2.
OPTIMIZED: Caching for frequently accessed data.

# NOTE: All public method signatures are identical to the original SQLite version —
# app.py requires zero changes for Step 1.
"""

import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from functools import lru_cache

import numpy as np
import psycopg2
import psycopg2.errors
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/here')


class Database:
    """Database handler for attendance system with caching."""

    def __init__(self, db_path=None):
        """
        Initialize the database connection.
        `db_path` is accepted for backward compatibility but ignored —
        the connection string comes from DATABASE_URL in .env.
        """
        self.dsn = _DATABASE_URL
        self.init_database()
        logger.info("Database initialized (PostgreSQL) with caching enabled")

    # ── Connection ────────────────────────────────────────────────────────────

    def get_connection(self):
        """Return a new psycopg2 connection with RealDictCursor factory.
        sslmode='require' is mandatory for Supabase (and harmless for local PG).
        """
        return psycopg2.connect(
            self.dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode='require',
        )

    def is_connected(self) -> bool:
        """Check that the database is reachable."""
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    # ── Schema ────────────────────────────────────────────────────────────────

    def init_database(self):
        """
        Create core tables if they don't exist (idempotent).
        The full schema (including Step 2/3 tables) is managed by
        db/migrate_postgres.py; this method only ensures the tables that
        Database itself reads/writes are present.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
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
                section_id     INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id             SERIAL PRIMARY KEY,
                student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                embedding      BYTEA NOT NULL,
                embedding_json TEXT,
                created_at     TIMESTAMP DEFAULT NOW()
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id         SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                date       TEXT NOT NULL,
                status     TEXT NOT NULL,
                confidence REAL DEFAULT NULL,
                timestamp  TIMESTAMP DEFAULT NOW(),
                session_id INTEGER,
                UNIQUE(student_id, date)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registration_tokens (
                token      TEXT PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                expires_at TIMESTAMP NOT NULL,
                used_at    TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_roll_no            ON students(roll_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_id         ON embeddings(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date    ON attendance(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_student      ON registration_tokens(student_id)')

        conn.commit()
        conn.close()
        logger.info("Database tables created/verified (PostgreSQL)")

    # ── Pending student + token flow ──────────────────────────────────────────

    def add_pending_student(self, name, roll_no, section=None, course=None,
                            dept=None, room_no=None, email=None):
        """
        Add a student record WITHOUT an embedding (pending self-registration).
        Returns student_id.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO students (name, roll_no, section, course, dept, room_no, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                ''',
                (name, roll_no, section, course, dept, room_no, email),
            )
            student_id = cursor.fetchone()['id']
            conn.commit()
            # TODO: replace with Redis before multi-worker deployment
            self.get_all_students_cached.cache_clear()
            logger.info(f"Added pending student: {name} (ID: {student_id})")
            return student_id
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise ValueError(f"Student with roll number {roll_no} already exists")
        finally:
            conn.close()

    def create_registration_token(self, student_id, expires_days=7):
        """Generate a secure one-time token for student self-registration."""
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO registration_tokens (token, student_id, expires_at) VALUES (%s, %s, %s)',
                (token, student_id, expires_at),
            )
            conn.commit()
            return token
        finally:
            conn.close()

    def get_token_info(self, token):
        """Return token + student info if token exists; None otherwise."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT t.token, t.student_id, t.expires_at, t.used_at,
                       s.name, s.roll_no, s.section, s.course, s.dept, s.room_no, s.email,
                       CASE WHEN s.embedding_json IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
                FROM registration_tokens t
                JOIN students s ON s.id = t.student_id
                WHERE t.token = %s
                ''',
                (token,),
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_token_info error: {e}")
            return None

    def mark_token_used(self, token):
        """Mark a token as consumed."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE registration_tokens SET used_at = %s WHERE token = %s',
                (datetime.now().isoformat(), token),
            )
            conn.commit()
        finally:
            conn.close()

    def get_registration_token_by_student(self, student_id):
        """Get the latest active registration token for a student (if exists)."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT token, student_id, created_at, expires_at, used_at
                   FROM registration_tokens
                   WHERE student_id = %s AND used_at IS NULL
                   ORDER BY created_at DESC
                   LIMIT 1''',
                (student_id,),
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_registration_token_by_student error: {e}")
            return None

    # ── Embedding helpers ─────────────────────────────────────────────────────

    def update_student_embedding(self, student_id, avg_embedding):
        """Write/overwrite the main embedding for an existing student record."""
        embedding_json = json.dumps(avg_embedding.tolist())
        embedding_blob = avg_embedding.astype(np.float32).tobytes()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE students SET embedding = %s, embedding_json = %s WHERE id = %s',
                (embedding_blob, embedding_json, student_id),
            )
            conn.commit()
            # TODO: replace with Redis before multi-worker deployment
            self.get_all_students_cached.cache_clear()
            logger.info(f"Updated embedding for student ID {student_id}")
        finally:
            conn.close()

    def add_student(self, name, roll_no, embedding, section=None, course=None,
                    dept=None, room_no=None, email=None):
        """
        Add a new student to the database with a face embedding.

        Args:
            name, roll_no, embedding: required
            section, course, dept, room_no, email: optional profile fields

        Returns:
            Student ID (int)
        """
        embedding_json = json.dumps(embedding.tolist())
        embedding_blob = embedding.astype(np.float32).tobytes()

        max_retries = 3
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO students
                        (name, roll_no, embedding, embedding_json, section, course, dept, room_no, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    ''',
                    (name, roll_no, embedding_blob, embedding_json,
                     section, course, dept, room_no, email),
                )
                student_id = cursor.fetchone()['id']
                conn.commit()
                conn.close()
                # TODO: replace with Redis before multi-worker deployment
                self.get_all_students_cached.cache_clear()
                logger.info(f"✅ Added student: {name} (ID: {student_id}) with JSON embedding")
                return student_id
            except psycopg2.errors.UniqueViolation:
                if conn:
                    conn.rollback()
                    conn.close()
                logger.error(f"Student with roll number {roll_no} already exists")
                raise ValueError(f"Student with roll number {roll_no} already exists")
            except psycopg2.OperationalError as e:
                if conn:
                    conn.close()
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"DB operational error, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.5)
                    continue
                logger.error(f"Error adding student after {attempt + 1} attempts: {e}")
                raise
            except Exception as e:
                if conn:
                    conn.rollback()
                    conn.close()
                logger.error(f"Error adding student: {e}")
                raise

    def add_embedding(self, student_id, embedding):
        """
        Add an additional embedding for a student.

        Args:
            student_id: Student ID
            embedding: Face embedding as numpy array
        """
        embedding_json = json.dumps(embedding.tolist())
        embedding_blob = embedding.astype(np.float32).tobytes()

        max_retries = 3
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO embeddings (student_id, embedding, embedding_json) VALUES (%s, %s, %s)',
                    (student_id, embedding_blob, embedding_json),
                )
                conn.commit()
                conn.close()
                # TODO: replace with Redis before multi-worker deployment
                self.get_student_embeddings_cached.cache_clear()
                logger.info(f"✅ Added JSON embedding for student {student_id}, cache cleared")
                return
            except psycopg2.OperationalError as e:
                if conn:
                    conn.close()
                if attempt < max_retries - 1:
                    import time
                    logger.warning(f"DB operational error, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.5)
                    continue
                logger.error(f"Error adding embedding after {attempt + 1} attempts: {e}")
                raise
            except Exception as e:
                if conn:
                    conn.rollback()
                    conn.close()
                logger.error(f"Error adding embedding: {e}")
                raise

    # ── Cached read helpers ───────────────────────────────────────────────────

    @lru_cache(maxsize=500)  # TODO: replace with Redis before multi-worker deployment
    def get_student_embeddings_cached(self, student_id):
        """
        Get all additional embeddings for a student (CACHED).
        Returns a tuple of dicts (tuple for lru_cache compatibility).
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, student_id, embedding_json AS embedding FROM embeddings WHERE student_id = %s',
                (student_id,),
            )
            rows = cursor.fetchall()
            conn.close()
            return tuple(dict(row) for row in rows)
        except Exception as e:
            logger.error(f"Error getting student embeddings: {e}")
            return tuple()

    def get_student_embeddings(self, student_id):
        """Get all additional embeddings for a student (wrapper for cached version)."""
        return list(self.get_student_embeddings_cached(student_id))

    def get_embeddings_by_student(self, student_id):
        """Get all embeddings (including main embedding) for a student. Used to check if student has registered."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Check main embedding
            cursor.execute('SELECT embedding FROM students WHERE id = %s AND embedding IS NOT NULL', (student_id,))
            main_row = cursor.fetchone()
            
            # Also check additional embeddings
            cursor.execute('SELECT COUNT(*) as count FROM embeddings WHERE student_id = %s', (student_id,))
            count_row = cursor.fetchone()
            conn.close()
            
            # Return True if either main or additional embeddings exist
            has_main = main_row is not None
            has_additional = count_row['count'] > 0 if count_row else False
            
            if has_main or has_additional:
                return self.get_student_embeddings(student_id) + ([dict(main_row)] if has_main else [])
            return []
        except Exception as e:
            logger.error(f"Error getting embeddings for student {student_id}: {e}")
            return []

    @lru_cache(maxsize=200)  # TODO: replace with Redis before multi-worker deployment
    def get_student_by_id_cached(self, student_id):
        """Get student information by ID (CACHED). Returns dict or None."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting student: {e}")
            return None

    def get_student_by_id(self, student_id):
        """Get student information by ID."""
        return self.get_student_by_id_cached(student_id)

    def get_all_students_full(self):
        """Get all students with full profile fields (for API display)."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT id, name, roll_no, section, course, dept, room_no, email,
                       created_at, section_id,
                       CASE WHEN embedding_json IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
                FROM students
                ORDER BY name
                '''
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all students full: {e}")
            return []

    def get_student_by_roll_no(self, roll_no):
        """Get student information by roll number."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE roll_no = %s', (roll_no,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting student by roll_no: {e}")
            return None

    @lru_cache(maxsize=1)  # TODO: replace with Redis before multi-worker deployment
    def get_all_students_cached(self):
        """Get all registered students (CACHED — cleared when students are added/removed)."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, name, roll_no, embedding_json AS embedding FROM students ORDER BY name'
            )
            rows = cursor.fetchall()
            conn.close()
            return tuple(dict(row) for row in rows)
        except Exception as e:
            logger.error(f"Error getting all students: {e}")
            return tuple()

    def get_all_students(self):
        """Get all registered students (wrapper for cached version)."""
        return list(self.get_all_students_cached())

    # ── Attendance ────────────────────────────────────────────────────────────

    def mark_attendance(self, student_id, date, status, force_override=False, confidence=None):
        """
        Mark attendance for a student.
        RULE: Never overwrite 'present' with 'absent' unless force_override=True.

        Args:
            student_id     : Student ID
            date           : Date in YYYY-MM-DD format
            status         : 'present' or 'absent'
            force_override : Allow overwriting present→absent (manual use)
            confidence     : Recognition confidence score (0–1), None for manual marks

        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'SELECT status FROM attendance WHERE student_id = %s AND date = %s',
                (student_id, date),
            )
            existing = cursor.fetchone()

            # Never overwrite present→absent unless forced
            if (existing and existing['status'] == 'present'
                    and status == 'absent' and not force_override):
                logger.info(f"⚠️ Skipping: Student {student_id} already PRESENT on {date}")
                conn.close()
                return True

            cursor.execute(
                '''
                INSERT INTO attendance (student_id, date, status, confidence)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id, date) DO UPDATE
                    SET status = EXCLUDED.status,
                        confidence = EXCLUDED.confidence,
                        timestamp = NOW()
                ''',
                (student_id, date, status, confidence),
            )
            conn.commit()
            conn.close()

            conf_str = f" (confidence: {confidence:.3f})" if confidence is not None else ""
            logger.info(f"✅ Marked student {student_id} as {status} on {date}{conf_str}")
            return True

        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
            return False

    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT s.id, s.name, s.roll_no, a.status, a.confidence, a.timestamp
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = %s
                ORDER BY s.name
                ''',
                (date,),
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting attendance: {e}")
            return []

    def get_attendance_report(self, start_date, end_date):
        """
        Get attendance report for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of attendance records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT s.id, s.name, s.roll_no, a.date, a.status, a.timestamp
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN %s AND %s
                ORDER BY a.date DESC, s.name
                ''',
                (start_date, end_date),
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting attendance report: {e}")
            return []

    # ── Delete / clear helpers ────────────────────────────────────────────────

    def delete_student(self, student_id):
        """Delete a student and all related records (cascades via FK)."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM students WHERE id = %s', (student_id,))
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            if rows_deleted > 0:
                # TODO: replace with Redis before multi-worker deployment
                self.get_all_students_cached.cache_clear()
                self.get_student_by_id_cached.cache_clear()
                self.get_student_embeddings_cached.cache_clear()
                logger.info(f"✅ Deleted student ID {student_id} and cleared caches")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting student: {e}")
            raise

    def clear_all_students(self):
        """Delete ALL students and their embeddings — DESTRUCTIVE!"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance')
            attendance_deleted = cursor.rowcount
            cursor.execute('DELETE FROM embeddings')
            embeddings_deleted = cursor.rowcount
            cursor.execute('DELETE FROM students')
            students_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            # TODO: replace with Redis before multi-worker deployment
            self.get_all_students_cached.cache_clear()
            self.get_student_by_id_cached.cache_clear()
            self.get_student_embeddings_cached.cache_clear()
            logger.warning(
                f"⚠️ CLEARED ALL DATA: {students_deleted} students, "
                f"{embeddings_deleted} embeddings, {attendance_deleted} attendance records"
            )
            return True
        except Exception as e:
            logger.error(f"Error clearing all students: {e}")
            raise

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_student_statistics(self, student_id):
        """Get attendance statistics for a student."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT
                    COUNT(*) AS total_days,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present_days,
                    SUM(CASE WHEN status = 'absent'  THEN 1 ELSE 0 END) AS absent_days
                FROM attendance
                WHERE student_id = %s
                ''',
                (student_id,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                result = dict(row)
                total = result['total_days'] or 0
                present = result['present_days'] or 0
                result['attendance_percentage'] = (present / total * 100) if total > 0 else 0.0
                return result
            return {'total_days': 0, 'present_days': 0, 'absent_days': 0, 'attendance_percentage': 0.0}
        except Exception as e:
            logger.error(f"Error getting student statistics: {e}")
            return None

    def clear_attendance_by_date(self, date):
        """
        Clear all attendance records for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance WHERE date = %s', (date,))
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            logger.info(f"Deleted {rows_deleted} attendance records for {date}")
            return True
        except Exception as e:
            logger.error(f"Error clearing attendance for {date}: {e}")
            return False
