from flask import Flask
from router import register_routes
from models.db import db, create_db_connection
import secrets
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def create_app(config=None):
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

    if config:
        app.config.update(config)

    create_db_connection()
    db.connect()
    
    register_routes(app)

    print("[app.py] Flask application created and configured.", flush=True)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
