from flask import Flask
from router import app_bp
from auth import auth_bp, google_bp
from models.DatabaseConnector import DatabaseConnector
import secrets
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.register_blueprint(app_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(google_bp, url_prefix='/login')

app.secret_key = secrets.token_hex(32)

database_connector = DatabaseConnector(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    user=os.getenv('DATABASE_USER', 'root'),
    password=os.getenv('DATABASE_PASSWORD', ''),
    database=os.getenv('DATABASE_NAME', 'test')
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
