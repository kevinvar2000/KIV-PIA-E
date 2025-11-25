from flask import Blueprint, redirect, render_template, request, jsonify, session, url_for
from services.AuthService import AuthService
from services.UserService import UserService
from services.ProjectService import ProjectService
from bin.helper import get_supported_languages, MAX_FILE_SIZE_MB


user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/users', methods=['POST'])
def create_user():
    """API endpoint to create a new user."""
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    languages = request.form.get('languages', [])

    try:
        hashed_password = AuthService.hash_password(password)
        UserService.create_user(name, email, hashed_password, role, languages)
        return jsonify({'message': 'User created successfully.'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """API endpoint to get all users."""
    users = UserService.get_all_users()
    return jsonify({'users': users}), 200


@user_bp.route('/users/<name>', methods=['GET'])
def get_user(name):
    """API endpoint to get a user by name."""
    user_data = UserService.get_user_by_name(name)

    if not user_data:
        return jsonify({'error': 'User not found.'}), 404

    return jsonify({'user': user_data}), 200


@user_bp.route('/customer', methods=['GET'])
def customer():
    """Customer dashboard and project creation"""

    user_session = session.get('user')
    if not user_session:
        return redirect(url_for('auth_bp.login_page'))
    
    print("User session found:", user_session, flush=True)

    user_data = UserService.get_user_by_name(user_session['name'])
    
    print("Rendering customer dashboard for user:", user_data, flush=True)

    projects = ProjectService.get_projects_by_user_id(user_data['id'], user_data['role'])

    print(f"Projects for customer {user_data['id']}: {projects}", flush=True)

    return render_template('pages/customer.html', max_file_size_mb=MAX_FILE_SIZE_MB, projects=projects, languages=get_supported_languages())


@user_bp.route('/translator', methods=['GET'])
def translator():
    """Translator dashboard"""

    user_session = session.get('user')
    if not user_session:
        return redirect(url_for('auth_bp.login_page'))
    
    print("User session found:", user_session, flush=True)

    user_data = UserService.get_user_by_name(user_session['name'])
    
    print("Rendering translator dashboard for user:", user_data, flush=True)

    projects = ProjectService.get_projects_by_user_id(user_data['id'], user_data['role'])

    ProjectService.check_feedbacks(projects)

    return render_template('pages/translator.html', projects=projects)