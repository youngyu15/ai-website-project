from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_current_user
from app.schemas import UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def me(user = Depends(get_current_user)):
    return UserOut.model_validate(user, from_attributes=True)
