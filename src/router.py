from fastapi import APIRouter

routers = APIRouter(prefix="/v1")

from routers.auth_router import router as auth_router
from routers.ai_router import router as ai_router


routers.include_router(auth_router)
routers.include_router(ai_router)