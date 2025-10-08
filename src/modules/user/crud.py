from core.crudbase import CRUDBase
from models import User
from .schemas import UserCreate, UserUpdate


class UserDatabase(CRUDBase[User, UserCreate, UserUpdate]):
    pass
