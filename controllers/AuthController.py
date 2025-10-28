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

    if session.get('user'):
        return redirect(url_for('app_bp.home'))

    return render_template('auth/login.html')


@auth_bp.route('/api/login', methods=['POST'])
def api_login():

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

    return render_template('auth/register.html', languages=get_supported_languages())


@auth_bp.route('/api/register', methods=['POST'])
def api_register():

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
    session.pop('user', None)
    return redirect(url_for('auth_bp.login_page'))


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return {'status': 'success'}, 200