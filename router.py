from controllers.AuthController import auth_bp, google_bp
from controllers.UserController import user_bp
from controllers.ProjectController import proj_bp
from flask import Blueprint, render_template, redirect, url_for, session


def register_routes(app):
    app.register_blueprint(app_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(google_bp, url_prefix='/login')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(proj_bp, url_prefix='/api')


app_bp = Blueprint('app_bp', __name__)


@app_bp.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('auth_bp.login_page'))

    # check user role and redirect accordingly
    user = session['user']
    if user.get('role') == 'CUSTOMER':
        return redirect(url_for('user_bp.customer'))
    elif user.get('role') == 'TRANSLATOR':
        return redirect(url_for('user_bp.translator'))
    elif user.get('role') == 'ADMINISTRATOR':
        return redirect(url_for('user_bp.administrator'))
    else:
        return "Unknown role", 403


@app_bp.route('/administrator')
def administrator():
    # Administrator page logic here
    return render_template('pages/administrator.html')


@app_bp.route('/translator')
def translator():
    # Translator page logic here
    return render_template('pages/translator.html')