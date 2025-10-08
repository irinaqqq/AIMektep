import jwt
import uuid
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from models import User
from core.logger import logger

class JWTService:
    def __init__(
        self,
        algorithm: str,
        secret_key: str, 
        access_expiry: int,
        refresh_expiry: int,
        ):
        self.algorithm = algorithm
        self.secret_key = secret_key
        self.access_expiry_timedelta = timedelta(minutes=access_expiry)
        self.refresh_expiry_timedelta = timedelta(minutes=refresh_expiry)

    def generate_access_token(self, user: User) -> str:
        payload = {
            "sub": user.email,
            "id": user.id,
            "role": user.role,
            "type": "access",
            "jti": str(uuid.uuid4()),
        }
        return self.create_token(payload, self.access_expiry_timedelta)


    def generate_refresh_token(self, user: User) -> str:
        payload = {
            "sub": user.email,
            "id": user.id,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        }
        return self.create_token(payload, self.refresh_expiry_timedelta)


    def create_token(self, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        to_encode.update({
            "iat": now,
            "exp": expire
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(status_code=403, detail="Token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            raise HTTPException(status_code=403, detail="Invalid token")
