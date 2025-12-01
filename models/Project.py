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
    REJECTED = "REJECTED"
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
        self.feedback = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'translator_id': self.translator_id,
            'language': self.language,
            'state': self.state.value,
            'created_at': self.created_at.isoformat()
        }


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
    def get_by_user_id(user_id: str, role: str) -> list:

        query = f"SELECT * FROM Projects WHERE {role} = %s"

        result = db.execute_query(
            query,
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
            project.id = row['id']
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


    @staticmethod
    def get_all() -> list:
        result = db.execute_query(
            "SELECT * FROM Projects"
        )
        projects = []
        for row in result:
            project = Project(
                customer_id=row.get('customerId') or '',
                translator_id=row.get('translatorId'),
                language=row.get('languageCode') or '',
                original_file=row.get('originalFile')
            )
            project.id = row.get('id', project.id)

            name = row.get('name')
            if name is not None:
                project.name = name

            description = row.get('description')
            if description is not None:
                project.description = description

            translated = row.get('translatedFile')
            project.translated_file = translated if translated is not None else None

            state_val = row.get('state')
            if state_val:
                try:
                    project.state = ProjectState(state_val)
                except ValueError:
                    project.state = ProjectState.CREATED

            created_at = row.get('createdAt')
            if created_at is not None:
                project.created_at = created_at

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
    def update_state(project_id: str, state: str) -> None:
        result = db.execute_query(
            "UPDATE Projects SET state = %s WHERE id = %s",
            (state, project_id)
        )
        if not result:
            raise ValueError("Failed to update project status.")


    @staticmethod
    def get_state(project_id: str) -> ProjectState:
        result = db.execute_query(
            "SELECT state FROM Projects WHERE id = %s",
            (project_id,)
        )
        if not result:
            raise ValueError("Project not found.")
        return ProjectState(result[0]['state'])

    @staticmethod
    def save_feedback(project_id: str, feedback: str) -> None:

        print( "Saving feedback:", project_id, feedback, flush=True)
        print(f"Query:",
               "INSERT INTO Feedbacks (projectId, text, createdAt) VALUES (%s, %s, %s)",
               (project_id, feedback, datetime.utcnow()), flush=True)

        result = db.execute_query(
            "INSERT INTO Feedbacks (projectId, text, createdAt) VALUES (%s, %s, %s)",
            (project_id, feedback, datetime.utcnow())
        )

        print("Result of saving feedback:", result, flush=True)
        
        if not result:
            raise ValueError("Failed to save feedback for the project.")


    @staticmethod
    def get_feedback(project_id: str) -> str:
        result = db.execute_query(
            "SELECT text FROM Feedbacks WHERE projectId = %s ORDER BY createdAt DESC LIMIT 1",
            (project_id,)
        )
        if not result:
            raise ValueError("Feedback not found.")
        return result[0]['text']


    @staticmethod
    def update_feedback(project_id: str, feedback: str) -> None:
        result = db.execute_query(
            "UPDATE Feedbacks SET text = %s, createdAt = %s WHERE projectId = %s",
            (feedback, datetime.utcnow(), project_id)
        )
        if not result:
            raise ValueError("Failed to update feedback for the project.")

    
    @staticmethod
    def save_translated_file(project_id: str, translated_file: bytes) -> None:

        result = db.execute_query(
            "UPDATE Projects SET translatedFile = %s WHERE id = %s",
            (translated_file, project_id)
        )

        if result is None:
            raise ValueError("Failed to save translated file for the project.")

        if result == 0:
            print("No changes were made (file identical), but upload is accepted.")
    

    @staticmethod
    def get_original_file(project_id: str) -> bytes:
        result = db.execute_query(
            "SELECT originalFile FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            raise ValueError("Project not found.")

        return result[0]['originalFile']


    @staticmethod
    def get_translated_file(project_id: str) -> bytes:
        result = db.execute_query(
            "SELECT translatedFile FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            raise ValueError("Project not found.")

        return result[0]['translatedFile']


    @staticmethod
    def get_by_customer_id(customer_id: str) -> list:
        result = db.execute_query(
            "SELECT * FROM Projects WHERE customerId = %s",
            (customer_id,)
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