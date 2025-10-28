from models.User import User


class UserService:


    @staticmethod
    def create_user(name, email, hashed_password, role, languages):

        if role not in ['CUSTOMER', 'TRANSLATOR']:
            raise ValueError("Role must be either 'CUSTOMER' or 'TRANSLATOR'.")

        if not name or not isinstance(name, str):
            raise ValueError("Name must be a valid non-empty string.")

        if not hashed_password or not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be a valid non-empty string.")

        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")

        user = User.create_customer(name, email, hashed_password) if role == 'CUSTOMER' else User.create_translator(name, email, hashed_password, languages)

        return user

    
    @staticmethod
    def get_user_by_name(name):

        user_data = User.get_user_by_name(name)

        if not user_data:
            return None

        return user_data