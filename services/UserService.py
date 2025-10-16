from models.User import User


class UserService:


    @staticmethod
    def create_user(name, email, hashed_password, role, languages):

        if role not in ['customer', 'translator']:
            raise ValueError("Role must be either 'customer' or 'translator'.")

        if not name or not isinstance(name, str):
            raise ValueError("Name must be a valid non-empty string.")

        if not email or not isinstance(email, str) or "@" not in email:
            raise ValueError("Email must be a valid non-empty string.")

        User.create_customer(name, email, hashed_password) if role == 'customer' else User.create_translator(name, email, hashed_password, languages)

    
    @staticmethod
    def get_user_by_name(name):

        user_data = User.get_user_by_name(name)

        if not user_data:
            return None

        return user_data