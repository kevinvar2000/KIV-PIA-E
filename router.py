from flask import render_template, redirect, url_for, Blueprint, request, session

app_bp = Blueprint('app_bp', __name__)

@app_bp.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('auth_bp.login'))

    # check user role and redirect accordingly
    user = session['user']
    if user.get('role') == 'customer':
        return redirect(url_for('app_bp.customer'))
    elif user.get('role') == 'translator':
        return redirect(url_for('app_bp.translator'))
    elif user.get('role') == 'administrator':
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