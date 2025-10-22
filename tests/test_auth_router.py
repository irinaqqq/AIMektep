from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from core.database import get_db
from schemas import StatusResponse
from modules.user.schemas import UserCreate
from modules.auth.service import AuthService
from modules.auth.schemas import TokenResponse, SimpleLoginForm
from modules.auth.dependencies import (
    get_auth_service,
    get_bearer_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authorization"])

# ---------------------------
# Register
# ---------------------------
@router.post("/register", response_model=TokenResponse, summary="Register a new user")
async def register_user_route(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token, refresh_token = await auth_service.register_user(payload, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

# ---------------------------
# Login (нужен тестам)
# ---------------------------
@router.post("/login", response_model=TokenResponse, summary="Login user and issue tokens")
async def login_user_route(
    form: SimpleLoginForm,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token, refresh_token = await auth_service.authenticate_user(
        form.username, form.password, db
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

# ---------------------------
# Refresh (алиас под тесты)
# ---------------------------
@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_access_token_route(
    db: AsyncSession = Depends(get_db),
    refresh_token: str = Depends(get_bearer_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = await auth_service.refresh_access_token(refresh_token, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

# (если хочешь сохранить старый путь, оставь алиас)
@router.post("/token/refresh", response_model=TokenResponse, summary="Refresh access token (alias)")
async def refresh_token_route(
    db: AsyncSession = Depends(get_db),
    refresh_token: str = Depends(get_bearer_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = await auth_service.refresh_access_token(refresh_token, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

# ---------------------------
# Logout
# ---------------------------
@router.post("/logout", response_model=StatusResponse, summary="Logout user")
async def logout_user_route(
    refresh_token: str = Depends(get_bearer_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout_user(refresh_token)
    return StatusResponse(message="Logged out successfully")

# ---------------------------
# Test endpoint (как в тестах)
# ---------------------------
@router.post("/test", response_model=StatusResponse, summary="test user")
async def test(
    current_user: User = Depends(get_current_user),
):
    return StatusResponse(message="Logged out successfully")
