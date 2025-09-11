# app/db/engine.py
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@asynccontextmanager
async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

async def init_models() -> None:
    """
    Prefer Alembic for schema, but for dev you can create tables with:
    await init_models()
    """
    from app.db import models  # ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
