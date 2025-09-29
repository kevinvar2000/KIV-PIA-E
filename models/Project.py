from enum import Enum
from datetime import datetime

class ProjectState(Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"

class User:
    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email

class Project:
    def __init__(self, customer: User, translator: User, language: str, original_file: str):
        self.customer = customer
        self.translator = translator
        self.language = language
        self.original_file = original_file
        self.translated_file = None
        self.state = ProjectState.CREATED
        self.created_at = datetime.now()

    def create_project(self, customer: User, translator: User, language: str, original_file: str):

        # check if customer is valid
        if not isinstance(customer, User):
            raise ValueError("Customer must be a valid User instance.")
        # check if translator is valid
        if not isinstance(translator, User):
            raise ValueError("Translator must be a valid User instance.")
        # check if language is valid
        if not language or not isinstance(language, str):
            raise ValueError("Language must be a non-empty string.")
        # check if original_file is valid
        if not original_file or not isinstance(original_file, str):
            raise ValueError("Original file must be a non-empty string.")

        return Project(customer, translator, language, original_file)

    def assign_translator(self, translator: User):

        if not isinstance(translator, User):
            raise ValueError("Translator must be a valid User instance.")
        
        if self.state != ProjectState.CREATED:
            raise ValueError("Project must be in CREATED state to assign a translator.")

        self.translator = translator
        self.state = ProjectState.ASSIGNED

    def complete_translation(self, translated_file: str):

        if not translated_file or not isinstance(translated_file, str):
            raise ValueError("Translated file must be a non-empty string.")

        self.translated_file = translated_file
        self.state = ProjectState.COMPLETED

    def approve(self):

        if self.state != ProjectState.COMPLETED:
            raise ValueError("Project must be in COMPLETED state to be approved.")
    
        self.state = ProjectState.APPROVED

    def reject(self):
        if self.state != ProjectState.COMPLETED:
            raise ValueError("Project must be in COMPLETED state to be rejected.")
    
        self.state = ProjectState.ASSIGNED
        self.translated_file = None

    def close(self):

        if self.state != ProjectState.APPROVED:
            raise ValueError("Project must be in APPROVED state to be closed.")

        self.state = ProjectState.CLOSED