"""
AuthDB — User account CRUD for the HERE backend.
Uses the same PostgreSQL connection pattern as Database.
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


class AuthDB:
    """User account data access layer."""

    def __init__(self):
        self.dsn = _DATABASE_URL
        self._ensure_users_table()

    # ── internal helpers ──────────────────────────────────────────────────────

    def _get_conn(self):
        return psycopg2.connect(
            self.dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode='require',
        )

    def _ensure_users_table(self):
        """Idempotent table creation (also done by migrate_postgres.py)."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role          TEXT NOT NULL CHECK (role IN ('admin', 'teacher')),
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            ''')
            conn.commit()
        finally:
            conn.close()

    # ── public API ────────────────────────────────────────────────────────────

    def get_user_by_username(self, username: str) -> dict | None:
        """Return the user row for the given username, or None."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_user_by_username error: {e}")
            return None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> dict | None:
        """Return the user row for the given id, or None."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_user_by_id error: {e}")
            return None
        finally:
            conn.close()

    def create_user(self, username: str, password_hash: str, role: str) -> int:
        """
        Insert a new user and return the new user_id.
        Raises ValueError if the username is already taken.
        """
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id',
                (username, password_hash, role),
            )
            user_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Created user '{username}' (role={role}) id={user_id}")
            return user_id
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise ValueError(f"Username '{username}' is already taken.")
        finally:
            conn.close()

    def list_users(self) -> list[dict]:
        """Return all users (password_hash excluded)."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, username, role, created_at FROM users ORDER BY id')
            return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"list_users error: {e}")
            return []
        finally:
            conn.close()
