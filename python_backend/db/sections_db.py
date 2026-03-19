"""
SectionsDB — CRUD for sections, subjects, teacher_sections, sessions,
and the student-section assignment endpoint.

Uses the same psycopg2 connection pattern as Database and AuthDB.
"""

import logging
import os

import psycopg2
import psycopg2.extras
import psycopg2.errors
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/here')


class SectionsDB:
    """Data access for sections, subjects, teacher_sections, and sessions."""

    def __init__(self):
        self.dsn = _DATABASE_URL

    def _get_conn(self):
        return psycopg2.connect(
            self.dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode='require',
        )

    # ── Sections ──────────────────────────────────────────────────────────────

    def create_section(self, name: str, year: int = None,
                       department: str = None, batch: str = None) -> int:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO sections (name, year, department, batch) VALUES (%s, %s, %s, %s) RETURNING id',
                (name, year, department, batch)
            )
            section_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Created section '{name}' id={section_id}")
            return section_id
        finally:
            conn.close()

    def get_all_sections(self) -> list:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM sections ORDER BY name')
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_all_sections error: {e}")
            return []
        finally:
            conn.close()

    def get_section_by_name(self, name: str) -> dict | None:
        """Case-insensitive name lookup — used by bulk import to resolve section_id."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM sections WHERE LOWER(name) = LOWER(%s) LIMIT 1', (name,))
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_section_by_name error: {e}")
            return None
        finally:
            conn.close()

    # ── Subjects ──────────────────────────────────────────────────────────────

    def create_subject(self, name: str, code: str, section_id: int) -> int:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO subjects (name, code, section_id) VALUES (%s, %s, %s) RETURNING id',
                (name, code, section_id)
            )
            subject_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Created subject '{name}' ({code}) in section {section_id}")
            return subject_id
        except psycopg2.errors.ForeignKeyViolation:
            conn.rollback()
            raise ValueError(f"Section id={section_id} does not exist.")
        finally:
            conn.close()

    def get_subjects_by_section(self, section_id: int) -> list:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM subjects WHERE section_id = %s ORDER BY name', (section_id,))
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_subjects_by_section error: {e}")
            return []
        finally:
            conn.close()

    # ── Teacher ↔ Section assignments ─────────────────────────────────────────

    def assign_teacher_section(self, teacher_id: int, section_id: int) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                '''
                INSERT INTO teacher_sections (teacher_id, section_id)
                VALUES (%s, %s)
                ON CONFLICT (teacher_id, section_id) DO NOTHING
                ''',
                (teacher_id, section_id)
            )
            conn.commit()
            return True
        except psycopg2.errors.ForeignKeyViolation as e:
            conn.rollback()
            raise ValueError(str(e))
        finally:
            conn.close()

    def get_teacher_sections(self, teacher_id: int = None) -> list:
        """
        Return teacher_sections rows joined with users and sections.
        If teacher_id is given, filter to that teacher only.
        """
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            if teacher_id is not None:
                cur.execute(
                    '''
                    SELECT ts.teacher_id, u.username, ts.section_id, s.name AS section_name
                    FROM teacher_sections ts
                    JOIN users u ON u.id = ts.teacher_id
                    JOIN sections s ON s.id = ts.section_id
                    WHERE ts.teacher_id = %s
                    ORDER BY s.name
                    ''',
                    (teacher_id,)
                )
            else:
                cur.execute(
                    '''
                    SELECT ts.teacher_id, u.username, ts.section_id, s.name AS section_name
                    FROM teacher_sections ts
                    JOIN users u ON u.id = ts.teacher_id
                    JOIN sections s ON s.id = ts.section_id
                    ORDER BY u.username, s.name
                    '''
                )
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_teacher_sections error: {e}")
            return []
        finally:
            conn.close()

    # ── Sessions ──────────────────────────────────────────────────────────────

    def create_session(self, teacher_id: int, section_id: int, subject_id: int,
                       gps_lat: float = None, gps_lon: float = None) -> int:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                '''
                INSERT INTO sessions
                    (teacher_id, section_id, subject_id, teacher_gps_lat, teacher_gps_lon)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                ''',
                (teacher_id, section_id, subject_id, gps_lat, gps_lon)
            )
            session_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Created session id={session_id} teacher={teacher_id} section={section_id}")
            return session_id
        except psycopg2.errors.ForeignKeyViolation as e:
            conn.rollback()
            raise ValueError(str(e))
        finally:
            conn.close()

    def get_sessions(self, teacher_id: int = None) -> list:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            if teacher_id is not None:
                cur.execute(
                    '''
                    SELECT sess.*,
                           u.username AS teacher_username,
                           sec.name   AS section_name,
                           sub.name   AS subject_name, sub.code AS subject_code
                    FROM sessions sess
                    JOIN users    u   ON u.id   = sess.teacher_id
                    JOIN sections sec ON sec.id = sess.section_id
                    JOIN subjects sub ON sub.id = sess.subject_id
                    WHERE sess.teacher_id = %s
                    ORDER BY sess.started_at DESC
                    ''',
                    (teacher_id,)
                )
            else:
                cur.execute(
                    '''
                    SELECT sess.*,
                           u.username AS teacher_username,
                           sec.name   AS section_name,
                           sub.name   AS subject_name, sub.code AS subject_code
                    FROM sessions sess
                    JOIN users    u   ON u.id   = sess.teacher_id
                    JOIN sections sec ON sec.id = sess.section_id
                    JOIN subjects sub ON sub.id = sess.subject_id
                    ORDER BY sess.started_at DESC
                    '''
                )
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_sessions error: {e}")
            return []
        finally:
            conn.close()

    def confirm_session(self, session_id: int) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET status = 'confirmed', confirmed_at = NOW() WHERE id = %s AND status = 'open'",
                (session_id,)
            )
            updated = cur.rowcount
            conn.commit()
            return updated > 0
        except Exception as e:
            logger.error(f"confirm_session error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def void_session(self, session_id: int) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET status = 'voided' WHERE id = %s AND status != 'voided'",
                (session_id,)
            )
            updated = cur.rowcount
            conn.commit()
            return updated > 0
        except Exception as e:
            logger.error(f"void_session error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ── Student ↔ Section assignment ──────────────────────────────────────────

    def update_student_section(self, student_id: int, section_id: int) -> bool:
        """Set students.section_id for the given student."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'UPDATE students SET section_id = %s WHERE id = %s',
                (section_id, student_id)
            )
            updated = cur.rowcount
            conn.commit()
            return updated > 0
        except psycopg2.errors.ForeignKeyViolation:
            conn.rollback()
            raise ValueError(f"Section id={section_id} does not exist.")
        finally:
            conn.close()
