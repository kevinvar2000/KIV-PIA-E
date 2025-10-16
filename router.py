from controllers.AuthController import auth_bp, google_bp
from flask import Blueprint, render_template, redirect, url_for, session


def register_routes(app):
    app.register_blueprint(app_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(google_bp, url_prefix='/login')


app_bp = Blueprint('app_bp', __name__)


@app_bp.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('auth_bp.login'))

    # check user role and redirect accordingly
    user = session['user']
    if user.get('role') == 'CUSTOMER':
        return redirect(url_for('app_bp.customer'))
    elif user.get('role') == 'TRANSLATOR':
        return redirect(url_for('app_bp.translator'))
    elif user.get('role') == 'ADMINISTRATOR':
        return redirect(url_for('app_bp.administrator'))
    else:
        return "Unknown role", 403


@app_bp.route('/customer')
def customer():
    # Customer page logic here
    return render_template('pages/customer.html')


@app_bp.route('/administrator')
def administrator():
    # Administrator page logic here
    return render_template('pages/administrator.html')


@app_bp.route('/translator')
def translator():
    # Translator page logic here
    return render_template('pages/translator.html')