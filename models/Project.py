from enum import Enum
from datetime import datetime
from models.User import User
from models.db import db
import uuid

class ProjectState(Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"


class Project:

    def __init__(self, customer_id: str, translator_id: str, language: str, original_file: str):
        self.id = str(uuid.uuid4())
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
            "INSERT INTO Projects (id, name, description, customerId, translatorId, languageCode, originalFile, translatedFile, state, createdAt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (str(project.id), project_name, description, str(customer_id), None, language, original_file, None, project.state.value, project.created_at)
        )

        print("Result of project creation:", result, flush=True)

        if not result:
            raise ValueError("Failed to create project in the database.")

        return project
    

    @staticmethod
    def get_by_user_id(user_id: str) -> list:

        result = db.execute_query(
            "SELECT * FROM Projects WHERE customerId = %s",
            (user_id,)
        )

        projects = []
        for row in result:
            project = Project(
                customer_id=row['customerId'],
                translator_id=row['translatorId'],
                language=row['languageCode'],
                original_file=row['originalFile']
            )
            project.translated_file = row['translatedFile']
            project.state = ProjectState(row['state'])
            project.created_at = row['createdAt']
            projects.append(project)

        return projects


    @staticmethod
    def assign_translator(project_id: str, translator_id: str) -> None:

        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if not translator_id or not isinstance(translator_id, str):
            raise ValueError("Translator ID must be a valid non-empty string.")

        db.execute_query(
            "UPDATE Projects SET translatorId = %s, state = %s WHERE id = %s",
            (translator_id, ProjectState.ASSIGNED.value, project_id)
        )


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


    @staticmethod
    def get_all() -> list:
        result = db.execute_query(
            "SELECT * FROM Projects"
        )
        projects = []
        for row in result:
            project = Project(
                customer_id=row['customerId'],
                translator_id=row['translatorId'],
                language=row['languageCode'],
                original_file=row['originalFile']
            )
            project.translated_file = row['translatedFile']
            project.state = ProjectState(row['state'])
            project.created_at = row['createdAt']
            projects.append(project)

        return projects


    @staticmethod
    def get_by_id(project_id: str) -> 'Project':
        result = db.execute_query(
            "SELECT * FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            return None

        row = result[0]
        project = Project(
            customer_id=row['customerId'],
            translator_id=row['translatorId'],
            language=row['languageCode'],
            original_file=row['originalFile']
        )
        project.translated_file = row['translatedFile']
        project.state = ProjectState(row['state'])
        project.created_at = row['createdAt']

        return project


    @staticmethod
    def update_status(project_id: str, status: str) -> None:
        result = db.execute_query(
            "UPDATE Projects SET state = %s WHERE id = %s",
            (status, project_id)
        )
        if not result:
            raise ValueError("Failed to update project status.")


