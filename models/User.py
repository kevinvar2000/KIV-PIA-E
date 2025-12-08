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
        """
        Convert a string to a corresponding User role enum member.

        This method normalizes the input by stripping whitespace and comparing
        case-insensitively against both the enum member's name and value.

        Parameters:
            value (str): The role represented as a string (e.g., "Admin", "admin").

        Returns:
            User: The matching enum member corresponding to the provided string.

        Raises:
            TypeError: If the provided value is not a string.
            ValueError: If no matching user role is found for the provided string.

        Examples:
            >>> User.from_string("Admin")
            <User.ADMIN: 'admin'>
            >>> User.from_string(" user ")
            <User.USER: 'user'>
        """
        if not isinstance(value, str):
            raise TypeError("Role value must be a string.")
        normalized = value.strip().lower()
        for role in cls:
            if role.value == normalized or role.name.lower() == normalized:
                return role
        raise ValueError(f"Unknown user role: {value}")


class User:

    def __init__(self, name: str, email: str, role: UserRole):
        """
        Initialize a new User instance.

        Parameters:
            name (str): The display name of the user.
            email (str): The user's email address.
            role (UserRole): The user's role within the system.

        Attributes:
            id (uuid.UUID): Unique identifier for the user, generated automatically.
            name (str): The display name of the user.
            email (str): The user's email address.
            role (UserRole): The user's role within the system.
            created_at (datetime): UTC timestamp when the user was created.
            _languages (list): Internal list of associated languages for the user.

        Returns:
            None
        """
        self.id = uuid.uuid4()
        self.name = name
        self.email = email
        self.role = role
        self.created_at = datetime.utcnow()
        self._languages = []


    @classmethod
    def create_customer(cls, name: str, email: str, hashed_password: str):
        """
        Create and persist a new customer user.
        Validates the provided name and email, constructs a User with the CUSTOMER role,
        and inserts the user into the database with the given hashed password.
        Parameters:
            name (str): Non-empty display name of the user.
            email (str): Non-empty email address containing '@'.
            hashed_password (str): Pre-hashed password to be stored for the user.
        Returns:
            User: The created user instance with a generated ID and timestamps.
        Raises:
            ValueError: If `name` is empty or not a string.
            ValueError: If `email` is empty, not a string, or does not contain '@'.
        """

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
        """
        Create a new translator user, persist it to the database, and associate language skills.
        Parameters:
            cls (Type[User]): The User class (used as a factory).
            name (str): Non-empty display name of the user.
            email (str): Valid email address containing "@".
            hashed_password (str): Pre-hashed password to be stored.
            languages (list): List of language identifiers/codes to assign to the user.
        Returns:
            User: The newly created translator user with languages set.
        Raises:
            ValueError: If `name` is empty or not a string.
            ValueError: If `email` is empty, not a string, or lacks "@".
            Exception: Propagates database or persistence-related errors when inserting the user or assigning languages.
        """

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
        """
        Retrieve a single user record by their exact username.
        This class method queries the Users table for a row with a matching `name`
        and returns the first result if found.
        Parameters:
            name (str): The exact username to look up.
        Returns:
            Optional[tuple]: A tuple containing (id, name, email, password, role, created_at)
            for the matched user, or None if no user with the given name exists.
        Notes:
            - If multiple rows match the same name, only the first result is returned.
            - The query uses a parameterized statement to prevent SQL injection.
        """
        
        result = db.execute_query(
            "SELECT id, name, email, password, role, created_at FROM Users WHERE name = %s",
            (name,)
        )
        
        return result[0] if result else None

    @property
    def languages(self):
        return self._languages


    def set_languages(self, languages):
        """
        Set the user's languages and persist them to the database.
        This method validates that the provided languages are a non-empty list of strings,
        assigns them to the user, and inserts each language into the Languages table
        associated with the user's ID.
        Parameters:
            languages (list[str]): A non-empty list of language names as strings.
        Raises:
            ValueError: If `languages` is empty, not a list, or contains non-string items.
        """
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
        """
        Retrieve a list of languages associated with the user.
        This method queries the database for all language entries linked to the
        current user's ID and returns them as a list of strings.
        Returns:
            list[str]: A list of language names for the user. If no languages are
                found, returns an empty list.
        Raises:
            Exception: Propagates any exceptions raised during database query execution.
        """
        result = db.execute_query(
            "SELECT language FROM Languages WHERE user_id = %s",
            (str(self.id),)
        )

        languages = [row['language'] for row in result]
        return languages
    
    @classmethod
    def get_all_users(cls):
        """
        Retrieve all users from the database.
        Executes a query to select user fields (id, name, email, role, created_at) from
        the Users table, constructs User instances from the results, and returns them
        as a list.
        Returns:
            list[User]: A list of User objects populated with database values.
        Raises:
            DatabaseError: If the database query fails.
            ValueError: If a user's role string cannot be parsed into a UserRole.
        """
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
        """
        Retrieve a user by their unique identifier.
        This class method queries the database for a user record with the given ID. If a
        matching record is found, it instantiates and returns a User object populated
        with the user's basic information (id, name, email, role, created_at). If no
        record is found, it returns None.
        Parameters:
            user_id (str): The unique identifier of the user to retrieve.
        Returns:
            Optional[User]: A User instance if found; otherwise, None.
        """
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
        """
        Retrieve all translators associated with a specific language code.
        This class method queries the database for users with the TRANSLATOR role
        who are linked to the provided language code via the Languages table. It
        constructs and returns a list of User instances populated with the queried
        fields.
        Parameters:
            language_code (str): The language identifier (e.g., "en", "de") used to
                filter translators.
        Returns:
            list: A list of User objects representing translators for the given language.
                Each User includes `id`, `name`, `email`, `role`, and `created_at`.
        Raises:
            DatabaseError: If the underlying database query fails.
            ValueError: If an invalid role value is encountered when converting to UserRole.
        """
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