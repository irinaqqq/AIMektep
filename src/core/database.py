import uuid

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.dependencies import get_config
from core.logger import logger

# --- Инициализация ---
config = get_config()

# --- Конфигурация URL ---
DATABASE_URL = config.DATABASE_URL
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment.")

ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("asyncpg", "psycopg2")

# --- Параметры подключения ---
COMMON_CONNECT_ARGS = {
    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
}

DATABASE_KWARGS = dict(echo=False, pool_size=20, max_overflow=30, pool_timeout=60)

# --- Создание движков ---
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args=COMMON_CONNECT_ARGS,
    **DATABASE_KWARGS
)

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    **DATABASE_KWARGS
)

# --- Сессии ---
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# --- Декларативная база ---
Base = declarative_base()

# --- Инициализация базы ---
async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.debug("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

# --- Асинхронная сессия ---
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            try:
                await session.rollback()
            except Exception as rollback_exc:
                logger.warning(f"Error during DB rollback: {rollback_exc}")
            raise
        finally:
            logger.debug("Async DB session closed.")

# --- Синхронная сессия (например, для Celery) ---
def get_db_sync():
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        try:
            session.rollback()
        except Exception as rollback_exc:
            logger.warning(f"Error during DB rollback: {rollback_exc}")
        raise
    finally:
        session.close()
        logger.debug("Sync DB session closed.")