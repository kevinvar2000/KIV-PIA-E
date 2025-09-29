from flask import render_template, redirect, url_for, Blueprint, request

app_bp = Blueprint('app_bp', __name__)

@app_bp.route('/')
def home():
    return redirect(url_for('app_bp.login'))

@app_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Email: {email}, Password: {password}", flush=True)

    return render_template('auth/login.html')

@app_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        languages = request.form.getlist('languages')

        print(f"Email: {email}, Password: {password}, Role: {role}, Languages: {languages}", flush=True)

    return render_template('auth/register.html')

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