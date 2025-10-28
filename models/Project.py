from enum import Enum
from datetime import datetime
from models.User import User
from models.db import db

class ProjectState(Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"


class Project:

    def __init__(self, customer_id: str, translator_id: str, language: str, original_file: str):
        self.customer_id = customer_id
        self.translator_id = translator_id
        self.language = language
        self.original_file = original_file
        self.translated_file = None
        self.state = ProjectState.CREATED
        self.created_at = datetime.now()


    @staticmethod
    def create_project(customer_id: str, project_name: str, description: str, language: str, original_file: bytes):

        project = Project(customer_id, None, language, original_file)

        result = db.execute_query(
            "INSERT INTO Projects (customerId, translatorId, languageCode, originalFile, translatedFile, state, createdAt) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (customer_id, None, language, original_file, None, project.state.value, project.created_at)
        )

        return project


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