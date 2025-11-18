from datetime import datetime
from enum import Enum
from models.db import db
import uuid


class UserRole(Enum):
    ADMINISTRATOR = "administrator"
    CUSTOMER = "customer"
    TRANSLATOR = "translator"

    @classmethod
    def from_string(cls, value: str):
        if not isinstance(value, str):
            raise TypeError("Role value must be a string.")
        normalized = value.strip().lower()
        for role in cls:
            if role.value == normalized or role.name.lower() == normalized:
                return role
        raise ValueError(f"Unknown user role: {value}")


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

    def get_languages(self):
        result = db.execute_query(
            "SELECT language FROM Languages WHERE user_id = %s",
            (str(self.id),)
        )

        languages = [row['language'] for row in result]
        return languages
    
    @classmethod
    def get_all_users(cls):
        result = db.execute_query(
            "SELECT id, name, email, role, created_at FROM Users"
        )

        users = []
        for row in result:
            user = cls(
                name=row['name'],
                email=row['email'],
                role=UserRole.from_string(row['role'])
            )
            user.id = row['id']
            user.created_at = row['created_at']
            users.append(user)

        return users
    

    @classmethod
    def get_user_by_id(cls, user_id: str):
        result = db.execute_query(
            "SELECT id, name, email, password, role, created_at FROM Users WHERE id = %s",
            (user_id,)
        )

        if not result:
            return None

        row = result[0]
        user = cls(
            name=row['name'],
            email=row['email'],
            role=UserRole.from_string(row['role'])
        )
        user.id = row['id']
        user.created_at = row['created_at']

        return user


    @classmethod
    def get_translators_by_language(cls, language_code: str) -> list:
        result = db.execute_query(
            "SELECT u.id, u.name, u.email, u.role, u.created_at FROM Users u "
            "JOIN Languages l ON u.id = l.user_id "
            "WHERE l.language = %s AND u.role = %s",
            (language_code, UserRole.TRANSLATOR.value)
        )

        translators = []
        for row in result:
            translator = cls(
                name=row['name'],
                email=row['email'],
                role=UserRole.from_string(row['role'])
            )
            translator.id = row['id']
            translator.created_at = row['created_at']
            translators.append(translator)

        return translators