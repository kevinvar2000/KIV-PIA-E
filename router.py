from controllers.AuthController import auth_bp, google_bp
from controllers.UserController import user_bp
from controllers.ProjectController import proj_bp
from controllers.EmailController import email_bp
from flask import Blueprint, redirect, url_for, session


def register_routes(app):
    """
    Register application blueprints with the given Flask app.

    This function attaches multiple blueprints to the Flask application:
    - Root application routes (`app_bp`)
    - Authentication routes under `/auth` (`auth_bp`)
    - Google login routes under `/login` (`google_bp`)
    - User-related API routes under `/api` (`user_bp`)
    - Project-related API routes under `/api` (`proj_bp`)

    Parameters:
        app (flask.Flask): The Flask application instance to register blueprints on.

    Returns:
        None
    """
    app.register_blueprint(app_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(google_bp, url_prefix='/login')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(proj_bp, url_prefix='/api')
    app.register_blueprint(email_bp, url_prefix='/api')

    print("[router.py] Blueprints registered.", flush=True)


app_bp = Blueprint('app_bp', __name__)


@app_bp.route('/')
def home():
    """
    Handle the home route by redirecting users based on authentication status and role.
    Behavior:
    - If no user is present in the session, redirects to the login page.
    - If the user is authenticated, redirects based on the user's role:
        - 'CUSTOMER' -> user_bp.customer
        - 'TRANSLATOR' -> user_bp.translator
        - 'ADMINISTRATOR' -> user_bp.administrator
    - Returns a 403 response with "Unknown role" if the role is missing or unrecognized.
    Returns:
    - A redirect response to the appropriate route based on the user's role.
    - A 403 response for unknown roles.
    """

    print("[router.py] Home route accessed.", flush=True)

    if 'user' not in session:
        return redirect(url_for('auth_bp.login_page'))

    user = session['user']
    if user.get('role') == 'CUSTOMER':
        return redirect(url_for('user_bp.customer_page'))
    elif user.get('role') == 'TRANSLATOR':
        return redirect(url_for('user_bp.translator_page'))
    elif user.get('role') == 'ADMINISTRATOR':
        return redirect(url_for('user_bp.administrator_page'))
    else:
        print(f"[router.py] Unknown role encountered: {user.get('role')}", flush=True)
        return "Unknown role", 403