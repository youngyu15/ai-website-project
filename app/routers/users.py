# app/routers/users.py
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from app.schemas import UserBase
from app.deps import get_current_user, User as DepUser

router = APIRouter()

@router.get("/me", response_model=UserBase)
def me(current: DepUser = Depends(get_current_user)):
    return UserBase(id=current.id, email=current.email, created_at=timezone.utc)
