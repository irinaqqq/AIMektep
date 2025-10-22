import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Импортируем сам роутер и зависимые callables, которые он использует
from src.routers.auth_router import router as auth_router
from core.database import get_db
from modules.auth.dependencies import get_auth_service, get_bearer_token, get_current_user

# ----------------------------
# Фейки / заглушки зависимостей
# ----------------------------

class FakeAuthService:
    async def register_user(self, data, db):
        # Имитируем успешную регистрацию
        return "access", "refresh"

    async def authenticate_user(self, username, password, db):
        # Имитируем успешный логин
        return "access", "refresh"

    async def refresh_access_token(self, refresh_token: str, db):
        # Имитация выдачи нового access токена по refresh
        return "new_access"

    async def logout_user(self, refresh_token: str):
        # Имитация успешного логаута
        return True


async def fake_db():
    # Минимальная заглушка для get_db (генератор как у Depends(get_db))
    class _Dummy:
        pass
    yield _Dummy()


async def fake_bearer_token():
    # Заглушка вытаскивания токена из Authorization
    return "fake_refresh"


async def fake_current_user():
    # Заглушка текущего пользователя
    class _User:
        id = 1
        username = "testuser"
        email = "test@example.com"
    return _User()


# ----------------------------
# Фикстура приложения
# ----------------------------

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)

    # Подменяем реальные зависимости на фейки
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    app.dependency_overrides[get_bearer_token] = fake_bearer_token
    app.dependency_overrides[get_current_user] = fake_current_user
    return app


# ----------------------------
# ТЕСТЫ
# ----------------------------

@pytest.mark.asyncio
async def test_login_returns_tokens(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post("/auth/login", data={"username": "user", "password": "pass"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("access_token") == "access"
    assert body.get("refresh_token") == "refresh"


@pytest.mark.asyncio
async def test_refresh_returns_access_token(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post("/auth/refresh")
    assert resp.status_code == 200
    body = resp.json()
    # роут (обычно) возвращает {"access_token": "..."} — проверяем наш фейк
    assert body.get("access_token") == "new_access"


@pytest.mark.asyncio
async def test_logout_returns_status(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post("/auth/logout")
    assert resp.status_code == 200
    body = resp.json()
    # в твоём роуте из примера сообщение именно такое
    assert body.get("message") == "Logged out successfully"


@pytest.mark.asyncio
async def test_test_endpoint_requires_user(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post("/auth/test")
    assert resp.status_code == 200
    body = resp.json()
    # судя по твоему роуту /auth/test возвращает то же сообщение
    assert body.get("message") == "Logged out successfully"
