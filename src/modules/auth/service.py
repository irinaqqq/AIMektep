from fastapi import HTTPException
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from .jwt_service import JWTService
from modules.user.schemas import UserCreate
from modules.user.service import UserService
from .password_manager import PasswordManager

class AuthService:
    def __init__(
        self,
        jwt_service: JWTService,
        password_manager: PasswordManager,
        user_service: UserService,
    ):
        self.jwt_service = jwt_service
        self.password_manager = password_manager
        self.user_service = user_service
        self.revoked_tokens: set[str] = set()

    async def register_user(self, data: UserCreate, db: AsyncSession):
        await self.user_service.create_user(data, self.password_manager.hash_password(data.password), db)
        return await self.authenticate_user(data.email, data.password, db)


    async def authenticate_user(self, email: str, password: str, db: AsyncSession):
        user = await self.user_service.get_user_by_email(email, db)

        if not self.password_manager.verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect password")

        access_token = self.jwt_service.generate_access_token(user)
        refresh_token = self.jwt_service.generate_refresh_token(user)

        return access_token, refresh_token


    async def refresh_token(self, token: str, db: AsyncSession):
        payload = self.jwt_service.decode_token(token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=403, detail="Invalid token type")

        jti = payload.get("jti")
        if jti in self.revoked_tokens:
            raise HTTPException(status_code=403, detail="Refresh token revoked")

        email = payload.get("sub")
        user = await self.user_service.get_user_by_email(email, db)

        return self.jwt_service.generate_access_token(user)


    async def process_change_password(self, token: str, new_password: str, db: AsyncSession):
        payload = self.jwt_service.decode_token(token)
        if payload.get("type") != "recovery":
            raise HTTPException(status_code=403, detail="Invalid token type")

        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        hashed = self.password_manager.hash_password(new_password)
        user = await self.user_service.update_user(user_id, {"password_hash": hashed}, db)
        return await self.authenticate_user(user.email, new_password, db)
    

    async def logout_user(self, refresh_token: str):
        payload = self.jwt_service.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=403, detail="Invalid token type")

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=403, detail="Invalid token payload")

        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            raise HTTPException(status_code=403, detail="Invalid token payload")

        ttl = exp_timestamp - int(datetime.now(timezone.utc).timestamp())
        if ttl <= 0:
            logger.info(f"Refresh token already expired (jti={jti}), skipping revoke.")
            return

        self.revoked_tokens.add(jti)