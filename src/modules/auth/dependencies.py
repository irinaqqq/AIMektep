from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials

from models import User
from core.database import get_db
from .service import AuthService
from .jwt_service import JWTService
from core.dependencies import get_config
from .password_manager import PasswordManager
from modules.user.dependencies import get_user_service

token_scheme = HTTPBearer(auto_error=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=get_config().OAUTH2_TOKEN_URL)

def get_auth_service() -> AuthService:
    return AuthService(
        user_service=get_user_service(),
        password_manager=PasswordManager(),
        jwt_service=JWTService(
            algorithm=get_config().ALGORITHM,
            secret_key=get_config().SECRET_KEY, 
            access_expiry=get_config().ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_expiry=get_config().REFRESH_TOKEN_EXPIRE_MINUTES,
            ),
    )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    ) -> User:
    payload = auth_service.jwt_service.decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(status_code=403, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=403, detail="Invalid token payload")

    user = await auth_service.user_service.get_user_by_email(email, db)
    return user


async def admin_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have access to this resource")
    return current_user


def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(token_scheme)) -> str:
    return credentials.credentials