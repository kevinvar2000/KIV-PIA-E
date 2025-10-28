from datetime import datetime
from enum import Enum
from models.db import db
import uuid


class UserRole(Enum):

    ADMINISTRATOR = "administrator"
    CUSTOMER = "customer"
    TRANSLATOR = "translator"


class User:

    def __init__(self, name: str, email: str, role: UserRole):
        self.id = uuid.uuid4()
        self.name = name
        self.email = email
        self.role = role
        self.created_at = datetime.utcnow()
        self._languages = []


    @classmethod
    def create_customer(cls, name: str, email: str, hashed_password: str):

        # check if name is valid
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")

        # check if email is valid
        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")

        user = cls(name, email, UserRole.CUSTOMER)
        
        result = db.execute_query(
            "INSERT INTO Users (id, name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (str(user.id), user.name, user.email, hashed_password, user.role.value, user.created_at)
        )

        return user


    @classmethod
    def create_translator(cls, name: str, email: str, hashed_password: str, languages: list):

        # check if name is valid
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        
        # check if email is valid
        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")

        user = User(name, email, UserRole.TRANSLATOR)

        db.execute_query(
            "INSERT INTO Users (id, name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (str(user.id), user.name, user.email, hashed_password, user.role.value, user.created_at)
        )
        user.set_languages(languages)

        return user


    @classmethod
    def get_user_by_name(cls, name: str):
        
        result = db.execute_query(
            "SELECT id, name, email, password, role, created_at FROM Users WHERE name = %s",
            (name,)
        )
        
        print(f"User query result for name '{name}': {result}", flush=True)

        return result[0] if result else None

    @property
    def languages(self):
        return self._languages


    def set_languages(self, languages):
        # check if languages is valid
        if not languages or not isinstance(languages, list) or not all(isinstance(lang, str) for lang in languages):
            raise ValueError("Languages must be a non-empty list of strings.")
        self._languages = languages

        for lang in languages:
            db.execute_query(
                "INSERT INTO Languages (user_id, language) VALUES (%s, %s)",
                (str(self.id), lang)
            )