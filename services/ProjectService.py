import os
from models.Project import Project, ProjectState
from werkzeug.datastructures import FileStorage as _WSFileStorage
from bin.helper import MAX_FILE_SIZE_MB
from services.UserService import UserService

class ProjectService:

    PROJECTS_FOLDER = 'projects/'
    ORIGINAL_FILES_FOLDER = os.path.join(PROJECTS_FOLDER, 'original_files/')
    TRANSLATED_FILES_FOLDER = os.path.join(PROJECTS_FOLDER, 'translated_files/')
    FILENAME_SEPARATOR = '_'

    os.makedirs(PROJECTS_FOLDER, exist_ok=True)
    os.makedirs(ORIGINAL_FILES_FOLDER, exist_ok=True)
    os.makedirs(TRANSLATED_FILES_FOLDER, exist_ok=True)

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
        
        if source_file.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Source file exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB.")

        filename = str(customer_id) + ProjectService.FILENAME_SEPARATOR + source_file.filename
        file_path = os.path.join(ProjectService.ORIGINAL_FILES_FOLDER, filename)

        source_file.save(file_path)

        project = Project.create_project(customer_id, project_name, description, target_language, filename)

        translators = UserService.get_translators_by_language(target_language)
        if translators:
            translator = translators[0]
            print(f"Assigning translator {translator.id} to project {project.id}", flush=True)
            Project.assign_translator(project.id, translator.id)

            # UserService.notify_translator(translator.id, project.id)
        else:
            print(f"No translators available for language: {target_language}", flush=True)
            project.update_state(project.id, ProjectState.CLOSED.value)

            # UserService.notify_customer(customer_id, project.id)

        return project

    @staticmethod
    def get_all_projects() -> list:
        """Retrieve all projects."""
        projects = Project.get_all()
        # projects_dict = [ProjectService.project_to_dict(p) for p in projects]
        # return projects_dict
        return projects

    @staticmethod
    def get_projects_by_user_id(user_id: str, role: str) -> list:
        """Retrieve all projects for a given user ID."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a valid non-empty string.")

        if not role or not isinstance(role, str):
            raise ValueError("Role must be a valid non-empty string.")

        if role == 'CUSTOMER':
            projects = Project.get_by_user_id(user_id, "customerId")
        elif role == 'TRANSLATOR':
            projects = Project.get_by_user_id(user_id, "translatorId")
        else:
            raise ValueError("Invalid role specified.")

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

        Project.update_state(project_id, status)

    @staticmethod
    def assign_translator_to_project(project_id: str, translator_id: str) -> None:
        """Assign a translator to a project."""

        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if not translator_id or not isinstance(translator_id, str):
            raise ValueError("Translator ID must be a valid non-empty string.")

        Project.assign_translator(project_id, translator_id)

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        """Convert a Project object to a dictionary representation."""
        return {
            'id': str(project.id),
            'customer_id': str(project.customer_id),
            'translator_id': str(project.translator_id) if project.translator_id else None,
            'language': project.language,
            'state': project.state.value,
            'created_at': project.created_at.isoformat()
        }


    @staticmethod
    def accept_translation(project_id: str) -> None:
        """Accept the translation for a project."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state != ProjectState.COMPLETED:
            raise ValueError("Only projects in COMPLETED state can be accepted.")

        Project.update_state(project_id, ProjectState.APPROVED.value)

        # UserService.notify_translator_of_acceptance(project_id)


    @staticmethod
    def reject_translation(project_id: str, feedback: str) -> None:
        """Reject the translation for a project with feedback."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if not feedback or not isinstance(feedback, str):
            raise ValueError("Feedback must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state != ProjectState.COMPLETED:
            raise ValueError("Only projects in COMPLETED state can be rejected.")

        Project.update_state(project_id, ProjectState.REJECTED.value)
        # check if the feedback for the project already exists
        try:
            existing_feedback = Project.get_feedback(project_id)
        except ValueError:
            existing_feedback = None

        if existing_feedback:
            Project.update_feedback(project_id, feedback)
        else:
            Project.save_feedback(project_id, feedback)
        
        # UserService.notify_translator_of_rejection(project_id, feedback)


    @staticmethod
    def close_project(project_id: str) -> None:
        """Close a project."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state == ProjectState.CLOSED:
            raise ValueError("Project is already closed.")

        Project.update_state(project_id, ProjectState.CLOSED.value)

        # UserService.notify_users_of_closure(project_id)


    @staticmethod
    def get_original_file(project_id: str) -> tuple[str, str]:
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")
        
        file = Project.get_original_file(project_id)
        if not file:
            raise ValueError("Original file not found.")
        
        file_path = os.path.join(ProjectService.ORIGINAL_FILES_FOLDER, file)

        filename= file.split(ProjectService.FILENAME_SEPARATOR, 1)[1]

        return file_path, filename

    def get_translated_file(project_id: str) -> tuple[str, str]:
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")
        
        file = Project.get_translated_file(project_id)
        if not file:
            raise ValueError("Translated file not found.")
        
        file_path =  os.path.join(ProjectService.TRANSLATED_FILES_FOLDER, file)

        filename= file.split(ProjectService.FILENAME_SEPARATOR, 1)[1]

        return file_path, filename


    @staticmethod
    def save_translated_file(project_id: str, translated_file: _WSFileStorage) -> None:
        """Save the translated file for a project."""
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a valid non-empty string.")

        if translated_file is None:
            raise ValueError("Translated file is required.")

        if translated_file.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Translated file exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB.")

        state = Project.get_state(project_id)
        if state != ProjectState.ASSIGNED:
            raise ValueError("Cannot upload translated file for a project that is not in ASSIGNED state.")

        filename = str(project_id) + ProjectService.FILENAME_SEPARATOR + translated_file.filename
        file_path = os.path.join(ProjectService.TRANSLATED_FILES_FOLDER, filename)

        translated_file.save(file_path)

        project = Project.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found.")

        Project.save_translated_file(project_id, filename)
        Project.update_state(project_id, ProjectState.COMPLETED.value)

        # UserService.notify_customer(project.customer_id, project.id)


    @staticmethod
    def check_feedbacks(projects: list) -> None:
        """Check projects for rejected status and print feedbacks."""
        for project in projects:
            if project.state == ProjectState.REJECTED:
                # check if the feedback for the project already exists
                try:
                    feedback = Project.get_feedback(project.id)
                except ValueError:
                    feedback = None
                project.feedback = feedback

    
    @staticmethod
    def get_all_project_states() -> list:
        """Retrieve all possible project states."""
        return list(ProjectState)