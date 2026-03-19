"""
JWT utility helpers for HERE backend.
Encodes and decodes HS256 tokens using the JWT_SECRET_KEY from .env.
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

_SECRET = os.environ.get('JWT_SECRET_KEY', 'change-me-in-production')
_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', '8'))
_ALGORITHM = 'HS256'


def generate_token(user_id: int, username: str, role: str) -> str:
    """
    Create a signed JWT valid for JWT_EXPIRY_HOURS hours.

    Payload fields: user_id, username, role, exp, iat
    """
    now = datetime.now(tz=timezone.utc)
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'iat': now,
        'exp': now + timedelta(hours=_EXPIRY_HOURS),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Verify and decode a JWT.

    Returns the payload dict on success.
    Raises jwt.ExpiredSignatureError if the token has expired.
    Raises jwt.InvalidTokenError (or subclass) for any other invalidity.
    """
    return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
