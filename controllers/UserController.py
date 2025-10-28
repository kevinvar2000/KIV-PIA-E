from flask import Blueprint, render_template, request, jsonify
from services.AuthService import AuthService
from services.UserService import UserService
from bin.helper import get_supported_languages, MAX_FILE_SIZE_MB


user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/users', methods=['POST'])
def create_user():
    """API endpoint to create a new user."""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    languages = data.get('languages', [])

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

    user_info = {
        'id': str(user_data.id),
        'name': user_data.name,
        'email': user_data.email,
        'role': user_data.role.value,
        'created_at': user_data.created_at.isoformat(),
        'languages': user_data.get_languages()
    }

    return jsonify({'user': user_info}), 200


@user_bp.route('/customer', methods=['GET'])
def customer():
    """Customer dashboard and project creation"""

    return render_template('pages/customer.html', max_file_size_mb=MAX_FILE_SIZE_MB, languages=get_supported_languages())