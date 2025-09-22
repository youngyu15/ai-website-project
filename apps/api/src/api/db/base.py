# app/db/engine.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from api.settings import settings

engine = create_async_engine(
    settings.database_url, echo=False, pool_pre_ping=True, future=True
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# FastAPI dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def init_models() -> None:
    # Only for local dev; prefer Alembic in real use
    from api.db import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
