from services.UserService import UserService
import hashlib
from flask import session, jsonify, redirect, url_for
from functools import wraps


class AuthService:

    @staticmethod
    def hash_password(password):
        """
        Hash a plaintext password using SHA-256 and return the hexadecimal digest.

        Note:
            This function performs a simple SHA-256 hash without a salt or key stretching.
            For production use, consider a stronger, salted password hashing algorithm such
            as bcrypt, scrypt, Argon2, or PBKDF2.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The SHA-256 hash of the password as a hexadecimal string.
        """
        return hashlib.sha256(password.encode()).hexdigest()
    

    @staticmethod
    def authenticate_user(name, password):
        """
        Authenticate a user by verifying the provided credentials.
        This function hashes the given plaintext password and compares it against
        the stored hashed password for the user identified by `name`. If the
        credentials match, the user's data is returned; otherwise, `None` is returned.
        Parameters:
            name (str): The unique username used to identify the user.
            password (str): The plaintext password to be authenticated.
        Returns:
            dict | None: A dictionary containing the authenticated user's data if the
            credentials are valid; otherwise, None.
        Notes:
            - Relies on AuthService.hash_password for password hashing.
            - Fetches user data via UserService.get_user_by_name.
        """

        hashed_password = AuthService.hash_password(password)

        user_data = UserService.get_user_by_name(name)

        if user_data and user_data.get('password') == hashed_password:
            return user_data

        return None


def login_required_api(f):
    """
    Decorator that enforces authentication for API endpoints.

    Checks if a 'user' key exists in the session. If absent, returns a JSON
    error response with HTTP 401 Unauthorized; otherwise, executes the wrapped
    view function.

    Parameters:
        f (Callable): The view function to wrap.

    Returns:
        Callable: The wrapped function that performs the authentication check.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapper


def login_required_ui(f):
    """
    Decorator for Flask view functions that enforces user authentication.
    This decorator checks the Flask session for a 'user' entry and verifies that the
    user exists via UserService.get_user_by_name. If the user is not authenticated
    or cannot be validated, the request is redirected to the 'auth_bp.login_page'.
    Parameters:
        f (Callable): The Flask view function to protect.
    Returns:
        Callable: A wrapped view function that either proceeds if the user is authenticated
        or redirects to the login page if not.
    Notes:
        - Relies on a Flask session containing a 'user' dict with a 'name' key.
        - Requires the 'auth_bp.login_page' route for redirection.
        - Depends on UserService.get_user_by_name to validate the user.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth_bp.login_page'))
        
        user_session = session.get('user')
        if not user_session:
            return redirect(url_for('auth_bp.login_page'))
    
        user_data = UserService.get_user_by_name(user_session['name'])
        if not user_data:
            return redirect(url_for('auth_bp.login_page'))

        return f(*args, **kwargs)
    return wrapper


def require_role(*allowed_roles):
    """
    Decorator factory that enforces role-based access control for Flask route handlers.

    This decorator checks the current session for a `user` object and validates that
    the user's `role` is among the specified `allowed_roles`. If the user is missing
    or their role is not permitted, it returns a JSON error response with HTTP 403
    (Forbidden). Otherwise, it proceeds to call the wrapped function.

    Parameters:
        *allowed_roles: One or more role identifiers (e.g., strings) that are allowed
            to access the decorated endpoint.

    Returns:
        Callable: A decorator that wraps a Flask view function, enforcing the role
        requirement and returning either the view's response or a 403 Forbidden JSON
        response.

    Usage:
        @require_role('admin', 'moderator')
        def protected_view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get('user')
            if not user or user['role'] not in allowed_roles:
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator