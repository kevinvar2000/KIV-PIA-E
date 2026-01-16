from flask import Blueprint, redirect, render_template, request, jsonify, session, url_for
from services.AuthService import AuthService, login_required_ui, login_required_api, require_role
from services.UserService import UserService
from services.ProjectService import ProjectService
from bin.helper import get_supported_languages, MAX_FILE_SIZE_MB


user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    API endpoint to create a new user.
    Expects a JSON payload with the following fields:
    - name (str): Full name of the user.
    - email (str): Unique email address for the user.
    - password (str): Plaintext password to be securely hashed.
    - role (str): Role assigned to the user (e.g., "admin", "user").
    - languages (list[str], optional): List of language codes/preferences. Defaults to an empty list.
    Behavior:
    - Hashes the provided password before persisting.
    - Delegates user creation to the UserService.
    - Returns a success message with HTTP 201 on successful creation.
    - Returns an error message with HTTP 400 if validation fails or a ValueError is raised.
    Returns:
        flask.Response: JSON response with a message on success (201) or error details (400).
    Raises:
        None: Errors are handled and returned as HTTP responses.
    """

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    languages = data.get('languages', [])

    try:
        hashed_password = AuthService.hash_password(password)
        UserService.create_user(name, email, hashed_password, role, languages)
        print(f"[UserController.py] User created: {name} with role {role}", flush=True)
        return jsonify({'message': 'User created successfully.'}), 201
    except ValueError as e:
        print(f"[UserController.py] User creation failed: {e}", flush=True)
        return jsonify({'error': str(e)}), 400


@user_bp.route('/users', methods=['GET'])
@login_required_api
@require_role('ADMINISTRATOR')
def get_all_users():
    """
    Retrieve all users.

    This Flask API endpoint invokes the UserService to fetch all users and returns
    a JSON response in the format {"users": [...]}, along with an HTTP 200 status code.

    Returns:
        Tuple[flask.Response, int]: A JSON response containing the list of users and the HTTP status code.
    """

    users = UserService.get_all_users()
    return jsonify({'users': users}), 200


@user_bp.route('/users/<name>', methods=['GET'])
@login_required_api
@require_role('ADMINISTRATOR')
def get_user(name):
    """
    Retrieve a user by name via the API.
    This endpoint queries the UserService for a user matching the provided name.
    If found, it returns a JSON response with the user data and an HTTP 200 status.
    If no user is found, it returns an error message with an HTTP 404 status.
    Parameters:
        name (str): The username to search for.
    Returns:
        tuple:
            - flask.Response: JSON response containing either:
                - {"user": <dict>} when the user is found.
                - {"error": "User not found."} when the user is absent.
            - int: HTTP status code (200 on success, 404 if not found).
    """

    user_data = UserService.get_user_by_name(name)

    if not user_data:
        print(f"[UserController.py] User not found: {name}", flush=True)
        return jsonify({'error': 'User not found.'}), 404

    return jsonify({'user': user_data}), 200


@user_bp.route('/customer', methods=['GET'])
@login_required_ui
@require_role('CUSTOMER')
def customer_page():
    """
    Render the customer dashboard and handle access control.
    This view function verifies the presence of an authenticated user in the
    session, redirects to the login page if absent, and otherwise retrieves the
    current user's data to fetch their associated projects. It then renders the
    customer dashboard template with:
    - max_file_size_mb: Maximum upload size (in megabytes) permitted for files.
    - projects: List of projects relevant to the authenticated user (based on role).
    - languages: List of supported programming languages for project creation.
    Returns:
        flask.Response: A redirect response to the login page if no active session
        is found, or the rendered customer dashboard page when the user is authenticated.
    """

    user_session = session.get('user')
    if not user_session:
        print(f"[UserController.py] No user in session for customer page.", flush=True)
        return redirect(url_for('auth_bp.login_page'))

    user_data = UserService.get_user_by_name(user_session['name'])
    
    projects = ProjectService.get_projects_by_user_id(user_data['id'], user_data['role'])

    return render_template('pages/customer.html', max_file_size_mb=MAX_FILE_SIZE_MB, projects=projects, languages=get_supported_languages())


@user_bp.route('/translator', methods=['GET'])
@login_required_ui
@require_role('TRANSLATOR')
def translator_page():
    """
    Render the translator dashboard or redirect to login if the user is not authenticated.
    This view:
    - Retrieves the current user session; if absent, redirects to the login page.
    - Loads the full user record by username from the session.
    - Fetches projects associated with the user, respecting the user's role.
    - Performs feedback checks/updates on the retrieved projects.
    - Renders the translator dashboard template with the user's projects.
    Returns:
        werkzeug.wrappers.response.Response: A redirect response to the login page when no user session is present,
        or a rendered HTML response for the translator dashboard with the 'projects' context.
    """

    user_session = session.get('user')
    if not user_session:
        print(f"[UserController.py] No user in session for translator page.", flush=True)
        return redirect(url_for('auth_bp.login_page'))
    
    user_data = UserService.get_user_by_name(user_session['name'])
    
    projects = ProjectService.get_projects_by_user_id(user_data['id'], user_data['role'])

    ProjectService.check_feedbacks(projects)

    return render_template('pages/translator.html', projects=projects)


@user_bp.route('/administrator', methods=['GET'])
@login_required_ui
@require_role('ADMINISTRATOR')
def administrator_page():
    """
    Render the administrator dashboard page.
    This view:
    - Checks for an authenticated user in the session; if absent, redirects to the login page.
    - Fetches all project states and prepends an 'all' option for filtering.
    - Retrieves all projects and performs a feedback check/update via ProjectService.
    - Applies an optional state-based filter when the 'state' query parameter is provided
        and not equal to "ALL" (case-sensitive), comparing against each project's state.
    Query Parameters:
    - state (str | None): Optional state filter taken from the request query string.
        If provided and not "ALL", projects are filtered to those whose state string
        matches the given value.
    Returns:
    - A rendered HTML template ('pages/administrator.html') with:
        - projects (list[dict]): The (optionally filtered) list of projects.
        - states (list[str]): Available state options including 'all'.
        - selected_state (str | None): The selected filter value, if any.
    Redirects:
    - To the login page ('auth_bp.login_page') if no user session is present.
    Side Effects:
    - May trigger feedback checks/updates on the retrieved projects via ProjectService.check_feedbacks.
    """

    selected_state = request.args.get("state")

    user_session = session.get('user')
    if not user_session:
        print(f"[UserController.py] No user in session for administrator page.", flush=True)
        return redirect(url_for('auth_bp.login_page'))

    states = ['all'] + [state.name for state in ProjectService.get_all_project_states()]

    projects = ProjectService.get_all_projects()

    ProjectService.check_feedbacks(projects)

    if selected_state and selected_state != "ALL":
        projects = [p for p in projects if str(p.get("state")) == selected_state]

    return render_template('pages/administrator.html', projects=projects, states=states, selected_state=selected_state)