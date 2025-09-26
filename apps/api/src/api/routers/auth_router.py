from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas import SignupRequest, LoginRequest, RefreshRequest, AuthResponse
from api.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from api.db.base import get_session
from api.repositories.users_repo import get_user_by_email, create_user
from jose import jwt, JWTError
from api.settings import settings

router = APIRouter()

@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_session)):
    if await get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user(db, body.email, hash_password(body.password))
    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Wrong token type")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload["sub"]
    new_access = create_access_token(user_id)
    # you can also rotate refresh tokens if you want
    return AuthResponse(
        access_token=new_access,
        refresh_token=body.refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/logout", status_code=204)
async def logout():
    return None