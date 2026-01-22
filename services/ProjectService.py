import os
from models.Project import Project, ProjectState
from werkzeug.datastructures import FileStorage as _WSFileStorage
from bin.helper import MAX_FILE_SIZE_MB
from services.UserService import UserService
from services.EmailService import EmailService

ALLOWED_TRANSITIONS = {
    ProjectState.ASSIGNED: [ProjectState.COMPLETED],
    ProjectState.COMPLETED: [ProjectState.APPROVED, ProjectState.REJECTED],
    ProjectState.REJECTED: [ProjectState.ASSIGNED, ProjectState.CLOSED],
    ProjectState.APPROVED: [ProjectState.CLOSED],
}

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
        """
        Create a new translation project for a customer, persist the uploaded source file,
        and attempt to auto-assign a translator based on the target language.
        Parameters:
            customer_id (str): Unique identifier of the customer creating the project. Must be a non-empty string.
            project_name (str): Human-readable name of the project. Must be a non-empty string.
            description (str): Description of the project. Must be a non-empty string.
            target_language (str): Language code or name the project should be translated into. Must be a non-empty string.
            source_file (_WSFileStorage): Uploaded file object containing the source content to translate. Must be provided
                and its size must not exceed MAX_FILE_SIZE_MB.
        Returns:
            Project: The newly created Project instance. If a translator is available for the target language,
            the translator is assigned; otherwise, the project state is set to CLOSED.
        Raises:
            ValueError: If any of the required string parameters are missing/invalid, if the source_file is not provided,
            or if the source_file exceeds the maximum allowed size.
        """

        if not customer_id or not isinstance(customer_id, str):
            print(f"[ProjectService.py] Invalid customer_id provided: {customer_id}", flush=True)
            raise ValueError("Customer ID must be a valid non-empty string.")

        if not project_name or not isinstance(project_name, str):
            print(f"[ProjectService.py] Invalid project_name provided: {project_name}", flush=True)
            raise ValueError("Project name must be a valid non-empty string.")

        if not description or not isinstance(description, str):
            print(f"[ProjectService.py] Invalid description provided: {description}", flush=True)
            raise ValueError("Description must be a valid non-empty string.")

        if not target_language or not isinstance(target_language, str):
            print(f"[ProjectService.py] Invalid target_language provided: {target_language}", flush=True)
            raise ValueError("Target language must be a valid non-empty string.")

        if source_file is None:
            print(f"[ProjectService.py] Source file is required.", flush=True)
            raise ValueError("Source file is required.")
        
        if source_file.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            print(f"[ProjectService.py] Source file exceeds maximum size: {source_file.content_length} bytes", flush=True)
            raise ValueError(f"Source file exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB.")

        filename = str(customer_id) + ProjectService.FILENAME_SEPARATOR + source_file.filename
        file_path = os.path.join(ProjectService.ORIGINAL_FILES_FOLDER, filename)

        source_file.save(file_path)

        project = Project.create_project(customer_id, project_name, description, target_language, filename)

        translators = UserService.get_translators_by_language(target_language)
        if translators:
            translator = translators[0]
            print(f"[ProjectService.py] Assigning translator {translator.id} to project {project.id}", flush=True)
            Project.assign_translator(project.id, translator.id)

            EmailService.send_email(
                email=translator.email,
                subject=f"New translation project assigned: {project_name}",
                body=f"You have been assigned to translate the project '{project_name}' into {target_language}."
            )
        else:
            print(f"[ProjectService.py] No translators available for language: {target_language}", flush=True)
            project.update_state(project.id, ProjectState.CLOSED.value)

            EmailService.send_email(
                email=UserService.get_user_by_id(customer_id).email,
                subject=f"Project closed: {project_name}",
                body=f"Your project '{project_name}' has been closed due to no available translators for the target language '{target_language}'."
            )

        return project

    @staticmethod
    def get_all_projects() -> list:
        """
        Retrieve all projects as plain serializable dictionaries.
        This function fetches all project instances via `Project.get_all()` and
        normalizes each item into a dictionary suitable for JSON serialization:
        - If an item is already a `dict`, it is used as-is.
        - If an item has a callable `to_dict()` method, that result is used.
        - Otherwise, a dictionary is constructed from the object's `__dict__` via `vars()`.
        For any `state` field that is an instance of `ProjectState`, the enum is converted
        to its underlying `.value` to ensure compatibility with JSON encoders.
        Returns:
            list[dict]: A list of serialized project dictionaries with enum fields converted
            to primitive values where applicable.
        Raises:
            AttributeError: If a non-dict, non-`to_dict` object lacks expected attributes.
        """

        projects = Project.get_all()

        serialized = []
        for p in projects:
            if isinstance(p, dict):
                data = p
            elif hasattr(p, "to_dict") and callable(getattr(p, "to_dict")):
                data = p.to_dict()
            else:
                data = {k: (v.value if isinstance(v, ProjectState) else v) for k, v in vars(p).items()}
            if "state" in data and isinstance(data["state"], ProjectState):
                data["state"] = data["state"].value
            serialized.append(data)

        return serialized

    @staticmethod
    def get_projects_by_user_id(user_id: str, role: str) -> list:
        """
        Retrieve all projects associated with a user based on their role.
        Parameters:
            user_id (str): The unique identifier of the user. Must be a non-empty string.
            role (str): The role of the user in the project context. Supported values are:
                - 'CUSTOMER': Fetch projects where the user is the customer.
                - 'TRANSLATOR': Fetch projects where the user is the translator.
        Returns:
            list: A list of Project instances associated with the given user and role.
        Raises:
            ValueError: If `user_id` is not a valid non-empty string.
            ValueError: If `role` is not a valid non-empty string.
            ValueError: If `role` is not one of the supported values ('CUSTOMER', 'TRANSLATOR').
        """

        if not user_id or not isinstance(user_id, str):
            print(f"[ProjectService.py] Invalid user_id provided: {user_id}", flush=True)
            raise ValueError("User ID must be a valid non-empty string.")

        if not role or not isinstance(role, str):
            print(f"[ProjectService.py] Invalid role provided: {role}", flush=True)
            raise ValueError("Role must be a valid non-empty string.")

        if role == 'CUSTOMER':
            projects = Project.get_by_user_id(user_id, "customerId")
        elif role == 'TRANSLATOR':
            projects = Project.get_by_user_id(user_id, "translatorId")
        else:
            print(f"[ProjectService.py] Unsupported role provided: {role}", flush=True)
            raise ValueError("Invalid role specified.")

        return projects
    
    @staticmethod
    def get_projects_by_customer_id(customer_id: str) -> list:
        """
        Retrieve all projects associated with a specific customer.
        Parameters:
            customer_id (str): The unique identifier of the customer. Must be a non-empty string.
        Returns:
            list: A list of Project instances associated with the given customer ID.
        Raises:
            ValueError: If `customer_id` is not a valid non-empty string.
        """

        if not customer_id or not isinstance(customer_id, str):
            print(f"[ProjectService.py] Invalid customer_id provided: {customer_id}", flush=True)
            raise ValueError("Customer ID must be a valid non-empty string.")

        projects = Project.get_by_user_id(customer_id, "customerId")
        projects = [Project.to_dict(p) for p in projects]
        return projects

    @staticmethod
    def get_project_by_id(project_id: str) -> Project:
        """
        Retrieve a project by its unique identifier.
        Parameters:
            project_id (str): The unique ID of the project to retrieve. Must be a non-empty string.
        Returns:
            Project: The project instance corresponding to the provided ID, or None if no such project exists.
        Raises:
            ValueError: If `project_id` is not a valid non-empty string.
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        project = Project.get_by_id(project_id)
        project = Project.to_dict(project) if project else None
        return project
    
    @staticmethod
    def update_project_status(project_id: str, status: str, actor: dict) -> None:
        """Update the status of a project."""

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        if not status or not isinstance(status, str):
            print(f"[ProjectService.py] Invalid status provided: {status}", flush=True)
            raise ValueError("Status must be a valid non-empty string.")

        if not actor:
            print(f"[ProjectService.py] Actor information is required.", flush=True)
            raise PermissionError("Actor information is required.")

        state = status.upper()

        try:
            new_state = ProjectState[state]
        except KeyError:
            print(f"[ProjectService.py] Unknown status provided: {status}", flush=True)
            raise ValueError("Invalid status value.")

        current_state = Project.get_state(project_id)

        allowed = ALLOWED_TRANSITIONS.get(current_state, [])
        if new_state not in allowed:
            print(f"[ProjectService.py] Invalid state transition from {current_state.value} to {new_state.value}", flush=True)
            raise ValueError("Invalid state transition.")

        role = actor.get('role')
        user_id = actor.get('id')

        project = Project.get_by_id(project_id)
        translator_id = project.translator_id
        customer_id = project.customer_id

        if new_state == ProjectState.COMPLETED:
            if role != "TRANSLATOR" or user_id != translator_id:
                raise PermissionError("Only assigned TRANSLATOR can complete the project.")

        elif new_state in (ProjectState.APPROVED, ProjectState.REJECTED):
            if role != "CUSTOMER" or user_id != customer_id:
                raise PermissionError("Only owning CUSTOMER can approve/reject the project.")

        elif new_state == ProjectState.CLOSED:
            if role != "ADMINISTRATOR":
                raise PermissionError("Only ADMINISTRATOR can close the project.")

        Project.update_state(project_id, new_state.value)

    @staticmethod
    def assign_translator_to_project(project_id: str, translator_id: str) -> None:
        """
        Assign a translator to a project.
        This function validates the provided project and translator identifiers,
        then delegates the assignment to the underlying Project model.
        Parameters:
            project_id (str): Unique identifier of the project to which the translator will be assigned.
            translator_id (str): Unique identifier of the translator to assign.
        Raises:
            ValueError: If `project_id` or `translator_id` is missing, empty, or not a string.
        Returns:
            None
        Example:
            assign_translator_to_project("proj_123", "trans_456")
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        if not translator_id or not isinstance(translator_id, str):
            print(f"[ProjectService.py] Invalid translator_id provided: {translator_id}", flush=True)
            raise ValueError("Translator ID must be a valid non-empty string.")

        Project.assign_translator(project_id, translator_id)


    @staticmethod
    def accept_translation(project_id: str) -> None:
        """
        Accept the translation for a project by transitioning its state from COMPLETED to APPROVED.
        This function validates the provided project ID, ensures the project is currently
        in the COMPLETED state, and then updates its state to APPROVED. If validation fails
        or the project is not in the correct state, a ValueError is raised.
        Args:
            project_id (str): The unique identifier of the project whose translation is being accepted.
        Raises:
            ValueError: If `project_id` is empty, not a string, or if the project's state is not COMPLETED.
        Side Effects:
            Updates the project's state in persistent storage to APPROVED.
            # Potential future side effect:
            # Notifies the translator of acceptance (currently commented out).
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state != ProjectState.COMPLETED:
            print(f"[ProjectService.py] Project {project_id} is not in COMPLETED state: {state}", flush=True)
            raise ValueError("Only projects in COMPLETED state can be accepted.")

        Project.update_state(project_id, ProjectState.APPROVED.value)

        project = Project.get_by_id(project_id)

        EmailService.send_email(
            email=UserService.get_user_by_id(project.translator_id).email,
            subject="Translation Accepted",
            body=f"Your translation for project '{project.name}' has been accepted."
        )


    @staticmethod
    def reject_translation(project_id: str, feedback: str) -> None:
        """
        Reject a completed project's translation with reviewer feedback.
        Validates inputs, ensures the project is in the COMPLETED state, transitions it
        to REJECTED, and stores or updates the provided feedback associated with the project.
        Args:
            project_id (str): Unique identifier of the project whose translation is being rejected.
            feedback (str): Explanation or notes detailing the reason for rejection.
        Raises:
            ValueError: If `project_id` is empty or not a string.
            ValueError: If `feedback` is empty or not a string.
            ValueError: If the project's state is not COMPLETED.
        Returns:
            None
        """
        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        if not feedback or not isinstance(feedback, str):
            print(f"[ProjectService.py] Invalid feedback provided: {feedback}", flush=True)
            raise ValueError("Feedback must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state != ProjectState.COMPLETED:
            print(f"[ProjectService.py] Project {project_id} is not in COMPLETED state: {state}", flush=True)
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
        
        project = Project.get_by_id(project_id)

        EmailService.send_email(
            email=UserService.get_user_by_id(project.translator_id).email,
            subject="Translation Rejected",
            body=f"Your translation for project '{project.name}' has been rejected. Feedback: {feedback}"
        )


    @staticmethod
    def close_project(project_id: str) -> None:
        """
        Close a project by setting its state to CLOSED.
        Parameters:
            project_id (str): Unique identifier of the project to close.
        Raises:
            ValueError: If `project_id` is empty or not a string.
            ValueError: If the project is already closed.
        Notes:
            This function updates the project's state to CLOSED. A future enhancement
            may include notifying users of the project closure.
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        state = Project.get_state(project_id)
        if state == ProjectState.CLOSED:
            print(f"[ProjectService.py] Project {project_id} is already closed.", flush=True)
            raise ValueError("Project is already closed.")

        Project.update_state(project_id, ProjectState.CLOSED.value)

        project = Project.get_by_id(project_id)

        EmailService.send_email(
            email=UserService.get_user_by_id(project.translator_id).email,
            subject="Project Closed",
            body=f"Your project '{project.name}' has been closed."
        )


    @staticmethod
    def get_original_file(project_id: str) -> tuple[str, str]:
        """
        Retrieve the path and original filename for a project's uploaded file.
        This method validates the provided project ID, fetches the associated original
        file identifier from the data layer, constructs the absolute file path in the
        original-files directory, and extracts the human-readable filename by removing
        the internal prefix/separator.
        Parameters:
            project_id (str): The unique identifier of the project. Must be a non-empty string.
        Returns:
            tuple[str, str]: A tuple containing:
                - file_path (str): The absolute path to the original file on disk.
                - filename (str): The original filename as presented to users (without internal prefix).
        Raises:
            ValueError: If `project_id` is empty or not a string.
            ValueError: If no original file is found for the given `project_id`.
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")
        
        file = Project.get_original_file(project_id)
        if not file:
            print(f"[ProjectService.py] Original file not found for project_id: {project_id}", flush=True)
            raise ValueError("Original file not found.")
        
        file_path = os.path.join(ProjectService.ORIGINAL_FILES_FOLDER, file)

        filename= file.split(ProjectService.FILENAME_SEPARATOR, 1)[1]

        return file_path, filename

    def get_translated_file(project_id: str) -> tuple[str, str]:
        """
        Retrieve the full filesystem path and original filename of a project's translated file.
        This function validates the provided project ID, locates the translated file
        associated with that project, and returns both the absolute path to the file
        and the original filename (excluding any internal prefixes used for storage).
        Parameters:
            project_id (str): The unique identifier of the project. Must be a non-empty string.
        Returns:
            tuple[str, str]: A tuple containing:
                - file_path (str): The full path to the translated file on disk.
                - filename (str): The original filename extracted from the stored file name.
        Raises:
            ValueError: If `project_id` is not a valid non-empty string.
            ValueError: If no translated file is found for the given project ID.
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")
        
        file = Project.get_translated_file(project_id)
        if not file:
            print(f"[ProjectService.py] Translated file not found for project_id: {project_id}", flush=True)
            raise ValueError("Translated file not found.")
        
        file_path =  os.path.join(ProjectService.TRANSLATED_FILES_FOLDER, file)

        filename= file.split(ProjectService.FILENAME_SEPARATOR, 1)[1]

        return file_path, filename


    @staticmethod
    def save_translated_file(project_id: str, translated_file: _WSFileStorage) -> None:
        """
        Save a translated file for the specified project and update its state to COMPLETED.
        This function validates the input parameters, ensures the uploaded file does not exceed
        the maximum allowed size, and checks that the project is in a valid state (ASSIGNED or REJECTED)
        for accepting a translated file. It then persists the file to storage, updates the project's
        record with the stored filename, and sets the project state to COMPLETED.
        Parameters:
            project_id (str): The unique identifier of the project. Must be a non-empty string.
            translated_file (_WSFileStorage): The uploaded file object containing the translated content.
        Raises:
            ValueError: If `project_id` is empty or not a string.
            ValueError: If `translated_file` is None.
            ValueError: If `translated_file` exceeds the maximum allowed size.
            ValueError: If the project's state is not ASSIGNED or REJECTED.
            ValueError: If the project cannot be found.
        """

        if not project_id or not isinstance(project_id, str):
            print(f"[ProjectService.py] Invalid project_id provided: {project_id}", flush=True)
            raise ValueError("Project ID must be a valid non-empty string.")

        if translated_file is None:
            print(f"[ProjectService.py] Translated file is required.", flush=True)
            raise ValueError("Translated file is required.")

        if translated_file.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            print(f"[ProjectService.py] Translated file exceeds maximum size: {translated_file.content_length} bytes", flush=True)
            raise ValueError(f"Translated file exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB.")

        state = Project.get_state(project_id)
        if state != ProjectState.ASSIGNED and state != ProjectState.REJECTED:
            print(f"[ProjectService.py] Project {project_id} is not in ASSIGNED or REJECTED state: {state}", flush=True)
            raise ValueError("Cannot upload translated file for a project that is not in ASSIGNED or REJECTED state.")
    
        filename = str(project_id) + ProjectService.FILENAME_SEPARATOR + translated_file.filename
        file_path = os.path.join(ProjectService.TRANSLATED_FILES_FOLDER, filename)

        translated_file.save(file_path)

        project = Project.get_by_id(project_id)
        if not project:
            print(f"[ProjectService.py] Project not found for project_id: {project_id}", flush=True)
            raise ValueError("Project not found.")

        Project.save_translated_file(project_id, filename)
        Project.update_state(project_id, ProjectState.COMPLETED.value)

        EmailService.send_email(
            email=UserService.get_user_by_id(project.customer_id).email,
            subject=f"Translated file uploaded for project {project.name}",
            body=f"The translated file for your project '{project.name}' has been uploaded and is now available."
        )


    @staticmethod
    def check_feedbacks(projects: list) -> None:
        """
        Check a collection of projects for a rejected state and attach feedback.
        This function iterates over a list of projects, which can be either serialized
        dicts or model instances. For each project that is in the REJECTED state, it
        retrieves feedback via Project.get_feedback(project_id). If feedback exists,
        it is added to the project:
        - For dict projects, the "feedback" key is set.
        - For model instances, the feedback attribute is set.
        If feedback cannot be retrieved (e.g., Project.get_feedback raises ValueError),
        the feedback is set to None.
        Parameters:
            projects (list): A list of project representations. Each element may be:
                - dict with keys "id" and "state"
                - a model instance with attributes `id` and `state` (where `state` may be
                  a ProjectState enum or its raw value)
        Returns:
            None: The function mutates the provided project objects in place.
        """

        for project in projects:
            # Support both dicts (serialized projects) and model objects
            if isinstance(project, dict):
                state = project.get("state")
                pid = project.get("id")
                is_rejected = state == ProjectState.REJECTED.value or state == ProjectState.REJECTED
            else:
                state = getattr(project, "state", None)
                norm_state = state.value if isinstance(state, ProjectState) else state
                pid = getattr(project, "id", None)
                is_rejected = norm_state == ProjectState.REJECTED.value

            if is_rejected and pid:
                # check if the feedback for the project already exists
                try:
                    feedback = Project.get_feedback(pid)
                except ValueError:
                    print(f"[ProjectService.py] Invalid feedback provided for project_id: {pid}", flush=True)
                    feedback = None

                if isinstance(project, dict):
                    project["feedback"] = feedback
                else:
                    project.feedback = feedback

    
    @staticmethod
    def get_all_project_states() -> list:
        """
        Retrieve all available project states.

        This utility function returns every value defined in the ProjectState enum,
        allowing callers to iterate, validate, or present the full set of possible
        states for a project.

        Returns:
            list[ProjectState]: A list containing all members of the ProjectState enum.
        """
        """Retrieve all possible project states."""

        return list(ProjectState)