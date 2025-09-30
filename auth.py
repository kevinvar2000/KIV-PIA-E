from flask import render_template, redirect, url_for, Blueprint, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
import pycountry
import os

auth_bp = Blueprint('auth_bp', __name__)
load_dotenv()

google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    redirect_to='auth_bp.google_login',
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        print(f"Name: {name}, Password: {password}", flush=True)

        # TODO: implement login logic

        return redirect(url_for('app_bp.home'))

    return render_template('auth/login.html')

@auth_bp.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    
    resp = google.get('/oauth2/v2/userinfo')
    assert resp.ok, resp.text

    user_info = resp.json()
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0])

    session['user'] = {'name': name, 'email': email}
    print(f"Google user info: {user_info}", flush=True)
    
    return redirect(url_for('app_bp.home'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        languages = request.form.getlist('languages')

        print(f"Name: {name}, Email: {email}, Password: {password}, Role: {role}, Languages: {languages}", flush=True)

        # TODO: save user to database
        return redirect(url_for('app_bp.login'))

    langs = sorted([(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')], key=lambda x: x[1])

    return render_template('auth/register.html', languages=langs)