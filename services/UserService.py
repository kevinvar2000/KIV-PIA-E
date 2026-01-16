from models.User import User


class UserService:


    @staticmethod
    def create_user(name, email, hashed_password, role, languages):
        """
        Create a new user as either a CUSTOMER or TRANSLATOR.
        Parameters:
            name (str): Full name of the user. Must be a non-empty string.
            email (str): Email address of the user. Must contain "@" and be non-empty.
            hashed_password (str): Hashed password string. Must be non-empty.
            role (str): The role of the user, either 'CUSTOMER' or 'TRANSLATOR'.
            languages (list[str] | None): For translators, a list of supported language codes.
                Ignored for customers.
        Returns:
            User: An instance of the created user, either a customer or translator.
        Raises:
            ValueError: If 'role' is not 'CUSTOMER' or 'TRANSLATOR'.
            ValueError: If 'name' is missing or not a valid non-empty string.
            ValueError: If 'hashed_password' is missing or not a valid non-empty string.
            ValueError: If 'email' is missing, not a string, or does not contain "@".
        """

        if role not in ['CUSTOMER', 'TRANSLATOR']:
            print(f"[UserService.py] Invalid role provided: {role}", flush=True)
            raise ValueError("Role must be either 'CUSTOMER' or 'TRANSLATOR'.")

        if not name or not isinstance(name, str):
            print(f"[UserService.py] Invalid name provided: {name}", flush=True)
            raise ValueError("Name must be a valid non-empty string.")

        if not hashed_password or not isinstance(hashed_password, str):
            print(f"[UserService.py] Invalid hashed_password provided.", flush=True)
            raise ValueError("Hashed password must be a valid non-empty string.")

        if not email or not isinstance(email, str) or "@" not in email:
            print(f"[UserService.py] Invalid email provided: {email}", flush=True)
            raise ValueError("Email must be a valid non-empty string.")
        
        if role == 'TRANSLATOR' and (not languages or not isinstance(languages, list)) and len(languages) > 0:
            print(f"[UserService.py] Invalid languages provided for TRANSLATOR: {languages}", flush=True)
            raise ValueError("Languages must be a valid list of language codes for TRANSLATOR role.")

        user = User.create_customer(name, email, hashed_password) if role == 'CUSTOMER' else User.create_translator(name, email, hashed_password, languages)

        return user

    
    @staticmethod
    def get_user_by_name(name):
        """
        Retrieve a user's data by their username.
        Args:
            name (str): The username to look up.
        Returns:
            dict | object | None: The user data returned by `User.get_user_by_name(name)`,
            or None if no matching user is found.
        """

        user_data = User.get_user_by_name(name)

        if not user_data:
            print(f"[UserService.py] No user found with name: {name}", flush=True)
            return None

        return user_data

    
    @staticmethod
    def get_user_by_email(email):
        """
        Retrieve a user's data by their email address.
        Args:
            email (str): The email address to look up.
        Returns:
            dict | object | None: The user data returned by `User.get_user_by_email(email)`,
            or None if no matching user is found.
        """

        user_data = User.get_user_by_email(email)

        if not user_data:
            print(f"[UserService.py] No user found with email: {email}", flush=True)
            return None

        return user_data


    
    @staticmethod
    def get_all_users():
        """
        Retrieve all users and return their serialized representations.
        Returns:
            list[dict]: A list of dictionaries, each representing a user.
        Raises:
            Exception: Propagates any unexpected errors from the underlying data access layer.
        """

        users = User.get_all_users()
        users_dict = [UserService.user_to_dict(user) for user in users]

        return users_dict


    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        """
        Retrieve a user by their unique identifier.
        Parameters:
            user_id (str): The unique ID of the user to fetch. Must be a non-empty string.
        Returns:
            User: The user instance corresponding to the provided ID.
        Raises:
            ValueError: If `user_id` is not a valid non-empty string.
        """

        if not user_id or not isinstance(user_id, str):
            print(f"[UserService.py] Invalid user_id provided: {user_id}", flush=True)
            raise ValueError("User ID must be a valid non-empty string.")

        user = User.get_user_by_id(user_id)

        return user


    @staticmethod
    def get_translators_by_language(language_code: str) -> list:
        """
        Retrieve a list of translators proficient in the specified language.
        This function validates the provided language code and delegates the query
        to the underlying data layer to fetch translators who can work with that language.
        Parameters:
            language_code (str): The ISO language code (e.g., "en", "de", "cs") for which
                to find proficient translators. Must be a non-empty string.
        Returns:
            list: A list of translator records/users proficient in the given language.
                The exact structure of each item depends on the `User.get_translators_by_language`
                implementation (e.g., dicts or model instances).
        Raises:
            ValueError: If `language_code` is empty or not a string.
        Examples:
            >>> get_translators_by_language("en")
            [<UserTranslator id=1 ...>, <UserTranslator id=7 ...>]
        """
        """Retrieve all translators proficient in a given language."""

        if not language_code or not isinstance(language_code, str):
            print(f"[UserService.py] Invalid language_code provided: {language_code}", flush=True)
            raise ValueError("Language code must be a valid non-empty string.")

        translators = User.get_translators_by_language(language_code)

        return translators
    
    @staticmethod
    def user_to_dict(user: User) -> dict:
        """
        Convert a User domain instance into a serializable dictionary.

        This helper normalizes key user attributes for transport or storage,
        including converting the UUID-like identifier to a string, the role
        enum to its value, and the creation timestamp to ISO 8601 format.

        Parameters:
            user (User): The user model instance to serialize. Must provide:
                - id: unique identifier (converted to str)
                - name: display name
                - email: email address
                - role: enum with a .value string
                - created_at: datetime with .isoformat()
                - get_languages(): method returning a list of language codes or names

        Returns:
            dict: A dictionary with keys:
                - 'id' (str)
                - 'name' (str)
                - 'email' (str)
                - 'role' (str)
                - 'created_at' (str, ISO 8601)
                - 'languages' (list)

        Raises:
            AttributeError: If required attributes or methods are missing from the user.
            ValueError: If fields cannot be serialized (e.g., invalid datetime).
        """

        return {
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'role': user.role.value,
            'created_at': user.created_at.isoformat(),
            'languages': user.get_languages()
        }