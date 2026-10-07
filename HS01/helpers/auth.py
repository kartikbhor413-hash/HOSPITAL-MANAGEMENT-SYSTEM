"""
helpers/auth.py
Authentication and Role-Based Access Control (RBAC) middleware for Flask.
Handles password hashing, session checking, and role protection decorators.
"""

from functools import wraps
from flask import session, jsonify, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from helpers.json_db import find_by_id, read_data


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Werkzeug's secure hash."""
    return generate_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks plaintext password against hashed password."""
    if not hashed_password:
        return False
    return check_password_hash(hashed_password, plain_password)


def get_current_user():
    """Returns the currently logged-in user dict from session, or None."""
    return session.get("user", None)


def login_required(f):
    """Decorator to require login. Returns 401 JSON for /api/ routes, else redirects to /login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "error": "Authentication required. Please log in."
                }), 401
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles):
    """
    Decorator to restrict access to specific roles.
    allowed_roles can be a string (e.g. 'Admin') or list of strings (e.g. ['Admin', 'Doctor']).
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.path.startswith("/api/"):
                    return jsonify({
                        "success": False,
                        "error": "Authentication required."
                    }), 401
                return redirect(url_for("login_page", next=request.path))

            user_role = user.get("role")
            if user_role not in allowed_roles:
                if request.path.startswith("/api/"):
                    return jsonify({
                        "success": False,
                        "error": f"Access forbidden. Required role: {', '.join(allowed_roles)}. Your role: {user_role}"
                    }), 403
                # For web views, redirect to appropriate role dashboard or show message
                return redirect(url_for("unauthorized_page"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def authenticate_user(username, password):
    """
    Validates user credentials against data/users.json.
    Returns (user_dict, None) on success or (None, error_message) on failure.
    """
    if not username or not password:
        return None, "Username and password are required."

    users = read_data("users")
    user = None
    for u in users:
        if u.get("username", "").lower() == username.strip().lower():
            user = u
            break

    if not user:
        return None, "Invalid username or password."

    if not user.get("is_active", True):
        return None, "This account is inactive. Please contact system administrator."

    # Verify password (supports hashed and plaintext fallback for initial seed safety)
    stored_hash = user.get("password_hash")
    stored_plain = user.get("password")  # In case plain is used during seed

    is_valid = False
    if stored_hash:
        is_valid = verify_password(password, stored_hash)
    elif stored_plain:
        is_valid = (stored_plain == password)

    if not is_valid:
        return None, "Invalid username or password."

    # Create safe user object for session (exclude password hashes)
    safe_user = {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "associated_id": user.get("associated_id")  # e.g. DOC001, PAT001, NUR001
    }
    return safe_user, None
