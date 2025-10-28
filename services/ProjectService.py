import os
from models.Project import Project
from werkzeug.datastructures import FileStorage as _WSFileStorage
from bin.helper import MAX_FILE_SIZE_MB

class ProjectService:

    UPLOAD_FOLDER = 'uploads/'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


    @staticmethod
    def create_project(customer_id: str, project_name: str, description: str, target_language: str, source_file: _WSFileStorage) -> Project:
        """Create a new project for a customer."""
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a valid non-empty string.")

        if not project_name or not isinstance(project_name, str):
            raise ValueError("Project name must be a valid non-empty string.")

        if not description or not isinstance(description, str):
            raise ValueError("Description must be a valid non-empty string.")

        if not target_language or not isinstance(target_language, str):
            raise ValueError("Target language must be a valid non-empty string.")

        if source_file is None:
            raise ValueError("Source file is required.")
        
        filename = source_file.filename
        file_path = os.path.join(ProjectService.UPLOAD_FOLDER, filename)

        source_file.save(file_path)

        project = Project.create_project(customer_id, project_name, description, target_language, file_path)
        return project
    
    @staticmethod
    def get_projects_by_customer_id(customer_id: str) -> list:
        """Retrieve all projects for a given customer ID."""
        if not customer_id or not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a valid non-empty string.")

        projects = Project.get_by_customer_id(customer_id)
        return projects
    
    @staticmethod
    def get_project_by_id(project_id: str) -> Project:
        """Retrieve a project by its ID."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        project = Project.get_by_id(project_id)
        return project
    
    @staticmethod
    def update_project_status(project_id: str, status: str) -> None:
        """Update the status of a project."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if not status or not isinstance(status, str):
            raise ValueError("Status must be a valid non-empty string.")

        Project.update_status(project_id, status)

    @staticmethod
    def assign_translator_to_project(project_id: str, translator_id: str) -> None:
        """Assign a translator to a project."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if not translator_id or not isinstance(translator_id, str):
            raise ValueError("Translator ID must be a valid non-empty string.")
        
        Project.assign_translator(project_id, translator_id)
    