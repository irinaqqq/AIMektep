from typing import Union
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from .crud import UserDatabase
from .schemas import UserCreate, UserUpdate, UserAdmin

class UserService:
    def __init__(
            self, 
            user_database: UserDatabase,
        ):
        self.user_database = user_database

    async def create_user(
        self,
        data: UserCreate,
        hashed_password: str,
        db: AsyncSession
    ) -> User:
        try:
            await self.get_user_by_email(data.email, db)
            raise HTTPException(status_code=400, detail=" User with this email already exists.")
        except HTTPException as e:
            if e.status_code != 404:
                raise e

        try:
            await self.user_database.get_objects(db, phone_number=data.phone_number)
            raise HTTPException(status_code=400, detail=" User with this phone number already exists.")
        except HTTPException as e:
            if e.status_code != 404:
                raise e

        return await self.user_database.create(
            db,
            {
                "email": data.email,
                "phone_number": data.phone_number,
                "password_hash": hashed_password,
                "role": data.role,
            }
        )


    async def update_user(self, user_id: int, data: Union[UserUpdate, dict], db: AsyncSession) -> User:
        return await self.user_database.update(db, db_obj=await self.user_database.get(db, user_id), obj_in=data)


    async def get_users(self, db: AsyncSession, skip: int, limit: int) -> tuple[list[UserAdmin], int]:
        users = await self.user_database.get_multi(db, skip, limit)
        total = await self.user_database.count(db)

        return users, total


    async def get_user_by_email(self, email: str, db: AsyncSession) -> User:
        return await self.user_database.get_objects(db, email=email)

    
    async def delete_user(self, id: int, db: AsyncSession):   
        await self.user_database.remove(db, id)