from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import models

async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    res = await db.execute(select(models.User).where(models.User.email == email))
    return res.scalar_one_or_none()

async def create_user(db: AsyncSession, email: str, password_hash: str) -> models.User:
    user = models.User(email=email, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user