import uuid
from datetime import datetime
from enum import Enum

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

    def create_customer(self, name: str, email: str):

        # check if name is valid
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")

        # check if email is valid
        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")

        return User(name, email, UserRole.CUSTOMER)
    
    def create_translator(self, name: str, email: str, languages: list):

        # check if name is valid
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        
        # check if email is valid
        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")
        
        # check if languages is valid
        if not languages or not isinstance(languages, list) or not all(isinstance(lang, str) for lang in languages):
            raise ValueError("Languages must be a non-empty list of strings.")

        user = User(name, email, UserRole.TRANSLATOR)
        user.set_languages(languages)
        return user

    @property
    def languages(self):
        return self._languages

    def set_languages(self, languages):
        if not isinstance(languages, list):
            raise ValueError("Languages must be a list.")
        self._languages = languages