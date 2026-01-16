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
        """
        Initialize a new Project instance.

        Parameters:
            customer_id (str): Unique identifier of the customer who created the project.
            translator_id (str): Unique identifier of the translator assigned to the project.
            language (str): Target language for translation (e.g., 'en', 'cs').
            original_file (str): Path or identifier of the original file to be translated.

        Attributes:
            id (str): UUID of the project, generated automatically.
            customer_id (str): Identifier of the customer associated with the project.
            translator_id (str): Identifier of the translator assigned to the project.
            language (str): Target translation language for the project.
            original_file (str): Reference to the original file to be translated.
            translated_file (Optional[str]): Reference to the translated file; None until available.
            state (ProjectState): Current state of the project; initialized to ProjectState.CREATED.
            created_at (datetime): Timestamp of when the project was created.
            feedback (Optional[str]): Feedback from the customer or reviewer; None if not provided.
        """
        self.id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.translator_id = translator_id
        self.language = language
        self.original_file = original_file
        self.translated_file = None
        self.state = ProjectState.CREATED
        self.created_at = datetime.now()
        self.feedback = None
        self.name = None
        self.description = None


    @staticmethod
    def create_project(customer_id: str, project_name: str, description: str, language: str, original_file: bytes):
        """
        Create and persist a new project record.
        This function initializes a Project instance using the provided customer ID,
        language, and original file, then inserts the new project into the database.
        If the database operation fails, a ValueError is raised.
        Parameters:
            customer_id (str): Identifier of the customer owning the project.
            project_name (str): Human-readable name of the project.
            description (str): Detailed description of the project's purpose or content.
            language (str): Language code (e.g., "en", "cs") indicating the source language of the original file.
            original_file (bytes): Raw bytes of the original file to be translated.
        Returns:
            Project: The newly created Project instance with generated ID and timestamps.
        Raises:
            ValueError: If the project could not be inserted into the database.
        """

        project = Project(customer_id, None, language, original_file)
        project.name = project_name
        project.description = description

        result = db.execute_query(
            "INSERT INTO Projects (id, name, description, customerId, translatorId, languageCode, originalFile, translatedFile, state, createdAt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (str(project.id), project.name, project.description, str(customer_id), None, language, original_file, None, project.state.value, project.created_at)
        )

        print("Result of project creation:", result, flush=True)

        if not result:
            raise ValueError("Failed to create project in the database.")

        return project
    

    @staticmethod
    def get_by_user_id(user_id: str, role: str) -> list:
        """
        Retrieve projects associated with a specific user based on role.
        This function executes a parameterized SQL query to fetch rows from the
        Projects table where the specified role column matches the given user_id.
        The returned rows are converted into Project instances via Project.from_result.
        Parameters:
            user_id (str): The identifier of the user whose projects are requested.
            role (str): The column name representing the user's role in the project
                (e.g., 'owner_id', 'member_id'). Must be a valid column in the Projects table.
        Returns:
            list: A list of Project instances associated with the given user_id for the specified role.
        Notes:
            - The role parameter is interpolated directly into the SQL string. To prevent SQL injection,
              ensure it is validated/whitelisted against known column names before calling this function.
        """

        query = f"SELECT * FROM Projects WHERE {role} = %s"

        result = db.execute_query(
            query,
            (user_id,)
        )

        projects = Project.from_result(result)

        return projects


    @staticmethod
    def assign_translator(project_id: str, translator_id: str) -> None:
        """
        Assign a translator to a project and update the project state to ASSIGNED.
        This function validates the provided project and translator identifiers and,
        upon successful validation, updates the corresponding project record in the
        database by setting the translatorId and state fields.
        Parameters:
            project_id (str): The unique identifier of the project to update.
            translator_id (str): The unique identifier of the translator to assign.
        Raises:
            ValueError: If `project_id` is not a valid non-empty string.
            ValueError: If `translator_id` is not a valid non-empty string.
        Side Effects:
            Executes an UPDATE query on the Projects table to set:
                - translatorId = translator_id
                - state = ProjectState.ASSIGNED.value
        """

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
        """Fetch all projects from the database.
        Executes a query to retrieve every record from the Projects table and converts
        the results into a list of Project instances.
        Returns:
            list[Project]: A list of all projects found in the database.
        Raises:
            DatabaseError: If the database query fails.
        """
        result = db.execute_query(
            "SELECT * FROM Projects"
        )
        
        projects = Project.from_result(result)

        return projects


    @staticmethod
    def get_by_id(project_id: str) -> 'Project':
        """
        Retrieve a single Project by its unique identifier.
        This method queries the database for a project record with the given ID.
        If a matching record is found, it is converted to a Project instance.
        If no record exists, None is returned.
        Parameters:
            project_id (str): The unique identifier of the project to retrieve.
        Returns:
            Project | None: The Project instance if found; otherwise, None.
        Raises:
            DatabaseError: If the underlying database query fails (depending on db.execute_query implementation).
        """
        result = db.execute_query(
            "SELECT * FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            return None

        projects = Project.from_result(result)

        return projects[0] if projects else None


    @staticmethod
    def update_state(project_id: str, state: str) -> None:
        """
        Update the state of a project in the database.

        Args:
            project_id (str): Unique identifier of the project to update.
            state (str): New state value to set for the project.

        Raises:
            ValueError: If the database update fails.

        Returns:
            None
        """
        result = db.execute_query(
            "UPDATE Projects SET state = %s WHERE id = %s",
            (state, project_id)
        )
        if not result:
            raise ValueError("Failed to update project status.")


    @staticmethod
    def get_state(project_id: str) -> ProjectState:
        """
        Retrieve the current state of a project by its unique identifier.

        Args:
            project_id (str): The unique ID of the project whose state is being queried.

        Returns:
            ProjectState: The project's state as a ProjectState enum member.

        Raises:
            ValueError: If no project with the given ID exists in the database.

        Notes:
            - Expects a database row with a 'state' column containing a valid ProjectState value.
            - The returned value is converted into a ProjectState enum instance.
        """
        result = db.execute_query(
            "SELECT state FROM Projects WHERE id = %s",
            (project_id,)
        )
        if not result:
            raise ValueError("Project not found.")
        return ProjectState(result[0]['state'])

    @staticmethod
    def save_feedback(project_id: str, feedback: str) -> None:
        """
        Persist a feedback entry for a given project.
        Logs the operation details, executes an INSERT into the `Feedbacks` table
        with the provided project ID, feedback text, and the current UTC timestamp,
        and validates that the database operation succeeded.
        Parameters:
            project_id (str): Unique identifier of the project to associate the feedback with.
            feedback (str): The feedback text to be stored.
        Raises:
            ValueError: If the feedback could not be saved (e.g., the database operation failed).
        """

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
        """
        Retrieve the most recent feedback text for a given project.

        Parameters:
            project_id (str): The unique identifier of the project whose latest feedback is requested.

        Returns:
            str: The text content of the most recently created feedback associated with the project.

        Raises:
            ValueError: If no feedback is found for the specified project_id.
        """
        result = db.execute_query(
            "SELECT text FROM Feedbacks WHERE projectId = %s ORDER BY createdAt DESC LIMIT 1",
            (project_id,)
        )
        if not result:
            raise ValueError("Feedback not found.")
        return result[0]['text']


    @staticmethod
    def update_feedback(project_id: str, feedback: str) -> None:
        """
        Update the feedback entry associated with a project.

        This function updates the text and timestamp of a feedback record in the
        `Feedbacks` table for the given project ID. The timestamp is set to the
        current UTC time.

        Parameters:
            project_id (str): The unique identifier of the project whose feedback
                should be updated.
            feedback (str): The new feedback text to store.

        Raises:
            ValueError: If the update operation fails (e.g., no rows affected).
        """
        result = db.execute_query(
            "UPDATE Feedbacks SET text = %s, createdAt = %s WHERE projectId = %s",
            (feedback, datetime.utcnow(), project_id)
        )
        if not result:
            raise ValueError("Failed to update feedback for the project.")

    
    @staticmethod
    def save_translated_file(project_id: str, translated_file: bytes) -> None:
        """
        Save the translated file into the database for a specific project.
        This function updates the `translatedFile` column in the `Projects` table
        for the given project ID. If no rows are affected because the content is
        identical, the upload is still accepted and a message is printed.
        Parameters:
            project_id (str): Unique identifier of the project to update.
            translated_file (bytes): Binary content of the translated file to store.
        Raises:
            ValueError: If the database operation fails (e.g., query returns None).
        Side Effects:
            - Executes an UPDATE statement on the `Projects` table.
            - Prints a message when no changes are made but the upload is accepted.
        Returns:
            None
        """

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
        """
        Retrieve the original file associated with a project.
        This function queries the database for the 'originalFile' blob from the
        Projects table using the provided project ID. If no project is found, a
        ValueError is raised.
        Parameters:
            project_id (str): The unique identifier of the project to look up.
        Returns:
            bytes: The binary contents of the original file.
        Raises:
            ValueError: If no project with the given ID exists.
        """
        result = db.execute_query(
            "SELECT originalFile FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            raise ValueError("Project not found.")

        return result[0]['originalFile']


    @staticmethod
    def get_translated_file(project_id: str) -> bytes:
        """
        Retrieve the translated file associated with a specific project.
        This function queries the database for the translated file of the project
        identified by the given project ID. If no project is found, a ValueError is raised.
        Args:
            project_id (str): The unique identifier of the project.
        Returns:
            bytes: The binary content of the translated file.
        Raises:
            ValueError: If the project with the given ID does not exist.
        """
        result = db.execute_query(
            "SELECT translatedFile FROM Projects WHERE id = %s",
            (project_id,)
        )

        if not result:
            raise ValueError("Project not found.")

        return result[0]['translatedFile']


    @staticmethod
    def get_by_customer_id(customer_id: str) -> list:
        """
        Retrieve all projects associated with a specific customer.
        Args:
            customer_id (str): The unique identifier of the customer whose projects should be fetched.
        Returns:
            list: A list of Project instances corresponding to the given customer ID.
        Raises:
            DatabaseError: If the underlying database query fails.
            ValueError: If `customer_id` is empty or not a valid string.
        Notes:
            This function queries the `Projects` table by `customerId` and converts
            the result rows into `Project` objects using `Project.from_result`.
        """
        result = db.execute_query(
            "SELECT * FROM Projects WHERE customerId = %s",
            (customer_id,)
        )

        projects = Project.from_result(result)

        return projects


    @staticmethod
    def from_result(result) -> list:
        """
        Convert an iterable of database/result rows into a list of Project instances.
        Each row is expected to be a mapping (e.g., dict) containing project-related
        fields such as:
        - 'id': optional unique identifier for the project
        - 'customerId': customer identifier (fallback: empty string if missing/None)
        - 'translatorId': translator identifier (optional)
        - 'languageCode': language code (fallback: empty string if missing/None)
        - 'originalFile': original file reference/path (optional)
        - 'name': project name (optional)
        - 'description': project description (optional)
        - 'translatedFile': translated file reference/path (optional, set to None if missing)
        - 'state': project state; attempted to cast to ProjectState, defaults to ProjectState.CREATED on invalid value
        - 'createdAt': creation timestamp (optional)
        Parameters:
            result (Iterable[Mapping[str, Any]]): Iterable of rows (e.g., dicts) representing projects.
        Returns:
            list[Project]: A list of populated Project instances, one per row.
        Notes:
            - Missing or None values for 'customerId' and 'languageCode' are replaced with empty strings.
            - If 'state' is present but invalid, it falls back to ProjectState.CREATED.
            - Fields not present or explicitly None remain unset or defaulted on the Project instance.
        """
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

