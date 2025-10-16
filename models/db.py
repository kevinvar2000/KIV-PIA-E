from models.DatabaseConnector import DatabaseConnector
from dotenv import load_dotenv
import os

load_dotenv()  # make sure .env values are loaded

db = DatabaseConnector(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    user=os.getenv('DATABASE_USER', 'root'),
    password=os.getenv('DATABASE_PASSWORD', ''),
    database=os.getenv('DATABASE_NAME', 'test')
)