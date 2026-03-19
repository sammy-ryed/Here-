"""
Flask route decorators for JWT authentication and role-based access control.

Usage:
    @app.route('/some/route', methods=['GET'])
    @require_auth
    def my_view():
        user = g.current_user  # {'user_id': int, 'username': str, 'role': str}
        ...

    @app.route('/admin/route', methods=['POST'])
    @require_auth
    @require_role('admin')
    def admin_view():
        ...
"""

import logging
from functools import wraps

import jwt
from flask import g, jsonify, request

from auth.jwt_utils import decode_token

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Validate the Bearer token in the Authorization header.
    On success: sets flask.g.current_user and calls the wrapped function.
    On failure: returns 401 JSON error immediately.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or malformed Authorization header. Use: Bearer <token>'}), 401
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT: {e}")
            return jsonify({'error': 'Invalid token.'}), 401
        g.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role'],
        }
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """
    Allow access only if g.current_user['role'] is in the given roles.
    Must be stacked AFTER @require_auth so that g.current_user is set.

    Example:
        @require_auth
        @require_role('admin')
        def admin_only_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if user is None:
                return jsonify({'error': 'Not authenticated'}), 401
            if user['role'] not in roles:
                return jsonify({
                    'error': f"Access denied. Required role: {' or '.join(roles)}. "
                             f"Your role: {user['role']}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
