from models.DatabaseConnector import DatabaseConnector
from dotenv import load_dotenv
import os

load_dotenv()

db = None

def create_db_connection():
    """
    Create and return a DatabaseConnector instance using environment variables
    for configuration. This function reads the database connection parameters
    from the environment and initializes a DatabaseConnector object.

    Returns:
        DatabaseConnector: An instance of DatabaseConnector configured with
        the database connection parameters.
    """
    global db
    db = DatabaseConnector(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        user=os.getenv('DATABASE_USER', 'root'),
        password=os.getenv('DATABASE_PASSWORD', ''),
        database=os.getenv('DATABASE_NAME', 'test')
    )

create_db_connection()
