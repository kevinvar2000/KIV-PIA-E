from flask import render_template, redirect, url_for, Blueprint, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from services.AuthService import AuthService
from services.UserService import UserService
from bin.helper import get_supported_languages
import os


auth_bp = Blueprint('auth_bp', __name__)
load_dotenv()


google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    redirect_to='auth_bp.google_login',
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
)


@auth_bp.route('/login')
def login_page():
    """
    The `login_page` function checks if a user is logged in and redirects to the home page if they are,
    otherwise it renders the login template.
    :return: The `login_page` function is returning either a redirect to the home page if the user is
    already logged in (based on the session), or it is rendering the 'auth/login.html' template if the
    user is not logged in.
    """

    if session.get('user'):
        return redirect(url_for('app_bp.home'))

    return render_template('auth/login.html')


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """
    This function handles user authentication for an API by verifying the user's credentials and setting
    a session with user information if successful.
    :return: If the authentication is successful, a dictionary containing the status as 'success' and
    the user's role will be returned with a status code of 200. If the authentication fails, a
    dictionary containing the status as 'failure' will be returned with a status code of 401.
    """

    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    user = AuthService.authenticate_user(name, password)

    if user:
        session['user'] = { 'user_id': user.get('id'), 'name': user.get('name'), 'email': user.get('email'), 'role': user.get('role')}
        return {'status': 'success', 'role': user.get('role')}, 200
    else:
        return {'status': 'failure'}, 401


@auth_bp.route('/google_login')
def google_login():
    """
    Handle Google OAuth login flow and user session initialization.
    - If the user is not yet authorized with Google, redirects to the Google OAuth login route.
    - On successful authorization, retrieves the user's Google profile (email and optional name).
    - Ensures a local user record exists; creates one with a 'user' role if absent.
    - Stores basic user info (name, email) in the session.
    - Redirects to the application home page upon completion.
    Returns:
        A Flask redirect response to either the Google login route (if not authorized) or the app's home page.
    """

    if not google.authorized:
        return redirect(url_for('google.login'))
    
    resp = google.get('/oauth2/v2/userinfo')
    assert resp.ok, resp.text

    user_info = resp.json()
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0])

    user = UserService.get_user_by_email(email)
    if not user:
        UserService.create_user(name=name, email=email, role='user')
    session['user'] = {'name': name, 'email': email}
    
    return redirect(url_for('app_bp.home'))


@auth_bp.route('/register')
def register_page():
    """
    Render the registration page with supported languages.
    :return: Rendered registration template with a list of supported languages.
    """
    return render_template('auth/register.html', languages=get_supported_languages())


@auth_bp.route('/api/register', methods=['POST'])
def api_register():        
    """
    Handle user registration via JSON API.
    Expects a JSON payload containing the user's name, email, plaintext password,
    role, and an optional list of language identifiers. The password is securely
    hashed before creating the user record.
    Parameters:
        None (reads JSON from the current Flask request context)
    JSON Payload:
        name (str): Full name of the user to register.
        email (str): Unique email address of the user.
        password (str): Plaintext password to be hashed and stored.
        role (str): Role identifier for the user (e.g., "admin", "user").
        languages (list[str], optional): List of language codes or IDs associated with the user. Defaults to [].
    Returns:
        tuple[dict, int]: A tuple containing a JSON response dict with a "status" key
        set to "success", and the HTTP status code 201 on successful registration.
    Raises:
        werkzeug.exceptions.BadRequest: If the request body is not valid JSON or required fields are missing.
        ValueError: If provided data fails validation (e.g., invalid email, weak password).
        Exception: For unexpected server errors during hashing or persistence.
    """

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    languages = data.get('languages', [])

    hashed_password = AuthService.hash_password(password)

    AuthService.register_user(name, email, hashed_password, role, languages)

    return {'status': 'success'}, 201


@auth_bp.route('/logout')
def logout():
    """
    The `logout` function removes the 'user' session and redirects to the login page of the
    authentication blueprint.
    :return: The `logout` function is returning a redirect response to the login page of the
    authentication blueprint (`auth_bp`).
    """
    session.pop('user', None)
    return redirect(url_for('auth_bp.login_page'))


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """
    The `api_logout` function logs out the user by removing the 'user' session variable and returns a
    success status with HTTP status code 200.
    :return: The function `api_logout` is returning a dictionary `{'status': 'success'}` along with the
    HTTP status code `200`.
    """
    session.pop('user', None)
    return {'status': 'success'}, 200