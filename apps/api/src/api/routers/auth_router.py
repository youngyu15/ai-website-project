from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas import SignupRequest, LoginRequest, RefreshRequest, AuthResponse
from api.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from api.db.base import get_session
from api.repositories.users_repo import get_user_by_email, create_user
from jose import jwt, JWTError
from api.settings import settings
import secrets

router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_refresh"
CSRF_HEADER_NAME = "x-csrf-token"

def _set_refresh_cookie(response: Response, refresh_token: str, *, secure: bool = True):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,              # True in prod; for local HTTP you can set False
        samesite="lax",           # good for same-domain apps
        path="/v1/auth",          # limit scope
        max_age=30*24*3600,       # e.g., 30 days
    )

def _rotate_csrf_cookie(response: Response, *, secure: bool = True) -> str:
    csrf = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf,
        httponly=False,           # JS must read this and echo in header
        secure=True,
        samesite="lax",
        path="/v1/auth",
        max_age=30*24*3600,
    )
    return csrf

def _validate_csrf(request: Request, x_csrf_token: str | None):
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_cookie or not x_csrf_token or csrf_cookie != x_csrf_token:
        raise HTTPException(status_code=403, detail="CSRF check failed")

@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_session)):
    if await get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user(db, body.email, hash_password(body.password))
    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token="",
    )

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session), response: Response = None):
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token=create_access_token(user.id)
    refresh_token=create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    _rotate_csrf_cookie(response)

    return AuthResponse(
        access_token=access_token,
        refresh_token="",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: Request, response: Response, x_csrf_token: str | None = Header(None, convert_underscores=False)):

    _validate_csrf(request, x_csrf_token)
    token = request.cookies.get("refresh_token")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Wrong token type")
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_refresh = create_refresh_token(user_id)
    new_access = create_access_token(user_id)

    _set_refresh_cookie(response, new_refresh)
    _rotate_csrf_cookie(response)

    return AuthResponse(
        access_token=new_access,
        refresh_token="",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/v1/auth")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/v1/auth")
    return None