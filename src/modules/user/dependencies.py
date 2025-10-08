from .crud import UserDatabase
from .service import UserService
from models import User

def get_user_service() -> UserService:
    return UserService(
        user_database=UserDatabase(User),
    )