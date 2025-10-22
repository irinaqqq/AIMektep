import pytest
from fastapi import FastAPI
from httpx import AsyncClient

# Import the router and dependency callables used in the router
from src.routers.auth_router import router as auth_router 
from core.database import get_db
from modules.auth.dependencies import get_auth_service, get_bearer_token, get_current_user

class FakeAuthService:
    async def register_user(self, data, db):
        return "access", "refresh"

    async def authenticate_user(self, username, password, db):
        return "access", "refresh"

    async def refresh_token(self, refresh_token, db):
        return "new_access"

    async def logout_user(self, refresh_token):
        return None

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(auth_router)

    fake_service = FakeAuthService()

    # override get_db to yield None (no real DB)
    async def get_db_override():
        yield None

    # override other dependencies to use fakes
    app.dependency_overrides[get_db] = get_db_override
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_bearer_token] = lambda: "fake_refresh_token"

    async def get_current_user_override():
        return {"id": 1, "username": "testuser"}

    app.dependency_overrides[get_current_user] = get_current_user_override

    return app

@pytest.mark.asyncio
async def test_login_returns_tokens(app):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # login endpoint expects form data (SimpleLoginForm.as_form)
        response = await ac.post("/auth/login", data={"username": "user", "password": "pass"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("access_token") == "access"
    assert body.get("refresh_token") == "refresh"

@pytest.mark.asyncio
async def test_refresh_returns_access_token(app):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/auth/token/refresh")
    assert response.status_code == 200
    body = response.json()
    assert body.get("access_token") == "new_access"

@pytest.mark.asyncio
async def test_logout_returns_status(app):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/auth/logout")
    assert response.status_code == 200
    assert response.json().get("message") == "Logged out successfully"

@pytest.mark.asyncio
async def test_test_endpoint_requires_user(app):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/auth/test")
    assert response.status_code == 200
    assert response.json().get("message") == "Logged out successfully"