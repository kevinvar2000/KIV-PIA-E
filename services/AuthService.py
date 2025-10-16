from services.UserService import UserService
import hashlib


class AuthService:


    @staticmethod
    def register_user(name, email, hashed_password, role, languages):
        print(f"Registering user: {name}, {email}, {role}, {languages}", flush=True)
        UserService.create_user(name, email, hashed_password, role, languages)


    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    

    @staticmethod
    def authenticate_user(name, password):

        hashed_password = AuthService.hash_password(password)

        user_data = UserService.get_user_by_name(name)

        if user_data and user_data.get('password') == hashed_password:
            return user_data
        
        return None