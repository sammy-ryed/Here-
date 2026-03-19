"""
Seed script — creates the default admin user in PostgreSQL.

Usage:
    python db/seed_admin.py

Credentials are read from environment variables (fall back to defaults):
    SEED_ADMIN_USER  (default: admin)
    SEED_ADMIN_PASS  (default: Admin@here1)

Safe to run multiple times — skips if the username already exists.
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from dotenv import load_dotenv

load_dotenv()

from db.auth_db import AuthDB


def main():
    username = os.environ.get('SEED_ADMIN_USER', 'admin')
    password = os.environ.get('SEED_ADMIN_PASS', 'Admin@here1')

    if len(password) < 8:
        print(f"ERROR: Password must be at least 8 characters.")
        sys.exit(1)

    auth_db = AuthDB()

    # Check if admin already exists
    existing = auth_db.get_user_by_username(username)
    if existing:
        print(f"[seed_admin] User '{username}' already exists (id={existing['id']}, role={existing['role']}). Skipping.")
        return

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_id = auth_db.create_user(username, password_hash, role='admin')

    print("=" * 50)
    print("[seed_admin] ✅ Admin user created successfully")
    print(f"  User ID  : {user_id}")
    print(f"  Username : {username}")
    print(f"  Password : {password}")
    print(f"  Role     : admin")
    print("=" * 50)
    print("IMPORTANT: Change the password after first login!")


if __name__ == '__main__':
    main()
