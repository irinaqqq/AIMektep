from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from router import routers
from core.dependencies import get_config
from core.database import engine, init_db
from core.logger import logger, setup_logging

setup_logging()

config = get_config() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    logger.debug(f"Debug mode: {config.DEBUG}")

    await init_db()

    try:
        yield
    finally:    
        await engine.dispose()


app = FastAPI(debug=get_config().DEBUG, lifespan=lifespan)

app.include_router(routers)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
