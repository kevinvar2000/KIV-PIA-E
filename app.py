from flask import Flask
from router import register_routes
from models.db import db
import secrets
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def create_app():
    """
    Create and configure the Flask application instance.
    This factory function initializes a new Flask app, generates a secure
    secret key for session management, establishes a database connection,
    and registers all application routes.
    Returns:
        Flask: A fully configured Flask application ready to run.
    """

    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)

    db.connect()
    
    register_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
